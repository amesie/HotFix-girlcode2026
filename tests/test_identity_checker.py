import pytest

from backend.services.identity_checker import check_identity


def test_clean_record():
    result = check_identity("DEMO-ID-001")

    assert result["status"] == "CLEAR"
    assert result["issues"] == []


def test_fraudulent_marriage():
    result = check_identity("DEMO-ID-002")

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "HIGH"
    assert result["issues"][0]["type"] == "MULTIPLE_ACTIVE_MARRIAGES"


def test_duplicate_id():
    result = check_identity("DEMO-ID-003")

    assert result["status"] == "FLAGGED"
    assert result["issues"][0]["type"] == "DUPLICATE_ID_NUMBER"


def test_deceased_flag():
    result = check_identity("DEMO-ID-004")

    assert result["status"] == "FLAGGED"
    assert result["riskLevel"] == "HIGH"
    assert result["issues"][0]["type"] == "DECEASED_FLAG"


def test_blocked_id():
    result = check_identity("DEMO-ID-005")

    assert result["status"] == "FLAGGED"
    assert result["issues"][0]["type"] == "BLOCKED_ID"


def test_unknown_id_raises_lookup_error():
    # routes.py's _run_detection() catches this and falls back to the
    # DB-record-derived mock detector instead of guessing "clean".
    with pytest.raises(LookupError):
        check_identity("DEMO-ID-999")
