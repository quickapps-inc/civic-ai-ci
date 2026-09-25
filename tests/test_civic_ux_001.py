"""Tests CIVIC-UX-001 — interface citoyenne, sans appel réseau.

Vérifie que la page publique / présente la nouvelle hiérarchie UX,
ne expose plus la terminologie technique interne, et que le JS
construit des blocs citoyens (sources sécurisées, statuts explicites,
notes de gouvernance filtrées). Les tests métier existants restent
intacts : ce fichier n'affaiblit aucun comportement backend.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent.parent


def _home_html() -> str:
    res = client.get("/")
    assert res.status_code == 200
    return res.text


def _read(rel: str) -> str:
    return (BASE_DIR / rel).read_text(encoding="utf-8")


def test_home_repond_200():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")


def test_proposition_valeur_presente():
    html = _home_html()
    assert "Votre guide intelligent des démarches administratives en Côte d'Ivoire" in html
    assert "Que souhaitez-vous faire ?" in html
    assert "Trouver ma démarche" in html
    assert "Ou décrivez simplement votre situation avec vos propres mots." in html
    assert "Expliquez simplement ce que vous souhaitez faire." in html
    assert "Lorsque nous ne pouvons pas vérifier une information" in html


def test_terminologie_technique_absente_interface_publique():
    html = _home_html()
    assert "UNKNOWN &gt; FAUX" not in html
    assert "UNKNOWN > FAUX" not in html
    assert "(VERIFIED)" not in html
    assert "(PARTIALLY_VERIFIED)" not in html
    assert "(UNVERIFIED)" not in html
    assert "MVP CIVIC-MVP-001" not in html
    assert "moteur déterministe local" not in html


def test_notes_gouvernance_absentes_interface_publique():
    html = _home_html()
    js = _read("static/js/app.js")
    # La note interne de l'exemple mission ne doit pas être affichée en dur.
    assert "ne pas fusionner" not in html.lower()
    # Le JS doit contenir un filtre (pas un affichage brut des notes).
    assert "dans cette mission" in js.lower()  # motif du filtre anti-gouvernance


def test_js_sans_statuts_techniques_bruts():
    js = _read("static/js/app.js")
    # L'ancien affichage brut "Statut (VERIFIED)" est supprimé.
    assert '(" + escapeHtml(effectiveStatus' not in js
    assert "(VERIFIED)" not in js
    assert "(PARTIALLY_VERIFIED)" not in js
    assert "(UNVERIFIED)" not in js
    # Nouveaux libellés citoyens présents.
    assert "Informations de cette démarche vérifiées" in js
    assert "Certaines informations restent à vérifier" in js
    assert "Informations non encore vérifiées" in js
    assert "Démarche identifiée" in js


def test_bloc_sources_officielles():
    html = _home_html()
    js = _read("static/js/app.js")
    assert "Sources officielles" in html or "Sources officielles" in js
    assert "Consulter la source officielle" in js
    assert 'target="_blank"' in js or "target" in js
    assert "noopener noreferrer" in js
    # Date lisible en français.
    assert "Vérifié le" in js
    assert "septembre" in js
    # Aucune URL brute affichée comme texte de lien : le texte est le libellé.
    assert "Consulter la source officielle" in js


def test_messages_api_sans_terminologie_interne():
    for q in ["J'ai perdu ma CNI", "je veux une CNI", "Quel temps fait-il demain ?"]:
        body = client.post("/api/search", json={"query": q}).json()
        assert "UNKNOWN > FAUX" not in body["message"]
        assert "(VERIFIED)" not in body["message"]
        assert "(PARTIALLY_VERIFIED)" not in body["message"]
        assert "(UNVERIFIED)" not in body["message"]
    clarification = client.post("/api/search", json={"query": "je veux une CNI"}).json()
    assert "nous avons besoin de préciser votre situation" in clarification["message"].lower()


def test_footer_citoyen():
    html = _home_html()
    assert "Prototype d'orientation vers les démarches administratives" in html
    assert "Consultez toujours" in html
    assert "sans affiliation officielle" in html.lower() or "Sans affiliation officielle" in html


def test_accessibilite_minimale():
    html = _home_html()
    assert 'for="query"' in html
    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    assert "<label" in html
    assert "skip-link" in html or "Aller à la recherche" in html
