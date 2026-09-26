"""Tests CIVIC-VISION-001 — infos pratiques ONECI + suivi externe, sans appel réseau.

Principe UNKNOWN > FAUX : aucun champ inconnu n'est inventé, aucun faux
statut administratif. L'URL de suivi https://statut.oneci.ci/ a été fournie
et vérifiée par l'humain (finalisation validée) : elle est donc attendue
comme URL officielle configurée.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.models import PracticalInfo, Procedure, TrackingInfo

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent.parent

HOURS = "08h00–12h00 / 13h00–17h00"
TRACKING_URL = "https://statut.oneci.ci/"


def _cni() -> dict:
    res = client.get("/api/procedures/cni")
    assert res.status_code == 200
    return res.json()


def test_infos_pratiques_oneci_retournees_pour_cni():
    proc = _cni()
    info = proc.get("practical_info")
    assert info is not None
    assert info["organization"] == "Office National de l'État Civil et de l'Identification (ONECI)"


def test_centre_appel_1340_present():
    proc = _cni()
    phones = proc["practical_info"]["phones"] or []
    assert "1340" in phones


def test_horaires_fournis_presents():
    proc = _cni()
    assert proc["practical_info"]["hours"] == HOURS


def test_jours_ouverture_accessibilite_non_inventes():
    proc = _cni()
    info = proc["practical_info"]
    assert info.get("opening_days") in (None, [])
    assert info.get("accessibility") in (None, "")
    assert info.get("address") in (None, "")
    # Le modèle accepte l'absence de ces champs (compatibilité).
    parsed = PracticalInfo(**info)
    assert parsed.opening_days is None
    assert parsed.accessibility is None


def test_modele_suivi_accepte_external_official():
    proc = _cni()
    tracking = proc.get("tracking")
    assert tracking is not None
    assert tracking["mode"] == "external_official"
    assert tracking["label"] == "Suivre ma demande"
    assert tracking["organization"] == "ONECI"
    assert tracking["available"] is True
    parsed = TrackingInfo(**tracking)
    assert parsed.mode == "external_official"
    # Le futur mode api_integrated est accepté architecturalement.
    future = TrackingInfo(available=False, mode="api_integrated")
    assert future.mode == "api_integrated"


def test_suivi_url_officielle_configuree():
    """Finalisation humaine validée : l'URL officielle est configurée, pas devinée."""
    proc = _cni()
    assert proc["tracking"].get("url") == TRACKING_URL
    body = client.post("/api/search", json={"query": "J'ai perdu ma CNI"}).json()
    assert body["procedure"]["tracking"]["url"] == TRACKING_URL


def test_suivi_source_officielle():
    proc = _cni()
    source = proc["tracking"]["source"]
    assert source["title"] == "Consultation de l'état d'une demande de titre d'identité"
    assert source["organization"] == "ONECI"
    assert source["url"] == TRACKING_URL
    assert source["verified_at"] == "2026-09-26"
    assert proc["tracking"]["verified_at"] == "2026-09-26"


def test_suivi_mode_reste_external_official():
    proc = _cni()
    assert proc["tracking"]["mode"] == "external_official"
    assert proc["tracking"]["available"] is True


def test_suivi_lien_externe_officiel_securise():
    proc = _cni()
    tracking = proc["tracking"]
    # URL http(s) valide selon le validateur du modèle (pas de faux lien).
    parsed = TrackingInfo(**tracking)
    assert parsed.url == TRACKING_URL
    assert parsed.url.startswith("https://")
    # L'interface rend le bouton actif comme lien externe sécurisé.
    js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "track-link" in js
    assert 'target="_blank"' in js
    assert "noopener noreferrer" in js
    # Le rendu du suivi utilise l'URL fournie par l'API (href échappée),
    # sans URL en dur inventée côté interface.
    assert "tracking.url" in js
    assert "statut.oneci.ci" not in js


def test_anciennes_procedures_restent_compatibles():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    by_slug = {p["slug"]: p for p in res.json()}
    for slug in ("passeport", "extrait-naissance", "certificat-nationalite", "casier-judiciaire"):
        proc = by_slug[slug]
        # Champs optionnels absents des anciens JSON -> None, validation OK.
        assert proc.get("practical_info") is None
        assert proc.get("tracking") is None
        Procedure(**proc)


def test_search_cni_expose_infos_et_suivi():
    body = client.post("/api/search", json={"query": "J'ai perdu ma CNI"}).json()
    assert body["match_status"] == "MATCHED"
    info = body["procedure"]["practical_info"]
    assert "1340" in (info["phones"] or [])
    assert info["hours"] == HOURS
    assert body["procedure"]["tracking"]["label"] == "Suivre ma demande"


def test_interface_bloc_suivi_sans_faux_statut():
    js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "Informations pratiques" in js
    assert "Et apr" in js
    assert "Suivre ma demande" in js
    assert ("lien à configurer" in js or "lien \\u00e0 configurer" in js
            or "lien \u00e0 configurer" in js)
    assert "peut vous orienter vers le service officiel de suivi" in js
    assert 'target="_blank"' in js
    assert "noopener noreferrer" in js
    # Aucun faux statut administratif généré côté interface.
    for fake in ("En traitement", "Disponible", "En cours de traitement", "Votre demande est"):
        assert fake not in js
    # Aucun faux statut non plus dans les payloads API (fiche + recherche).
    import json as _json

    payloads = [
        _json.dumps(_cni(), ensure_ascii=False),
        _json.dumps(
            client.post("/api/search", json={"query": "J'ai perdu ma CNI"}).json(),
            ensure_ascii=False,
        ),
    ]
    for payload in payloads:
        for fake in ("En traitement", "En cours de traitement", "Votre demande est"):
            assert fake not in payload
    css = (BASE_DIR / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert "track-link" in css
    assert "track-pending" in css
