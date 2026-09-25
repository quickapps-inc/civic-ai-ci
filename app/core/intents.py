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
    Conservé à l'identique pour compatibilité (l'intent reste le slug
    de la procédure ; la variante est résolue séparément).
    """
    normalized = normalize_query(raw_query or "")
    if not normalized:
        return UNKNOWN, normalized
    for slug in SCAN_ORDER:
        for pattern in INTENT_PATTERNS[slug]:
            if pattern in normalized:
                return slug, normalized
    return UNKNOWN, normalized


# Signaux de variantes (requêtes déjà normalisées). Ordre d'évaluation
# CNI : perte/duplicata > renouvellement > première demande.
CNI_LOSS_SIGNALS = ("duplicata", "perdu", "perte", "egare", "vole")
CNI_RENEW_SIGNALS = ("renouvel", "expir")
CNI_FIRST_SIGNALS = ("premier", "premiere", "1er", "1ere")

EXTRAIT_LOSS_SIGNALS = ("perdu", "perte", "egare", "detruit", "vole")


def resolve_variant(intent: str, normalized: str) -> tuple[str | None, bool]:
    """Résout la variante d'une intention déjà détectée.

    Retourne (variant_id_ou_None, needs_clarification).
    - CNI générique sans signal de variante -> (None, True) : aucun choix
      arbitraire, la route demandera une précision.
    - Extrait générique sans signal de perte -> (None, False) : la fiche
      générique est retournée sans présumer qu'il s'agit d'un extrait égaré.
    - Autres procédures (sans variantes) -> (None, False).
    """
    text = normalized or ""
    if intent == "cni":
        if any(s in text for s in CNI_LOSS_SIGNALS):
            return "duplicata-perte", False
        if any(s in text for s in CNI_RENEW_SIGNALS):
            return "renouvellement", False
        if any(s in text for s in CNI_FIRST_SIGNALS):
            return "premiere-demande", False
        return None, True
    if intent == "extrait-naissance":
        if any(s in text for s in EXTRAIT_LOSS_SIGNALS):
            return "copie-extrait-egare", False
        return None, False
    return None, False


def detect_intent_with_variant(raw_query: str) -> tuple[str, str | None, str, bool]:
    """Détecte (intent, variant_id, normalized, needs_clarification)."""
    intent, normalized = detect_intent(raw_query)
    if intent == UNKNOWN:
        return UNKNOWN, None, normalized, False
    variant_id, needs_clarification = resolve_variant(intent, normalized)
    return intent, variant_id, normalized, needs_clarification
