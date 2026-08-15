"""Shared test fixtures.

Stubs home_affairs_guide's Groq client to "unavailable" for every test in
the whole suite by default, so nothing here ever makes a live network call
even though GROQ_API_KEY may be set in the local environment (e.g. via
.env for manual/live testing). Patched at the _get_groq_client() seam (not
_call_groq_json/_call_groq_text directly) so those functions' own real
error-handling code still runs, and so individual tests in
tests/test_home_affairs_guide.py can override just _get_groq_client with a
fake client to exercise the Groq-specific paths without fighting this
fixture.
"""

import pytest

from backend.services import home_affairs_guide


@pytest.fixture(autouse=True)
def _groq_unavailable_by_default(monkeypatch):
    monkeypatch.setattr(home_affairs_guide, "_get_groq_client", lambda: None)
    yield
