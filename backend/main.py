"""FastAPI app entrypoint for Verifi.

Thin by design: wiring only (CORS, router mount, exception handlers,
startup seeding). All business logic lives in backend/api/routes.py.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Configure logging before importing routes so their startup logs appear.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Load .env from the project root explicitly.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

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
    """Build and seed the SQLite DB on startup."""
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


app = FastAPI(
    title="Verifi API",
    version="0.1.0",
    lifespan=lifespan,
)


_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

_extra_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

_allowed_origins = _DEFAULT_ORIGINS + [
    origin for origin in _extra_origins
    if origin not in _DEFAULT_ORIGINS
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning("Validation error on %s", request.url.path)

    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "message": "Invalid request data",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": str(exc.detail),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception on %s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
        },
    )


@app.get("/health")
def health() -> dict:
    """Integration smoke test for the API and database."""
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

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
