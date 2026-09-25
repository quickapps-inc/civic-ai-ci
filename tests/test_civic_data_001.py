"""Tests CIVIC-DATA-001 — variantes + seed vérifié, sans appel réseau.

Couvre les intentions à variantes, les données officielles intégrées,
la provenance (URLs + verified_at 2026-09-25) et la compatibilité des
endpoints existants. Principe UNKNOWN > FAUX : aucune donnée devinée.
"""

from fastapi.testclient import TestClient

from app.core.intents import detect_intent_with_variant
from app.main import app

client = TestClient(app)

VERIFIED_AT = "2026-09-25"


def _search(query: str) -> dict:
    res = client.post("/api/search", json={"query": query})
    assert res.status_code == 200
    return res.json()


def test_cni_premiere_demande():
    body = _search("je veux ma première CNI")
    assert body["intent"] == "cni"
    assert body["match_status"] == "MATCHED"
    assert body["variant"] is not None
    assert body["variant"]["id"] == "premiere-demande"
    assert body["needs_clarification"] is False


def test_cni_renouvellement():
    body = _search("je veux renouveler ma CNI")
    assert body["intent"] == "cni"
    assert body["match_status"] == "MATCHED"
    assert body["variant"] is not None
    assert body["variant"]["id"] == "renouvellement"


def test_cni_perte_duplicata():
    body = _search("j'ai perdu ma CNI")
    assert body["intent"] == "cni"
    assert body["match_status"] == "MATCHED"
    assert body["variant"] is not None
    assert body["variant"]["id"] == "duplicata-perte"


def test_cni_generique_sans_variante_arbitraire():
    body = _search("je veux une CNI")
    assert body["intent"] == "cni"
    assert body["variant"] is None
    assert body["needs_clarification"] is True
    assert body["match_status"] == "NEEDS_CLARIFICATION"
    assert body["procedure"]["slug"] == "cni"


def test_cni_premiere_demande_cout_et_pieces():
    body = _search("je veux ma première CNI")
    variant = body["variant"]
    assert variant["cost"] == "5 000 FCFA"
    assert variant["delay"] is None  # aucun délai fixe encodé
    assert any("nationalit" in r for r in variant["requirements"])
    assert any("enr" in r.lower() for r in variant["requirements"])


def test_cni_duplicata_distinct_de_premiere_demande():
    perte = _search("j'ai perdu ma CNI")["variant"]
    premiere = _search("je veux ma première CNI")["variant"]
    assert perte["id"] == "duplicata-perte"
    assert premiere["id"] == "premiere-demande"
    assert perte["id"] != premiere["id"]
    assert any("perte" in r.lower() for r in perte["requirements"])


def test_passeport_cout():
    body = _search("je veux un passeport")
    assert body["intent"] == "passeport"
    assert body["procedure"]["cost"] == "40 000 FCFA"


def test_passeport_delai_conditionnel_paf():
    body = _search("je veux un passeport")
    delay = body["procedure"]["delay"]
    assert "72 heures" in delay
    assert "Police de l'Air et des Frontières" in delay
    assert delay != "72 heures"  # jamais la version courte non conditionnelle


def test_extrait_egare_variante_et_cout_neant():
    body = _search("j'ai perdu mon extrait de naissance")
    assert body["intent"] == "extrait-naissance"
    assert body["variant"] is not None
    assert body["variant"]["id"] == "copie-extrait-egare"
    assert body["variant"]["cost"] == "Néant"
    assert body["variant"]["delay"] is None  # délai non déterminé
    assert "Mairie" in (body["variant"]["competent_authority"] or "")


def test_certificat_nationalite_cout_detaille():
    body = _search("je veux un certificat de nationalité")
    assert body["intent"] == "certificat-nationalite"
    cost = body["procedure"]["cost"]
    assert "2 500 FCFA" in cost
    assert "500 FCFA" in cost
    assert "timbre" in cost.lower()


def test_certificat_nationalite_delai():
    body = _search("je veux un certificat de nationalité")
    assert body["procedure"]["delay"] == "24 heures après dépôt des dossiers"


def test_casier_bulletin3_cout():
    body = _search("je veux un casier judiciaire")
    assert body["intent"] == "casier-judiciaire"
    assert body["procedure"]["cost"] == "2 500 FCFA"


def test_casier_delai():
    body = _search("je veux un casier judiciaire")
    assert body["procedure"]["delay"] == "24 heures"


def test_sources_urls_presentes():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    by_slug = {p["slug"]: p for p in res.json()}
    expected_fragments = {
        "cni": ["oneci.ci/nos-produits/carte-identite/documents-a-fournir", "timbre.oneci.ci"],
        "passeport": ["snedai.com/passeport-en-cote-divoire", "monpasseport.ci/faq"],
        "extrait-naissance": ["servicepublic.gouv.ci/accueil/detaildemarcheparticulier/gupc/480"],
        "certificat-nationalite": ["servicepublic.gouv.ci/accueil/detaildemarcheparticulier/1/573"],
        "casier-judiciaire": ["servicepublic.gouv.ci/accueil/detaildemarcheparticulier/1/81/61"],
    }
    for slug, fragments in expected_fragments.items():
        proc = by_slug[slug]
        urls = [s["url"] for s in proc["sources"]]
        for variant in proc.get("variants", []):
            urls += [s["url"] for s in variant["sources"]]
        for fragment in fragments:
            assert any(fragment in u for u in urls), f"{slug} : {fragment} manquant"


def test_verified_at_2026_09_25():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    for proc in res.json():
        if proc["verification_status"] in ("VERIFIED", "PARTIALLY_VERIFIED"):
            assert proc["verified_at"] == VERIFIED_AT
            for source in proc["sources"]:
                assert source["verified_at"] == VERIFIED_AT
                assert source["title"]
                assert source["organization"]
                assert source["url"]
        for variant in proc.get("variants", []):
            if variant["verification_status"] in ("VERIFIED", "PARTIALLY_VERIFIED"):
                assert variant["verified_at"] == VERIFIED_AT
                for source in variant["sources"]:
                    assert source["verified_at"] == VERIFIED_AT


def test_aucune_non_sourcee_promue_verified():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    for proc in res.json():
        if proc["verification_status"] in ("VERIFIED", "PARTIALLY_VERIFIED"):
            assert len(proc["sources"]) > 0
        for variant in proc.get("variants", []):
            if variant["verification_status"] in ("VERIFIED", "PARTIALLY_VERIFIED"):
                assert len(variant["sources"]) > 0


def test_pas_de_score_numerique():
    res = client.get("/api/procedures")
    for proc in res.json():
        assert "score" not in proc
        assert "confiance" not in proc
        for variant in proc.get("variants", []):
            assert "score" not in variant


def test_compatibilite_endpoints_existants():
    res = client.get("/api/procedures")
    assert res.status_code == 200
    assert {p["slug"] for p in res.json()} == {
        "cni",
        "passeport",
        "extrait-naissance",
        "certificat-nationalite",
        "casier-judiciaire",
    }
    one = client.get("/api/procedures/cni")
    assert one.status_code == 200
    assert one.json()["slug"] == "cni"
    assert client.get("/api/procedures/inexistante").status_code == 404
    unknown = _search("Quel temps fait-il demain ?")
    assert unknown["intent"] == "UNKNOWN"
    assert unknown["procedure"] is None


def test_moteur_intentions_mission():
    cases = [
        ("j'ai perdu ma CNI", "cni", "duplicata-perte"),
        ("je veux renouveler ma CNI", "cni", "renouvellement"),
        ("je veux ma première CNI", "cni", "premiere-demande"),
        ("j'ai perdu mon extrait de naissance", "extrait-naissance", "copie-extrait-egare"),
        ("je veux un passeport", "passeport", None),
        ("je veux un certificat de nationalité", "certificat-nationalite", None),
        ("je veux un casier judiciaire", "casier-judiciaire", None),
    ]
    for query, intent, variant_id in cases:
        got_intent, got_variant, _, _ = detect_intent_with_variant(query)
        assert got_intent == intent, query
        assert got_variant == variant_id, query
    # Générique CNI : pas de variante arbitraire.
    intent, variant_id, _, needs = detect_intent_with_variant("je veux une CNI")
    assert intent == "cni"
    assert variant_id is None
    assert needs is True
