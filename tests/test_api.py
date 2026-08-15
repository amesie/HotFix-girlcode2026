"""Tests for the API layer: backend/main.py, backend/api/routes.py, and
backend/database/database.py.

Every test that touches the DB uses a temporary file via the `client`
fixture below — never the real data/verifi.db. MARRIAGES_JSON_PATH is
also pointed at a nonexistent path so seeding deterministically falls
back to the fixed 5-record demo dataset regardless of what the
teammate's real marriages.json currently contains.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api import routes
from backend.database import database as db

# Luhn-valid, calendar-valid, 13-digit ID that is deliberately NOT one of
# the 5 demo IDs and NOT seeded anywhere — used for the not-found case.
VALID_UNKNOWN_ID = "9905155800080"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "MARRIAGES_JSON_PATH", tmp_path / "does_not_exist.json")
    monkeypatch.setattr(db, "_last_seed_source", None)

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# The five demo scenarios
# ---------------------------------------------------------------------------

_SCENARIOS = [
    ("9001015800083", True, "no_flags", "low"),
    ("8505124800086", False, "marital_status_mismatch", "high"),
    ("7712089800081", False, "duplicate_id", "medium"),
    ("6003215800084", False, "deceased_flag", "high"),
    ("9506306800082", False, "blocked_id", "high"),
]


@pytest.mark.parametrize("id_number, clean_record, flag_type, severity", _SCENARIOS)
def test_check_identity_demo_scenarios(client, id_number, clean_record, flag_type, severity):
    response = client.post("/api/check-identity", json={"idNumber": id_number})
    assert response.status_code == 200

    body = response.json()
    assert body["found"] is True
    assert body["idNumber"] == id_number
    assert body["cleanRecord"] is clean_record
    assert len(body["flags"]) == 1

    flag = body["flags"][0]
    assert flag["type"] == flag_type
    assert flag["severity"] == severity
    assert flag["title"]
    assert flag["plainExplanation"]
    assert isinstance(flag["nextSteps"], list) and flag["nextSteps"]


def test_check_identity_not_found(client):
    response = client.post("/api/check-identity", json={"idNumber": VALID_UNKNOWN_ID})
    assert response.status_code == 200

    body = response.json()
    assert body == {
        "found": False,
        "idNumber": VALID_UNKNOWN_ID,
        "flags": [],
        "cleanRecord": False,
        "message": "No record found for this ID number in our demo dataset.",
    }


def test_check_identity_malformed_input_returns_error_shape(client):
    response = client.post("/api/check-identity", json={"idNumber": "123"})
    assert response.status_code == 400
    assert response.json() == {"error": True, "message": "Invalid ID number format"}


def test_check_identity_missing_field_returns_error_shape(client):
    response = client.post("/api/check-identity", json={})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] is True
    assert isinstance(body["message"], str)


def test_check_identity_strips_spaces_and_dashes(client):
    spaced = "850512 4800-086"
    response = client.post("/api/check-identity", json={"idNumber": spaced})
    assert response.status_code == 200
    assert response.json()["idNumber"] == "8505124800086"


# ---------------------------------------------------------------------------
# ID validation
# ---------------------------------------------------------------------------


def test_validate_id_number_rejects_bad_date():
    with pytest.raises(routes.InvalidIdNumberError):
        routes.validate_id_number("9913015800083")  # month 13 doesn't exist


def test_validate_id_number_rejects_failed_luhn_when_demo_ids_disallowed(monkeypatch):
    monkeypatch.setenv("ALLOW_DEMO_IDS", "false")
    with pytest.raises(routes.InvalidIdNumberError):
        routes.validate_id_number("9001015800083")


def test_validate_id_number_allows_demo_id_bypass_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_DEMO_IDS", raising=False)
    assert routes.validate_id_number("9001015800083") == "9001015800083"


def test_validate_id_number_accepts_genuinely_valid_luhn_id():
    assert routes.validate_id_number(VALID_UNKNOWN_ID) == VALID_UNKNOWN_ID


# ---------------------------------------------------------------------------
# Adapter: teammate's detection shape -> API contract
# ---------------------------------------------------------------------------


def test_adapter_translates_clear_status():
    flags, clean_record = routes._adapt_detection_result({"status": "CLEAR", "riskLevel": "LOW", "issues": []})
    assert clean_record is True
    assert flags == [{"type": "no_flags", "severity": "low", **routes._FLAG_COPY["no_flags"]}]


@pytest.mark.parametrize(
    "issue_type, expected_flag_type",
    [
        ("MULTIPLE_ACTIVE_MARRIAGES", "marital_status_mismatch"),
        ("DUPLICATE_ID_NUMBER", "duplicate_id"),
        ("DECEASED_FLAG", "deceased_flag"),
        ("BLOCKED_ID", "blocked_id"),
    ],
)
def test_adapter_maps_known_issue_types(issue_type, expected_flag_type):
    result = {
        "status": "FLAGGED",
        "riskLevel": "HIGH",
        "issues": [{"type": issue_type, "message": "irrelevant, copy comes from routes.py"}],
    }
    flags, clean_record = routes._adapt_detection_result(result)
    assert clean_record is False
    assert flags[0]["type"] == expected_flag_type
    assert flags[0]["severity"] == "high"


def test_adapter_handles_unknown_issue_type_without_crashing():
    result = {
        "status": "FLAGGED",
        "riskLevel": "MEDIUM",
        "issues": [{"type": "SOME_NEW_ISSUE_TYPE", "message": "a brand new kind of problem"}],
    }
    flags, clean_record = routes._adapt_detection_result(result)
    assert clean_record is False
    assert len(flags) == 1
    assert flags[0]["severity"] == "medium"
    assert flags[0]["plainExplanation"] == "a brand new kind of problem"


# ---------------------------------------------------------------------------
# Resilient import / graceful fallback when identity_checker is absent
# ---------------------------------------------------------------------------


def test_bind_detection_function_falls_back_to_mock_when_module_missing():
    fn, mode, bound_name = routes._bind_detection_function(None)
    assert fn is None
    assert mode == "mock"
    assert bound_name is None


def test_bind_detection_function_binds_to_first_matching_name():
    class FakeModule:
        def check(self, id_number):
            return {"status": "CLEAR", "riskLevel": "LOW", "issues": []}

    fn, mode, bound_name = routes._bind_detection_function(FakeModule())
    assert mode == "real"
    assert bound_name == "check"
    assert fn("anything") == {"status": "CLEAR", "riskLevel": "LOW", "issues": []}


def test_bind_detection_function_mock_when_no_recognized_entry_point():
    class EmptyModule:
        pass

    fn, mode, bound_name = routes._bind_detection_function(EmptyModule())
    assert fn is None
    assert mode == "mock"


def test_run_detection_falls_back_to_mock_if_real_service_raises(monkeypatch):
    def broken(id_number):
        raise RuntimeError("teammate's code isn't done yet")

    monkeypatch.setattr(routes, "_detection_fn", broken)
    record = {"is_deceased": 0, "is_blocked": 0, "duplicate_of": None}
    result = routes._run_detection("9001015800083", record)
    assert result["status"] == "CLEAR"  # falls through to _mock_detect


# ---------------------------------------------------------------------------
# Seed idempotency
# ---------------------------------------------------------------------------


def test_seed_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "idempotency.db")
    monkeypatch.setattr(db, "MARRIAGES_JSON_PATH", tmp_path / "does_not_exist.json")
    monkeypatch.setattr(db, "_last_seed_source", None)

    db.init_db()
    db.seed()
    first_count = db.health()["recordCount"]

    db.seed()
    db.seed()
    second_count = db.health()["recordCount"]

    assert first_count == 5
    assert second_count == 5
    assert len(db.all_records()) == 5


def test_seed_upserts_from_valid_json(tmp_path, monkeypatch):
    json_path = tmp_path / "marriages.json"
    json_path.write_text(
        '[{"id_number": "1111111111111", "marital_status": "married", '
        '"is_deceased": false, "is_blocked": false, "duplicate_of": null, "notes": "test"}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "json_seed.db")
    monkeypatch.setattr(db, "MARRIAGES_JSON_PATH", json_path)
    monkeypatch.setattr(db, "_last_seed_source", None)

    db.init_db()
    db.seed()

    assert db.health()["seededFrom"] == "json"
    records = db.get_records_for_id("1111111111111")
    assert len(records) == 1
    assert records[0]["marital_status"] == "married"


def test_seed_keeps_existing_data_when_json_becomes_malformed(tmp_path, monkeypatch):
    json_path = tmp_path / "marriages.json"
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "malformed.db")
    monkeypatch.setattr(db, "MARRIAGES_JSON_PATH", json_path)
    monkeypatch.setattr(db, "_last_seed_source", None)

    db.init_db()
    db.seed()  # no JSON yet -> fallback data
    assert db.health()["recordCount"] == 5

    json_path.write_text("{not valid json", encoding="utf-8")
    db.reseed()  # malformed -> must keep serving existing data, not crash

    assert db.health()["recordCount"] == 5


# ---------------------------------------------------------------------------
# Health and chat placeholder
# ---------------------------------------------------------------------------


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["datasource"] == "sqlite"
    assert body["seededFrom"] == "fallback"
    assert body["recordCount"] == 5
    assert body["detection"] in ("real", "mock")


def test_chat_binds_to_home_affairs_guide_and_reaches_a_full_checklist(client):
    # backend/services/home_affairs_guide.py now defines answer(), so routes.py's
    # existing _CHAT_CANDIDATE_FN_NAMES binding picks it up over _chat_stub().
    # "spelling error" is the one sub-case with no follow-up complications
    # question, so a single message reaches a full checklist.
    from backend.services import home_affairs_guide

    home_affairs_guide.reset_sessions()
    response = client.post("/api/chat", json={"message": "how do I fix my name, there's a spelling mistake"})
    home_affairs_guide.reset_sessions()

    assert response.status_code == 200
    body = response.json()
    assert body["nearestBranch"] is None
    assert isinstance(body["documentsNeeded"], list) and body["documentsNeeded"]


def test_chat_never_fabricates_a_branch_even_with_location(client):
    # home_affairs_guide has no branch-location data source, so it honestly
    # returns None rather than inventing an address the way the old stub did.
    from backend.services import home_affairs_guide

    home_affairs_guide.reset_sessions()
    response = client.post(
        "/api/chat",
        json={"message": "baby", "location": {"lat": -33.9249, "lng": 18.4241}},
    )
    home_affairs_guide.reset_sessions()

    assert response.status_code == 200
    body = response.json()
    assert body["nearestBranch"] is None
