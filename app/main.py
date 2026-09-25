"""Point d'entrée FastAPI — CIVIC-AI CI (MVP CIVIC-MVP-001)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="CIVIC-AI CI", version="0.1.0-mvp")
app.include_router(router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))
