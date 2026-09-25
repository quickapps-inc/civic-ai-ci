"""Moteur d'intention déterministe (règles par sous-chaînes, sans LLM)."""

from app.core.normalize import normalize_query

UNKNOWN = "UNKNOWN"

# Motifs déjà normalisés (minuscules, sans accents). Ordre = priorité
# en cas de chevauchement : les formulations les plus spécifiques d'abord
# au sein de chaque intention, et les intentions spécifiques avant les
# génériques lors du balayage.
INTENT_PATTERNS: dict[str, list[str]] = {
    "cni": [
        "carte nationale d identite",
        "carte d identite",
        "renouveler ma carte",
        "perdu ma carte",
        "cni",
    ],
    "passeport": [
        "voyage a l etranger",
        "passeport",
        "voyager",
    ],
    "extrait-naissance": [
        "extrait de naissance",
        "acte de naissance",
        "document de naissance",
    ],
    "certificat-nationalite": [
        "certificat de nationalite",
        "prouver ma nationalite",
    ],
    "casier-judiciaire": [
        "casier judiciaire",
        "bulletin numero 3",
        "bulletin n 3",
    ],
}

# Ordre de balayage global : formulations multi-mots spécifiques d'abord.
SCAN_ORDER: list[str] = [
    "casier-judiciaire",
    "certificat-nationalite",
    "extrait-naissance",
    "cni",
    "passeport",
]


def detect_intent(raw_query: str) -> tuple[str, str]:
    """Détecte l'intention d'une requête brute.

    Retourne (intent_slug_ou_UNKNOWN, normalized_query).
    Règles : normalisation puis recherche de sous-chaîne.
    """
    normalized = normalize_query(raw_query or "")
    if not normalized:
        return UNKNOWN, normalized
    for slug in SCAN_ORDER:
        for pattern in INTENT_PATTERNS[slug]:
            if pattern in normalized:
                return slug, normalized
    return UNKNOWN, normalized
