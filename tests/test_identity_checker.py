import pytest

from backend.services.identity_checker import check_identity


def test_clean_record():
    result = check_identity("DEMO-ID-001")

    assert result["found"] is True
    assert result["flags"] == []
    assert result["cleanRecord"] is True


def test_fraudulent_marriage():
    result = check_identity("DEMO-ID-002")

    assert result["found"] is True
    assert result["cleanRecord"] is False
    assert result["flags"][0]["type"] == "marital_status_mismatch"
    assert result["flags"][0]["severity"] == "high"


def test_duplicate_id():
    result = check_identity("DEMO-ID-003")

    assert result["found"] is True
    assert result["cleanRecord"] is False
    assert result["flags"][0]["type"] == "duplicate_id"


def test_deceased_flag():
    result = check_identity("DEMO-ID-004")

    assert result["found"] is True
    assert result["cleanRecord"] is False
    assert result["flags"][0]["type"] == "deceased_flag"
    assert result["flags"][0]["severity"] == "high"


def test_blocked_id():
    result = check_identity("DEMO-ID-005")

    assert result["found"] is True
    assert result["cleanRecord"] is False
    assert result["flags"][0]["type"] == "blocked_id"


def test_unknown_id():
    result = check_identity("DEMO-ID-999")

    assert result["found"] is False
    assert result["flags"] == []
    assert result["cleanRecord"] is False