"""HTTP routes for Verifi: identity check + chat placeholder.

This module owns the API contract with the frontend. It validates
input, talks to backend.database for record lookups, and adapts the
teammate's detection-service shape into the frontend-facing shape. It
never runs raw SQL and never leaks stack traces or internal detection
output to the caller.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.database import database as db

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models (local to the API layer — backend/models/schemas.py belongs
# to a teammate and is for detection-domain models, not request bodies).
# ---------------------------------------------------------------------------


class CheckIdentityRequest(BaseModel):
    idNumber: str


class LocationModel(BaseModel):
    lat: float
    lng: float


class ChatRequest(BaseModel):
    message: str
    location: LocationModel | None = None
    conversationId: str | None = None


# ---------------------------------------------------------------------------
# ID number validation
# ---------------------------------------------------------------------------


class InvalidIdNumberError(Exception):
    """Raised for any ID format problem. Deliberately carries no detail —
    callers return a single generic message so we don't hand a fraudster
    a rule-by-rule validator."""


# Demo IDs from the project brief. Real SA ID numbers must pass Luhn, but
# these synthetic ones don't all happen to, so ALLOW_DEMO_IDS whitelists
# exactly this set past the checksum.
_DEMO_IDS = {
    "9001015800083",
    "8505124800086",
    "7712089800081",
    "6003215800084",
    "9506306800082",
}


def _allow_demo_ids() -> bool:
    """Read ALLOW_DEMO_IDS each call (not cached) so tests can toggle it
    via monkeypatching os.environ without reimporting this module."""
    return os.getenv("ALLOW_DEMO_IDS", "true").strip().lower() in {"1", "true", "yes", "on"}


def _is_valid_yymmdd(yy: str, mm: str, dd: str) -> bool:
    """SA IDs don't encode century, so a YYMMDD is valid if it forms a
    real calendar date in either the 1900s or 2000s (handles Feb 29 on
    century-dependent leap years correctly)."""
    for century in (1900, 2000):
        try:
            date(century + int(yy), int(mm), int(dd))
            return True
        except ValueError:
            continue
    return False


def _luhn_is_valid(id13: str) -> bool:
    """Luhn checksum over all 13 digits (digit 13 is the check digit).

    Standard Luhn: walking right to left, the check digit itself (index 0
    from the right) is never doubled; every second digit after it is
    doubled, with doubled values over 9 reduced by subtracting 9 (same as
    summing their two digits). The number is valid iff the total is a
    multiple of 10.
    """
    total = 0
    for i, ch in enumerate(reversed(id13)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def validate_id_number(raw: str) -> str:
    """Clean and validate an SA ID number. Returns the 13-digit string.

    Raises InvalidIdNumberError on any failure: wrong length, bad date,
    or failed Luhn check (unless ALLOW_DEMO_IDS whitelists it).
    """
    cleaned = re.sub(r"[\s\-]", "", raw or "")
    if not re.fullmatch(r"\d{13}", cleaned):
        raise InvalidIdNumberError()

    if not _is_valid_yymmdd(cleaned[0:2], cleaned[2:4], cleaned[4:6]):
        raise InvalidIdNumberError()

    if not _luhn_is_valid(cleaned):
        if _allow_demo_ids() and cleaned in _DEMO_IDS:
            logger.warning("ALLOW_DEMO_IDS bypassed Luhn check for %s", db.mask_id(cleaned))
        else:
            raise InvalidIdNumberError()

    return cleaned


# ---------------------------------------------------------------------------
# Resilient import of the teammate's detection service
# ---------------------------------------------------------------------------

_CANDIDATE_FN_NAMES = ("check_identity", "check", "run_check")


def _bind_detection_function(module: Any | None) -> tuple[Any | None, str, str | None]:
    """Find a usable entry point on the detection module.

    Returns (callable_or_None, mode, bound_name); mode is "real" only if
    a callable was found. Kept separate from the import itself so it's
    unit-testable without faking sys.modules.
    """
    if module is None:
        return None, "mock", None
    for name in _CANDIDATE_FN_NAMES:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn, "real", name
    return None, "mock", None


try:
    from backend.services import identity_checker as _identity_checker_module
except ImportError:
    _identity_checker_module = None

_detection_fn, _DETECTION_MODE, _bound_name = _bind_detection_function(_identity_checker_module)
if _DETECTION_MODE == "real":
    logger.info("USING REAL DETECTION SERVICE (bound to identity_checker.%s)", _bound_name)
else:
    logger.warning("USING MOCK DETECTION DATA (identity_checker unavailable or missing a recognized entry point)")


def detection_mode() -> str:
    """"real" or "mock" — exposed for GET /health."""
    return _DETECTION_MODE


# ---------------------------------------------------------------------------
# Mock detection data — keeps /api/check-identity fully functional even
# with no detection service wired up yet.
# ---------------------------------------------------------------------------

_MOCK_RESULTS: dict[str, dict[str, Any]] = {
    "9001015800083": {"status": "CLEAR", "riskLevel": "LOW", "issues": []},
    "8505124800086": {
        "status": "FLAGGED",
        "riskLevel": "HIGH",
        "issues": [
            {"type": "MULTIPLE_ACTIVE_MARRIAGES", "message": "Multiple active marriages detected."}
        ],
    },
    "7712089800081": {
        "status": "FLAGGED",
        "riskLevel": "MEDIUM",
        "issues": [{"type": "DUPLICATE_ID_NUMBER", "message": "Duplicate ID number detected."}],
    },
    "6003215800084": {
        "status": "FLAGGED",
        "riskLevel": "HIGH",
        "issues": [{"type": "DECEASED_FLAG", "message": "ID number is flagged as deceased."}],
    },
    "9506306800082": {
        "status": "FLAGGED",
        "riskLevel": "HIGH",
        "issues": [{"type": "BLOCKED_ID", "message": "ID number is blocked."}],
    },
}


def _derive_mock_result(record: dict[str, Any]) -> dict[str, Any]:
    """Fallback for any DB record outside the fixed 5-ID mock table.

    Reads straight off the identity_records columns so mock mode stays
    useful once the teammate's marriages.json grows beyond the demo set,
    without needing _MOCK_RESULTS hand-updated for every new row.
    """
    if record.get("is_deceased"):
        return {"status": "FLAGGED", "riskLevel": "HIGH", "issues": [{"type": "DECEASED_FLAG", "message": "Record marked deceased."}]}
    if record.get("is_blocked"):
        return {"status": "FLAGGED", "riskLevel": "HIGH", "issues": [{"type": "BLOCKED_ID", "message": "ID number is blocked."}]}
    if record.get("duplicate_of"):
        return {"status": "FLAGGED", "riskLevel": "MEDIUM", "issues": [{"type": "DUPLICATE_ID_NUMBER", "message": "Duplicate ID number detected."}]}
    return {"status": "CLEAR", "riskLevel": "LOW", "issues": []}


def _mock_detect(id_number: str, record: dict[str, Any]) -> dict[str, Any]:
    return _MOCK_RESULTS.get(id_number) or _derive_mock_result(record)


def _run_detection(id_number: str, record: dict[str, Any]) -> dict[str, Any]:
    """Call the real detection service if bound; fall back to mock data
    for this single request if it raises, so one bad call never 500s
    the endpoint."""
    if _detection_fn is not None:
        try:
            return _detection_fn(id_number)
        except Exception:
            logger.exception("identity_checker raised for %s; using mock data for this request", db.mask_id(id_number))
    return _mock_detect(id_number, record)


# ---------------------------------------------------------------------------
# Adapter: teammate's detection shape -> frontend API contract
# ---------------------------------------------------------------------------

# Explicit mapping from the detection service's issue.type to our flag.type.
# Anything not in this dict is "unknown" and handled defensively below.
_ISSUE_TYPE_MAP = {
    "MULTIPLE_ACTIVE_MARRIAGES": "marital_status_mismatch",
    "DUPLICATE_ID_NUMBER": "duplicate_id",
    "DECEASED_FLAG": "deceased_flag",
    "BLOCKED_ID": "blocked_id",
}

# User-facing copy, keyed by our flag.type. The detection service only
# supplies machine-readable issue types; this is where plain-language
# text lives, since that's not the detection service's job.
_FLAG_COPY: dict[str, dict[str, Any]] = {
    "marital_status_mismatch": {
        "title": "Unexpected Marriage on Record",
        "plainExplanation": (
            "Our records show you're listed as married, but this doesn't match what you told us. "
            "This can happen when someone fraudulently registers a marriage using your ID."
        ),
        "nextSteps": [
            "Confirm your real marital status by SMSing 'M' + your ID number to 32551 (free)",
            "If the result is wrong, report it to SAPS and get a case number",
            "Call the DHA Fraud Unit on 0800 60 11 90 to open an investigation",
            "Submit a formal dispute at your nearest Home Affairs office",
        ],
    },
    "duplicate_id": {
        "title": "Duplicate ID Number Detected",
        "plainExplanation": (
            "Your ID number appears more than once in Home Affairs records, linked to different "
            "personal details. This is a common sign your identity has been used fraudulently."
        ),
        "nextSteps": [
            "Report the duplication to SAPS and get a case number",
            "Call the DHA Fraud Unit on 0800 60 11 90 to open an investigation",
            "Apply for a new smart ID card at your nearest Home Affairs office once the case is logged",
            "Keep the case number safe — you'll need it for any bank or service provider disputes",
        ],
    },
    "deceased_flag": {
        "title": "You're Marked as Deceased",
        "plainExplanation": (
            "Home Affairs records incorrectly show you as deceased. This can block access to "
            "banking, social grants, and other services until it's corrected."
        ),
        "nextSteps": [
            "Go in person to your nearest Home Affairs office — this cannot be fixed remotely",
            "Bring your green barcoded ID book or smart ID card and proof of life (e.g. an affidavit)",
            "Ask for the death flag to be reversed and request written confirmation",
            "Call the DHA Contact Centre on 0800 60 11 90 for urgent escalation",
        ],
    },
    "blocked_id": {
        "title": "Your ID Number Is Blocked",
        "plainExplanation": (
            "Your ID number has been flagged and blocked, which can prevent you from accessing "
            "services that rely on ID verification."
        ),
        "nextSteps": [
            "Visit your nearest Home Affairs office to find out why the block was placed",
            "Bring your ID document and any supporting paperwork you have",
            "Ask for a formal reason and a reference number for the block",
            "Call the DHA Contact Centre on 0800 60 11 90 if you need to escalate",
        ],
    },
    "no_flags": {
        "title": "No Issues Found",
        "plainExplanation": (
            "We didn't find any identity-integrity problems on your record. Your ID number, "
            "marital status, and status flags all look clean in our demo dataset."
        ),
        "nextSteps": [
            "No action needed right now",
            "It's still good practice to check again periodically",
        ],
    },
}

_GENERIC_UNKNOWN_COPY = {
    "title": "Issue Detected",
    "plainExplanation": "We detected an issue with your record that doesn't match a known category.",
    "nextSteps": [
        "Visit your nearest Home Affairs office for assistance",
        "Call the DHA Contact Centre on 0800 60 11 90",
    ],
}


def _adapt_detection_result(result: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """Translate the detection service's {status, riskLevel, issues} shape
    into a list of API flag objects plus the cleanRecord bool."""
    status = (result.get("status") or "").upper()
    if status == "CLEAR":
        return [{"type": "no_flags", "severity": "low", **_FLAG_COPY["no_flags"]}], True

    severity = (result.get("riskLevel") or "MEDIUM").lower()
    flags: list[dict[str, Any]] = []
    for issue in result.get("issues", []):
        raw_type = issue.get("type") or ""
        mapped_type = _ISSUE_TYPE_MAP.get(raw_type)
        if mapped_type is None:
            logger.warning("Unknown detection issue type %r; emitting generic flag", raw_type)
            flags.append({
                "type": raw_type.lower() if raw_type else "unknown",
                "severity": "medium",
                "title": _GENERIC_UNKNOWN_COPY["title"],
                "plainExplanation": issue.get("message") or _GENERIC_UNKNOWN_COPY["plainExplanation"],
                "nextSteps": _GENERIC_UNKNOWN_COPY["nextSteps"],
            })
            continue
        flags.append({"type": mapped_type, "severity": severity, **_FLAG_COPY[mapped_type]})
    return flags, False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/api/check-identity", response_model=None)
def check_identity(payload: CheckIdentityRequest) -> dict[str, Any] | JSONResponse:
    """Look up an SA ID number and return plain-language identity flags."""
    try:
        id_number = validate_id_number(payload.idNumber)
    except InvalidIdNumberError:
        return JSONResponse(status_code=400, content={"error": True, "message": "Invalid ID number format"})

    records = db.get_records_for_id(id_number)
    if not records:
        return {
            "found": False,
            "idNumber": id_number,
            "flags": [],
            "cleanRecord": False,
            "message": "No record found for this ID number in our demo dataset.",
        }

    result = _run_detection(id_number, records[0])
    flags, clean_record = _adapt_detection_result(result)
    logger.info("check-identity %s -> cleanRecord=%s flags=%d", db.mask_id(id_number), clean_record, len(flags))
    return {
        "found": True,
        "idNumber": id_number,
        "flags": flags,
        "cleanRecord": clean_record,
    }


# ---------------------------------------------------------------------------
# PLACEHOLDER — owned by chatbot pair, replace on integration
# ---------------------------------------------------------------------------

_CHAT_CANDIDATE_FN_NAMES = ("get_guidance", "handle_chat", "chat", "answer")

try:
    from backend.services import home_affairs_guide as _home_affairs_guide_module
except ImportError:
    _home_affairs_guide_module = None

_home_affairs_fn = None
for _name in _CHAT_CANDIDATE_FN_NAMES:
    _fn = getattr(_home_affairs_guide_module, _name, None)
    if callable(_fn):
        _home_affairs_fn = _fn
        logger.info("Chat: bound to home_affairs_guide.%s", _name)
        break
if _home_affairs_fn is None:
    logger.info("Chat: home_affairs_guide has no recognized entry point yet; using placeholder stub")


def _chat_stub(message: str, location: LocationModel | None) -> dict[str, Any]:
    """Hardcoded placeholder response so the frontend can wire up the
    chat feature today, independent of the chatbot pair's progress."""
    nearest_branch = None
    if location is not None:
        nearest_branch = {
            "name": "Cape Town Home Affairs",
            "address": "56 Barrack Street, Cape Town City Centre, 8001",
            "distanceKm": 3.2,
        }
    return {
        "reply": (
            "To register your baby's birth, visit your nearest Home Affairs office within 30 "
            "days so it's free of charge."
        ),
        "documentsNeeded": [
            "Both parents' ID documents (or the mother's ID if unmarried and the father is absent)",
            "Notice of Birth (BI-24) from the hospital or clinic",
            "Proof of marriage, if applicable",
        ],
        "estimatedCost": "Free if registered within 30 days of birth; a late-registration penalty applies after that",
        "estimatedTime": "Same day at the office, once documents are in order",
        "nearestBranch": nearest_branch,
    }


@router.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    """Delegates to home_affairs_guide.answer() when bound (see the binding
    block above); falls back to the hardcoded _chat_stub() placeholder if
    that module is unavailable or raises. conversationId lets the callee
    track multi-turn state per conversation instead of guessing a session."""
    if _home_affairs_fn is not None:
        try:
            return _home_affairs_fn(
                payload.message,
                payload.location.model_dump() if payload.location else None,
                payload.conversationId,
            )
        except Exception:
            logger.exception("home_affairs_guide raised; falling back to placeholder stub")
    return _chat_stub(payload.message, payload.location)
