"""Schémas Pydantic du MVP CIVIC-AI CI."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class Procedure(BaseModel):
    id: str
    slug: str
    name: str
    summary: str
    requirements: list[str] = Field(default_factory=list)
    cost: Optional[str] = None
    delay: Optional[str] = None
    competent_authority: Optional[str] = None
    sources: list[str] = Field(default_factory=list)
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
    match_status: str  # "MATCHED" | "UNKNOWN"
    procedure: Optional[Procedure] = None
    verification_status: Optional[VerificationStatus] = None
    message: str
