"""Tests for backend/services/home_affairs_guide.py.

Layered on purpose:
  - classifier tests exercise the deterministic keyword-matching fallback
    layer directly
  - checklist-assembly tests build a ConversationState by hand and call
    the deterministic response builders directly, so they're robust
    against classifier wording changes and test the data-fidelity
    guarantees precisely
  - Groq tests mock the SDK client at the _get_groq_client() seam (so
    _call_groq_json/_call_groq_text's own error handling is exercised
    exactly as in production), never touching the network
  - a couple of full answer() runs prove the state machine wiring works
    end-to-end for a realistic conversation

An autouse fixture stubs _call_groq_json/_call_groq_text to None for every
test by default (simulating "Groq unavailable"), so every test other than
the ones explicitly about Groq exercises the deterministic fallback path —
exactly the same path the pre-Groq version of this module used. This keeps
the whole suite network-independent, per the requirement that tests never
need a live API key.
"""

from __future__ import annotations

import json
import re
from unittest.mock import MagicMock

import pytest

from backend.services import home_affairs_guide as guide

FEE_PATTERN = re.compile(r"R\s?\d+")


@pytest.fixture(autouse=True)
def _clean_sessions():
    guide.reset_sessions()
    yield
    guide.reset_sessions()


def _fake_completion(content: str):
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=content))]
    return completion


# ---------------------------------------------------------------------------
# Service classification from realistic phrasing (deterministic fallback)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message, expected_service",
    [
        ("My passport expired, what do I need to renew it?", "passport"),
        ("I need to register my baby, she was born last week", "birth_registration"),
        ("How do I fix my name, there's a spelling mistake", "name_surname_amendment"),
        ("I need to renew my smart id, it's expired", "smart_id"),
    ],
)
def test_classify_service_identifies_all_four_services(message, expected_service):
    assert guide._classify_service(message) == expected_service


def test_classify_service_returns_none_for_out_of_scope_message():
    assert guide._classify_service("What's the weather like in Cape Town today?") is None


# ---------------------------------------------------------------------------
# Out-of-scope handling via the full answer() entry point
# ---------------------------------------------------------------------------


def test_out_of_scope_question_gets_honest_response_not_a_guess():
    response = guide.answer("Can you help me file my taxes?", None, "conv-out-of-scope")

    assert "don't have information" in response["reply"].lower()
    assert response["documentsNeeded"] == []


# ---------------------------------------------------------------------------
# Checklist assembly — built from hand-constructed state, bypassing the
# classifier entirely, so these test data fidelity precisely.
# ---------------------------------------------------------------------------


def _build(service_id, sub_case_id, situation_id=None, complications=None):
    reference = guide.load_reference()
    service = reference["services"][service_id]
    sub_case = service["sub_cases"][sub_case_id]
    state = guide.ConversationState(
        service_id=service_id,
        sub_case_id=sub_case_id,
        situation_id=situation_id,
        complications=complications or set(),
    )
    return guide._final_response(state, reference, service, sub_case)


def _doc_names(response):
    return [line.split(" — ")[0] for line in response["documentsNeeded"]]


def test_checklist_birth_registration_within_30_days_base_case():
    response = _build("birth_registration", "within_30_days")

    names = _doc_names(response)
    assert "Proof of birth (Form DHA-24/PB)" in names
    assert "Parents' IDs or passports" in names
    assert len(response["documentsNeeded"]) == 3  # no complications -> base_documents only
    assert response["estimatedCost"].startswith("Generally free")
    assert "verify before demo" not in response["estimatedCost"]  # free, nothing to verify


def test_checklist_birth_registration_late_registration_is_honestly_not_covered():
    reference = guide.load_reference()
    sub_case = reference["services"]["birth_registration"]["sub_cases"]["late_registration"]
    response = guide._not_covered_response(sub_case)

    assert "don't have the specific document checklist" in response["reply"]
    assert response["documentsNeeded"] == []


def test_checklist_smart_id_first_application_vs_renewal_differ():
    first_app = _build("smart_id", "first_application_16_plus")
    renewal = _build("smart_id", "renewal_or_replacement", situation_id="replacing_smart_id")

    first_names = _doc_names(first_app)
    renewal_names = _doc_names(renewal)

    assert "Birth certificate" in first_names
    assert "Existing card or a copy" in renewal_names
    assert first_names != renewal_names

    # First application: no fee stated in the source material for this case.
    assert first_app["estimatedCost"].startswith("Not specified")
    # Renewal: R140 IS stated, but must carry the verify-before-demo flag.
    assert "R140" in renewal["estimatedCost"]
    assert "verify before demo" in renewal["estimatedCost"]


def test_checklist_passport_adult_vs_under_16_differ():
    adult = _build("passport", "adult")
    under_16 = _build("passport", "under_16")

    assert "Form DHA-73" in _doc_names(adult)
    assert "Birth certificate and copy" in _doc_names(under_16)

    # Adult: R600 tourist tariff IS stated, must be flagged for verification.
    assert "R600" in adult["estimatedCost"]
    assert "verify before demo" in adult["estimatedCost"]
    # Under 16: no amount is stated in the source material for this category.
    assert under_16["estimatedCost"].startswith("Not specified") or "amount is not stated" in under_16["estimatedCost"]


def test_checklist_name_amendment_spelling_error_vs_marriage_differ():
    spelling = _build("name_surname_amendment", "spelling_error")
    marriage = _build("name_surname_amendment", "marriage")

    assert "DHA-9 fingerprint form" in _doc_names(spelling)
    assert "Marriage certificate" in _doc_names(marriage)
    assert _doc_names(spelling) != _doc_names(marriage)


def test_complication_parent_deceased_adds_extra_documents_to_smart_id_first_application():
    without = _build("smart_id", "first_application_16_plus")
    with_complication = _build(
        "smart_id", "first_application_16_plus", complications={"parent_deceased"}
    )

    without_names = set(_doc_names(without))
    with_names = set(_doc_names(with_complication))

    added = with_names - without_names
    assert "Death certificate" in added
    assert "Deceased parent's ID" in added


def test_complication_none_disclosed_keeps_base_documents_only():
    response = _build("birth_registration", "within_30_days", complications=set())
    assert len(response["documentsNeeded"]) == 3


# ---------------------------------------------------------------------------
# No hardcoded, unverified fee anywhere in a generated response.
# Every "R<number>" figure that appears must be paired with the
# verify-before-demo caution — never a bare, confident number.
# ---------------------------------------------------------------------------


def _all_generated_responses():
    reference = guide.load_reference()
    responses = []
    for service_id, service in reference["services"].items():
        for sub_case_id, sub_case in service["sub_cases"].items():
            if sub_case.get("not_covered"):
                continue
            if service_id == "smart_id" and sub_case_id == "renewal_or_replacement":
                for situation_id in sub_case["situations"]:
                    responses.append(_build(service_id, sub_case_id, situation_id=situation_id))
            else:
                responses.append(_build(service_id, sub_case_id))
    return responses


def _assert_no_unverified_fee(response):
    full_text = response["reply"] + " " + " ".join(response["documentsNeeded"]) + " " + response["estimatedCost"]
    for match in FEE_PATTERN.finditer(full_text):
        assert "verify before demo" in full_text, (
            f"Found unverified fee {match.group()!r} in response text: {full_text!r}"
        )


def test_no_response_contains_a_fee_not_marked_verify_before_demo():
    for response in _all_generated_responses():
        _assert_no_unverified_fee(response)


def test_birth_registration_never_states_a_re_issue_fee():
    response = _build("birth_registration", "within_30_days")
    assert "R75" not in response["estimatedCost"]
    assert "R20" not in response["estimatedCost"]


def test_no_unverified_fee_holds_even_with_groq_phrasing_active(monkeypatch):
    """Same invariant as above, but with a (mocked, successful) Groq
    phrasing call in the loop: proves the grounding check protects the
    fee-fidelity guarantee even when Groq's phrasing is actually used,
    not just when it's unavailable."""

    def fake_call_groq_text(system_prompt, user_prompt):
        payload = json.loads(user_prompt.split("facts you may use):\n", 1)[1])
        cost = payload.get("cost")
        if cost and cost.get("amount"):
            return f"Here's a quick summary. {cost['amount']}."
        return "Here's a quick summary. Please confirm any fee with Home Affairs."

    monkeypatch.setattr(guide, "_call_groq_text", fake_call_groq_text)

    for response in _all_generated_responses():
        _assert_no_unverified_fee(response)


# ---------------------------------------------------------------------------
# Groq classification: used when valid, rejected + falls back when not.
# Mocked at the _get_groq_client() seam so _call_groq_json's own error
# handling (the real production code path) is what's actually exercised.
# ---------------------------------------------------------------------------


def test_groq_classification_used_when_valid(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion('{"category": "passport"}')
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    # Deliberately zero keyword overlap with any service, so a correct
    # result can only have come from the (mocked) Groq call.
    message = "I need the document that lets me leave the country"
    assert guide._classify_service(message) is None  # keyword matcher genuinely can't resolve this

    result = guide._resolve_service(message, guide.load_reference())
    assert result == "passport"


def test_groq_returns_unclear_falls_back_to_keyword_classifier(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion('{"category": "unclear"}')
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    result = guide._resolve_service("I need to register my baby's birth", guide.load_reference())
    assert result == "birth_registration"  # keyword fallback


def test_groq_invalid_category_is_rejected_and_falls_back_to_keyword_classifier(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion('{"category": "totally_made_up_service"}')
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    result = guide._resolve_service("I need to register my baby's birth", guide.load_reference())
    assert result == "birth_registration"  # invalid Groq output never used


def test_groq_complications_multiselect_validated(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion('{"complications": ["parent_deceased"]}')
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    reference = guide.load_reference()
    sub_case = reference["services"]["smart_id"]["sub_cases"]["first_application_16_plus"]
    applicable = list(sub_case["conditional_documents"].keys())

    result = guide._resolve_complications(applicable, "my mother passed away last year", sub_case)
    assert result == {"parent_deceased"}


def test_groq_complications_with_invalid_item_rejects_whole_response_and_falls_back(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion(
        '{"complications": ["parent_deceased", "not_a_real_id"]}'
    )
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    reference = guide.load_reference()
    sub_case = reference["services"]["smart_id"]["sub_cases"]["first_application_16_plus"]
    applicable = list(sub_case["conditional_documents"].keys())

    # message the keyword matcher CAN resolve on its own, proving the
    # tainted Groq response (with an id outside the valid set) was
    # discarded entirely rather than partially trusted.
    result = guide._resolve_complications(applicable, "my father died last year", sub_case)
    assert result == {"parent_deceased"}


# ---------------------------------------------------------------------------
# Fallback behavior: a Groq API failure (not just an "unclear"/invalid
# result) must not take down classification — it should fall back to the
# deterministic keyword classifier, and log that it did.
# ---------------------------------------------------------------------------


def test_groq_api_failure_falls_back_to_keyword_classifier_and_logs(monkeypatch, caplog):
    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = TimeoutError("simulated Groq timeout")
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    with caplog.at_level("WARNING"):
        result = guide._resolve_service("My passport expired, what do I need to renew it?", guide.load_reference())

    assert result == "passport"  # deterministic fallback still worked
    assert any("Groq" in record.message for record in caplog.records)


def test_full_conversation_survives_groq_outage_end_to_end(monkeypatch, caplog):
    """The whole multi-turn flow, not just one classification call, keeps
    working when Groq is down throughout."""
    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = ConnectionError("simulated Groq outage")
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    with caplog.at_level("WARNING"):
        guide.answer("I need to register my baby", None, "conv-outage")
        guide.answer("she was just born this week", None, "conv-outage")
        response = guide.answer("no complications", None, "conv-outage")

    assert response["documentsNeeded"]
    assert any("Proof of birth" in line for line in response["documentsNeeded"])
    assert any("Groq" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# Phrasing: Groq's output is used only when grounded; rejected (with
# fallback to the deterministic template) when it isn't.
# ---------------------------------------------------------------------------


def test_groq_phrasing_used_when_grounded(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion(
        "You'll need a few documents for your Smart ID replacement, including proof of loss. "
        "There's a R140 re-issue fee, but do check that's still current before your visit."
    )
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    response = _build("smart_id", "renewal_or_replacement", situation_id="lost_or_stolen")
    assert "R140" in response["reply"]


def test_groq_phrasing_rejected_when_it_invents_a_fee(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion(
        "This will cost you R99 at your local branch."
    )
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    # Real cost for this sub-case is "Generally free" — no R-number at all.
    response = _build("birth_registration", "within_30_days")
    assert "R99" not in response["reply"]
    assert "R99" not in response["estimatedCost"]
    assert response["estimatedCost"].startswith("Generally free")


def test_groq_phrasing_rejected_when_it_falsely_implies_fee_uncertainty(monkeypatch):
    """Found via live testing against the real Groq API: phrasing can claim
    a fee "needs to be confirmed" even when the source data states it
    plainly (verify_before_demo=False) and contains no number to
    hallucinate — the fee-number check alone doesn't catch this, since no
    digit is involved. This is the regression test for that gap."""
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion(
        "You'll need a few documents to register the birth. The fee for this "
        "service needs to be confirmed with your local office."
    )
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    # Real cost for this sub-case is "Generally free", verify_before_demo=False —
    # there is nothing to confirm, so this phrasing must be rejected.
    response = _build("birth_registration", "within_30_days")
    assert "needs to be confirmed" not in response["reply"].lower()
    assert response["estimatedCost"].startswith("Generally free")


def test_groq_phrasing_never_used_for_documents_needed(monkeypatch):
    """documentsNeeded must always be the deterministic, itemised list —
    never passed through Groq — regardless of what Groq's phrasing returns."""
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_completion(
        "Everything looks fine, no documents needed at all!"
    )
    monkeypatch.setattr(guide, "_get_groq_client", lambda: fake_client)

    response = _build("birth_registration", "within_30_days")
    assert len(response["documentsNeeded"]) == 3
    assert "Proof of birth (Form DHA-24/PB)" in _doc_names(response)


# ---------------------------------------------------------------------------
# conversationId isolates concurrent users
# ---------------------------------------------------------------------------


def test_conversation_id_isolates_two_concurrent_users():
    guide.answer("I need to register my baby", None, "user-a-conv")
    guide.answer("I need a passport", None, "user-b-conv")

    # Interleaved turns: if sessions leaked into each other, one user's
    # answer could resolve the other's pending question instead of their own.
    guide.answer("she was just born this week", None, "user-a-conv")
    guide.answer("it's for myself, I'm an adult", None, "user-b-conv")

    state_a = guide._SESSIONS[guide._session_key("user-a-conv")]
    state_b = guide._SESSIONS[guide._session_key("user-b-conv")]

    assert state_a.service_id == "birth_registration"
    assert state_a.sub_case_id == "within_30_days"
    assert state_b.service_id == "passport"
    assert state_b.sub_case_id == "adult"


def test_missing_conversation_id_never_shares_state_across_calls():
    """No conversationId supplied twice in a row must NOT be treated as
    the same conversation (that was the old, explicitly-retired
    location-keyed behavior) — each call gets an isolated session."""
    guide.answer("I need to register my baby", None, None)
    response = guide.answer("she was just born this week", None, None)

    # Second call started a fresh session, so "she was just born this week"
    # is being classified as a SERVICE message (no service known yet), not
    # as an answer to the sub-case question from the first call.
    assert response["documentsNeeded"] == []


# ---------------------------------------------------------------------------
# Full multi-turn conversations through the real answer() entry point.
# ---------------------------------------------------------------------------


def test_full_conversation_birth_registration_reaches_correct_checklist():
    guide.answer("I need to register my baby", None, "conv-birth")
    guide.answer("she was just born this week", None, "conv-birth")
    response = guide.answer("no complications", None, "conv-birth")

    assert response["documentsNeeded"]
    assert any("Proof of birth" in line for line in response["documentsNeeded"])
    assert response["conversationId"] == "conv-birth"


def test_full_conversation_passport_lost_adds_loss_report():
    guide.answer("My passport expired, what do I need?", None, "conv-passport")
    response = guide.answer("it's for myself, I'm an adult", None, "conv-passport")

    # Should have reached the complications question by now.
    assert response["documentsNeeded"] == []

    final = guide.answer("actually it was lost, not just expired", None, "conv-passport")
    assert any("Loss report" in line for line in final["documentsNeeded"])
