import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic"
    / "marriages.json"
)

# Matches the severity taxonomy routes.py already uses in _MOCK_RESULTS —
# duplicate-ID hits are MEDIUM, everything else here is HIGH.
_ISSUE_RISK_LEVEL = {
    "MULTIPLE_ACTIVE_MARRIAGES": "HIGH",
    "DUPLICATE_ID_NUMBER": "MEDIUM",
    "DECEASED_FLAG": "HIGH",
    "BLOCKED_ID": "HIGH",
}
_RISK_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def load_records():
    """Load synthetic identity records from the JSON dataset."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def check_identity(id_number):
    """
    Check a synthetic ID against the demo dataset.

    This function uses synthetic data only.
    It does not connect to real Home Affairs records.

    Returns the raw-detection shape backend/api/routes.py's
    _adapt_detection_result() expects: {"status": "CLEAR" | "FLAGGED",
    "riskLevel": "LOW" | "MEDIUM" | "HIGH", "issues": [{"type", "message"}]}.
    routes.py owns turning `issues` into user-facing flag copy via
    _ISSUE_TYPE_MAP / _FLAG_COPY — this function only reports what it found.

    Raises LookupError if id_number isn't in this dataset, so routes.py's
    existing _run_detection() fallback (to the DB-record-derived mock) takes
    over instead of this function silently guessing "clean".
    """

    records = load_records()

    record = next(
        (item for item in records if item["idNumber"] == id_number),
        None
    )

    if record is None:
        raise LookupError(f"No demo record found for id_number {id_number!r}")

    issues = []

    # Check for fraudulent or unexpected marriage
    if record.get("scenario") == "fraudulent_marriage":
        issues.append({
            "type": "MULTIPLE_ACTIVE_MARRIAGES",
            "message": (
                "The demo record shows a marriage that does not match "
                "the expected marital status."
            ),
        })

    # Check for duplicate ID
    if record.get("duplicate") is True:
        issues.append({
            "type": "DUPLICATE_ID_NUMBER",
            "message": "The demo record contains a duplicate identity indicator.",
        })

    # Check for deceased flag
    if record.get("deceased") is True:
        issues.append({
            "type": "DECEASED_FLAG",
            "message": "The demo record contains a deceased-status indicator.",
        })

    # Check for blocked ID
    if record.get("blocked") is True:
        issues.append({
            "type": "BLOCKED_ID",
            "message": "The demo record indicates that the identity record is blocked.",
        })

    if not issues:
        return {"status": "CLEAR", "riskLevel": "LOW", "issues": []}

    risk_level = max(
        (_ISSUE_RISK_LEVEL.get(issue["type"], "MEDIUM") for issue in issues),
        key=_RISK_LEVEL_RANK.get,
    )
    return {"status": "FLAGGED", "riskLevel": risk_level, "issues": issues}