"""Chargement de la base de connaissances locale (fichiers JSON versionnés)."""

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.models import Procedure

PROCEDURES_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "procedures"


def _load_all() -> dict[str, Procedure]:
    procedures: dict[str, Procedure] = {}
    if not PROCEDURES_DIR.exists():
        return procedures
    for path in sorted(PROCEDURES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        try:
            procedure = Procedure(**data)
        except Exception:
            continue
        procedures[procedure.slug] = procedure
    return procedures


@lru_cache(maxsize=1)
def get_procedures() -> dict[str, Procedure]:
    """Retourne les procédures indexées par slug (mise en cache)."""
    return _load_all()


def get_procedure(slug: str) -> Procedure | None:
    """Retourne une procédure par slug, ou None si inconnue."""
    return get_procedures().get(slug)


def list_procedures() -> list[Procedure]:
    """Retourne toutes les procédures triées par slug."""
    return [get_procedures()[slug] for slug in sorted(get_procedures())]
