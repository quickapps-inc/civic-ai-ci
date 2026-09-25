"""Normalisation déterministe des requêtes citoyennes (minuscules, sans accents)."""

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def remove_accents(text: str) -> str:
    """Retire les diacritiques (é -> e, è -> e, ° supprimé séparément)."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_query(text: str) -> str:
    """Normalise une requête : minuscules, sans accents, ponctuation aplanie.

    - insensible à la casse
    - insensible aux accents
    - espaces multiples réduits
    - apostrophes/ponctuation courante remplacées par des espaces
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = remove_accents(text)
    # Normaliser les variantes du bulletin n°3 / nº / no
    text = text.replace("°", " ").replace("º", " ").replace("nº", "n ")
    # Remplacer la ponctuation courante par des espaces
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    # Replier les variantes "bulletin n 3" déjà gérées ; garder aussi "n3" -> "n 3"
    text = re.sub(r"\bn\s*3\b", "n 3", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text
