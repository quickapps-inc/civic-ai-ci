"""Routes API — CIVIC-AI CI (CIVIC-DATA-001 : procédures + variantes)."""

from fastapi import APIRouter, HTTPException

from app.core.intents import UNKNOWN, detect_intent_with_variant
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
    intent, variant_id, normalized, needs_clarification = detect_intent_with_variant(
        payload.query
    )
    if intent == UNKNOWN:
        return SearchResponse(
            query=payload.query,
            normalized_query=normalized,
            intent=UNKNOWN,
            match_status="UNKNOWN",
            procedure=None,
            variant=None,
            needs_clarification=False,
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
            variant=None,
            needs_clarification=False,
            verification_status=None,
            message=(
                "Démarche détectée mais fiche non disponible localement. "
                "Aucune information n'est inventée."
            ),
        )
    variant = None
    if variant_id:
        for candidate in procedure.variants:
            if candidate.id == variant_id:
                variant = candidate
                break
    if needs_clarification:
        variant_names = ", ".join(v.name for v in procedure.variants) or "aucune variante"
        return SearchResponse(
            query=payload.query,
            normalized_query=normalized,
            intent=intent,
            match_status="NEEDS_CLARIFICATION",
            procedure=procedure,
            variant=None,
            needs_clarification=True,
            verification_status=procedure.verification_status,
            message=(
                f"Démarche identifiée : {procedure.name}, mais votre situation "
                f"ne permet pas de déterminer la variante ({variant_names}). "
                "Précisez par exemple : « première demande », « renouvellement » "
                "ou « perte / duplicata ». Aucune variante n'est choisie "
                "arbitrairement (principe UNKNOWN > FAUX)."
            ),
        )
    effective_status = variant.verification_status if variant else procedure.verification_status
    if variant:
        message = f"Démarche identifiée : {procedure.name} — variante : {variant.name}."
    elif procedure.verification_status.value == "UNVERIFIED":
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
        variant=variant,
        needs_clarification=False,
        verification_status=effective_status,
        message=message,
    )
