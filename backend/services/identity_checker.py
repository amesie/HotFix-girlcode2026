import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic"
    / "marriages.json"
)


def load_records():
    """Load synthetic identity records from the JSON dataset."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def check_identity(id_number):
    """
    Check a synthetic ID against the demo dataset.

    This function uses synthetic data only.
    It does not connect to real Home Affairs records.
    """

    records = load_records()

    record = next(
        (item for item in records if item["idNumber"] == id_number),
        None
    )

    # ID does not exist in the demo dataset
    if record is None:
        return {
            "found": False,
            "idNumber": id_number,
            "flags": [],
            "cleanRecord": False,
            "message": "No record found for this ID number in our demo dataset."
        }

    flags = []

    # Check for fraudulent or unexpected marriage
    if record.get("scenario") == "fraudulent_marriage":
        flags.append({
            "type": "marital_status_mismatch",
            "severity": "high",
            "title": "Unexpected Marriage on Record",
            "plainExplanation": (
                "The demo record shows a marriage that does not match "
                "the expected marital status."
            ),
            "nextSteps": [
                "Verify the information with Home Affairs.",
                "Report suspected identity fraud to the appropriate authorities.",
                "Keep a record of your case or reference number."
            ]
        })

    # Check for duplicate ID
    if record.get("duplicate") is True:
        flags.append({
            "type": "duplicate_id",
            "severity": "high",
            "title": "Possible Duplicate ID",
            "plainExplanation": (
                "The demo record contains a duplicate identity indicator."
            ),
            "nextSteps": [
                "Contact Home Affairs for verification.",
                "Request clarification about the duplicate record.",
                "Keep any reference number provided."
            ]
        })

    # Check for deceased flag
    if record.get("deceased") is True:
        flags.append({
            "type": "deceased_flag",
            "severity": "high",
            "title": "Deceased Status Flag",
            "plainExplanation": (
                "The demo record contains a deceased-status indicator."
            ),
            "nextSteps": [
                "Contact Home Affairs immediately for verification.",
                "Request correction of the record if it is incorrect."
            ]
        })

    # Check for blocked ID
    if record.get("blocked") is True:
        flags.append({
            "type": "blocked_id",
            "severity": "high",
            "title": "Blocked Identity Record",
            "plainExplanation": (
                "The demo record indicates that the identity record is blocked."
            ),
            "nextSteps": [
                "Contact Home Affairs to determine why the record is blocked.",
                "Request the appropriate process for resolving the issue."
            ]
        })

    return {
        "found": True,
        "idNumber": id_number,
        "flags": flags,
        "cleanRecord": len(flags) == 0
    }