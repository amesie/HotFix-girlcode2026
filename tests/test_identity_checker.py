import pytest

from backend.services.identity_checker import check_identity

# Same 5 canonical demo IDs used throughout backend/api/routes.py
# (_DEMO_IDS, _MOCK_RESULTS) and backend/database/database.py
# (_FALLBACK_RECORDS), and now seeded under data/synthetic/marriages.json.
CLEAN_ID = "9001015800083"
FRAUDULENT_MARRIAGE_ID = "8505124800086"
DUPLICATE_ID = "7712089800081"
DECEASED_ID = "6003215800084"
BLOCKED_ID = "9506306800082"

# Luhn-valid, calendar-valid, but not seeded anywhere.
UNKNOWN_ID = "9905155800080"


def test_clean_record():
    result = check_identity(CLEAN_ID)

    assert result["status"] == "CLEAR"
    assert result["issues"] == []


def test_fraudulent_marriage():
    result = check_identity(FRAUDULENT_MARRIAGE_ID)

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "HIGH"
    assert result["issues"][0]["type"] == "MULTIPLE_ACTIVE_MARRIAGES"


def test_duplicate_id():
    result = check_identity(DUPLICATE_ID)

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "MEDIUM"
    assert result["issues"][0]["type"] == "DUPLICATE_ID_NUMBER"


def test_deceased_flag():
    result = check_identity(DECEASED_ID)

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "HIGH"
    assert result["issues"][0]["type"] == "DECEASED_FLAG"


def test_blocked_id():
    result = check_identity(BLOCKED_ID)

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "HIGH"
    assert result["issues"][0]["type"] == "BLOCKED_ID"


def test_unknown_id_raises_lookup_error():
    # routes.py's _run_detection() catches this and falls back to the
    # DB-record-derived mock detector instead of guessing "clean".
    with pytest.raises(LookupError):
        check_identity(UNKNOWN_ID)
