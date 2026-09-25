"""Schémas Pydantic — CIVIC-AI CI (CIVIC-DATA-001 : procédures + variantes)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class Source(BaseModel):
    """Provenance d'une information administrative vérifiée.

    Champs minimaux exigés par la mission : titre/nom de la source,
    organisme institutionnel, URL, date de vérification (2026-09-25).
    """

    title: str
    organization: str
    url: str
    verified_at: str


class ProcedureVariant(BaseModel):
    """Variante administrative d'une procédure (ex. CNI / renouvellement)."""

    id: str
    name: str
    requirements: list[str] = Field(default_factory=list)
    cost: Optional[str] = None
    delay: Optional[str] = None
    competent_authority: Optional[str] = None
    notes: Optional[str] = None
    sources: list[Source] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_at: Optional[str] = None


class Procedure(BaseModel):
    id: str
    slug: str
    name: str
    summary: str
    # Champs génériques conservés pour rétrocompatibilité des endpoints
    # existants. Ils restent null/vides au niveau procédure lorsque
    # l'information varie selon la variante (principe UNKNOWN > FAUX).
    requirements: list[str] = Field(default_factory=list)
    cost: Optional[str] = None
    delay: Optional[str] = None
    competent_authority: Optional[str] = None
    notes: Optional[str] = None
    variants: list[ProcedureVariant] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_at: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("query ne doit pas être vide")
        if len(value.strip()) > 500:
            raise ValueError("query trop longue (max 500 caractères)")
        return value.strip()


class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    intent: str
    match_status: str  # "MATCHED" | "UNKNOWN" | "NEEDS_CLARIFICATION"
    procedure: Optional[Procedure] = None
    # Variante identifiée (None si générique / à préciser). L'intent reste
    # le slug de la procédure pour compatibilité avec les clients existants.
    variant: Optional[ProcedureVariant] = None
    needs_clarification: bool = False
    verification_status: Optional[VerificationStatus] = None
    message: str
