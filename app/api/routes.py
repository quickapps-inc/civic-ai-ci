"""Routes API du MVP."""

from fastapi import APIRouter, HTTPException

from app.core.intents import UNKNOWN, detect_intent
from app.schemas.models import Procedure, SearchRequest, SearchResponse
from app.services.procedures import get_procedure, list_procedures

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "civic-ai-ci"}


@router.get("/api/procedures", response_model=list[Procedure])
def api_list_procedures() -> list[Procedure]:
    return list_procedures()


@router.get("/api/procedures/{slug}", response_model=Procedure)
def api_get_procedure(slug: str) -> Procedure:
    procedure = get_procedure(slug)
    if procedure is None:
        raise HTTPException(status_code=404, detail="Procédure introuvable")
    return procedure


@router.post("/api/search", response_model=SearchResponse)
def api_search(payload: SearchRequest) -> SearchResponse:
    intent, normalized = detect_intent(payload.query)
    if intent == UNKNOWN:
        return SearchResponse(
            query=payload.query,
            normalized_query=normalized,
            intent=UNKNOWN,
            match_status="UNKNOWN",
            procedure=None,
            verification_status=None,
            message=(
                "Aucune démarche reconnue pour cette demande. "
                "Aucune information administrative n'est inventée : "
                "reformulez avec, par exemple, « CNI », « passeport », "
                "« extrait de naissance », « certificat de nationalité » "
                "ou « casier judiciaire »."
            ),
        )
    procedure = get_procedure(intent)
    if procedure is None:  # Garde-fou : intention sans fiche locale
        return SearchResponse(
            query=payload.query,
            normalized_query=normalized,
            intent=intent,
            match_status="UNKNOWN",
            procedure=None,
            verification_status=None,
            message=(
                "Démarche détectée mais fiche non disponible localement. "
                "Aucune information n'est inventée."
            ),
        )
    if procedure.verification_status.value == "UNVERIFIED":
        message = (
            f"Démarche identifiée : {procedure.name}. "
            "Les informations détaillées (documents, coût, délai, autorité) "
            "ne sont pas encore vérifiées et restent donc non renseignées "
            "(principe UNKNOWN > FAUX)."
        )
    else:
        message = f"Démarche identifiée : {procedure.name}."
    return SearchResponse(
        query=payload.query,
        normalized_query=normalized,
        intent=intent,
        match_status="MATCHED",
        procedure=procedure,
        verification_status=procedure.verification_status,
        message=message,
    )
