"""Tests MVP CIVIC-MVP-001 — moteur déterministe + API, sans appel réseau."""

from fastapi.testclient import TestClient

from app.core.intents import detect_intent
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_procedures():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    slugs = {p["slug"] for p in res.json()}
    assert slugs == {
        "cni",
        "passeport",
        "extrait-naissance",
        "certificat-nationalite",
        "casier-judiciaire",
    }


def test_get_procedure_connue():
    res = client.get("/api/procedures/cni")
    assert res.status_code == 200
    assert res.json()["slug"] == "cni"


def test_procedure_inexistante():
    res = client.get("/api/procedures/inexistante")
    assert res.status_code == 404


def test_search_cni():
    res = client.post("/api/search", json={"query": "J'ai perdu ma CNI"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "cni"
    assert body["match_status"] == "MATCHED"
    assert body["procedure"]["slug"] == "cni"


def test_search_passeport():
    res = client.post("/api/search", json={"query": "Je veux obtenir un passeport"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "passeport"
    assert body["match_status"] == "MATCHED"


def test_search_extrait_naissance():
    res = client.post("/api/search", json={"query": "J'ai besoin de mon extrait de naissance"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "extrait-naissance"
    assert body["match_status"] == "MATCHED"


def test_search_certificat_nationalite():
    res = client.post(
        "/api/search", json={"query": "Comment obtenir un certificat de nationalité ?"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "certificat-nationalite"
    assert body["match_status"] == "MATCHED"


def test_search_casier_judiciaire():
    res = client.post("/api/search", json={"query": "On me demande un casier judiciaire"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "casier-judiciaire"
    assert body["match_status"] == "MATCHED"


def test_search_casse_differente():
    res = client.post("/api/search", json={"query": "J'AI PERDU MA cni"})
    assert res.status_code == 200
    assert res.json()["intent"] == "cni"


def test_accents_normalisation():
    intent, normalized = detect_intent("Carte d'identité")
    assert intent == "cni"
    assert normalized == "carte d identite"
    res = client.post("/api/search", json={"query": "Carte d'identité"})
    assert res.status_code == 200
    assert res.json()["intent"] == "cni"
    # bulletin n°3 avec symbole degré
    res2 = client.post("/api/search", json={"query": "bulletin n°3"})
    assert res2.status_code == 200
    assert res2.json()["intent"] == "casier-judiciaire"


def test_requete_inconnue():
    res = client.post("/api/search", json={"query": "Quel temps fait-il demain ?"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "UNKNOWN"
    assert body["match_status"] == "UNKNOWN"
    assert body["procedure"] is None


def test_requete_vide_invalide():
    res = client.post("/api/search", json={"query": ""})
    assert res.status_code == 422
    res2 = client.post("/api/search", json={"query": "   "})
    assert res2.status_code == 422
    res3 = client.post("/api/search", json={})
    assert res3.status_code == 422


def test_donnees_non_verifiees_ne_deviennent_pas_verified():
    """Garantie UNKNOWN > FAUX : aucune fiche locale ne doit être VERIFIED
    par défaut et /api/search ne doit jamais promouvoir artificiellement."""
    res = client.get("/api/procedures")
    assert res.status_code == 200
    for proc in res.json():
        assert proc["verification_status"] == "UNVERIFIED"
        assert proc["cost"] is None
        assert proc["delay"] is None
        assert proc["competent_authority"] is None
        assert proc["requirements"] == []
        assert proc["sources"] == []
    search = client.post("/api/search", json={"query": "J'ai perdu ma CNI"})
    assert search.json()["verification_status"] == "UNVERIFIED"
    assert search.json()["procedure"]["verification_status"] == "UNVERIFIED"
