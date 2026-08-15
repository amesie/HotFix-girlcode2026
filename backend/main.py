"""FastAPI app entrypoint for Verifi.

Thin by design: wiring only (CORS, router mount, exception handlers,
startup seeding). All business logic lives in backend/api/routes.py.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Configured before importing routes, so that module's import-time log
# lines (USING REAL/MOCK DETECTION SERVICE) actually get emitted.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import routes
from backend.database import database as db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build and seed the SQLite DB on startup. Idempotent, so this is
    safe to run every time the process starts, including in tests."""
    db.init_db()
    db.seed()
    health = db.health()
    logger.info(
        "Startup complete: datasource=%s seededFrom=%s recordCount=%d detection=%s",
        health["datasource"],
        health["seededFrom"],
        health["recordCount"],
        routes.detection_mode(),
    )
    yield


app = FastAPI(title="Verifi API", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# CORS — the frontend runs on a different port, so getting this wrong is a
# guaranteed 2am debugging session. Defaults cover both CRA and Vite dev
# servers; ALLOWED_ORIGINS lets ops/deploy add more without a code change.
# ---------------------------------------------------------------------------

_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
_allowed_origins = _DEFAULT_ORIGINS + [o for o in _extra_origins if o not in _DEFAULT_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)


# ---------------------------------------------------------------------------
# Global exception handlers — every endpoint, every failure path, returns
# {"error": true, "message": str}. The default FastAPI {"detail": ...}
# body would break the frontend's error handling.
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error on %s", request.url.path)
    return JSONResponse(status_code=400, content={"error": True, "message": "Invalid request data"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": True, "message": str(exc.detail)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak a stack trace or raw exception text to the caller —
    # log it server-side, return a generic message.
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(status_code=500, content={"error": True, "message": "Internal server error"})


@app.get("/health")
def health() -> dict:
    """Integration smoke test: confirms the DB seeded and which
    detection mode (real vs mock) the API is currently running in."""
    db_health = db.health()
    return {
        "status": "ok",
        "datasource": db_health["datasource"],
        "seededFrom": db_health["seededFrom"],
        "recordCount": db_health["recordCount"],
        "detection": routes.detection_mode(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
