# Verifi API

> **Security:** Verifi uses synthetic/demo data only. It does not connect to real Home Affairs records.

Base URL for local development: `http://localhost:8000`

Every error response — validation failure, unhandled exception, unknown route — uses the same shape:

```json
{ "error": true, "message": "..." }
```

---

## GET /health

Confirms the database seeded and which mode the identity-detection service is running in.

### Response

```json
{
  "status": "ok",
  "datasource": "sqlite",
  "seededFrom": "json",
  "recordCount": 5,
  "detection": "real"
}
```

`detection` is `"real"` when `backend/services/identity_checker.py` is bound, `"mock"` if it's unavailable and the API is serving fixed mock results instead.

---

## POST /api/check-identity

Checks a South African ID number against the Verifi synthetic demo dataset and returns any identity-integrity warning flags, in plain language.

### Request

```json
{ "idNumber": "9001015800083" }
```

`idNumber` must be exactly 13 digits (spaces/dashes are stripped automatically), with a real embedded date of birth and a valid Luhn checksum — the standard South African ID format. Five synthetic demo IDs are whitelisted past the Luhn check (see below) so they work even though they don't happen to pass it for real; this can be disabled with `ALLOW_DEMO_IDS=false`.

### Response — clean record

```json
{
  "found": true,
  "idNumber": "9001015800083",
  "flags": [
    {
      "type": "no_flags",
      "severity": "low",
      "title": "No Issues Found",
      "plainExplanation": "We didn't find any identity-integrity problems on your record. Your ID number, marital status, and status flags all look clean in our demo dataset.",
      "nextSteps": [
        "No action needed right now",
        "It's still good practice to check again periodically"
      ]
    }
  ],
  "cleanRecord": true
}
```

### Response — flag found

```json
{
  "found": true,
  "idNumber": "8505124800086",
  "flags": [
    {
      "type": "marital_status_mismatch",
      "severity": "high",
      "title": "Unexpected Marriage on Record",
      "plainExplanation": "Our records show you're listed as married, but this doesn't match what you told us. This can happen when someone fraudulently registers a marriage using your ID.",
      "nextSteps": [
        "Confirm your real marital status by SMSing 'M' + your ID number to 32551 (free)",
        "If the result is wrong, report it to SAPS and get a case number",
        "Call the DHA Fraud Unit on 0800 60 11 90 to open an investigation",
        "Submit a formal dispute at your nearest Home Affairs office"
      ]
    }
  ],
  "cleanRecord": false
}
```

### Response — ID not found

```json
{
  "found": false,
  "idNumber": "9905155800080",
  "flags": [],
  "cleanRecord": false,
  "message": "No record found for this ID number in our demo dataset."
}
```

### Response — invalid format (`400`)

```json
{ "error": true, "message": "Invalid ID number format" }
```

### Flag types and copy

Each flag carries a `title`, a `plainExplanation`, and a list of `nextSteps` — never a raw internal code on its own.

| `type` | `severity` | Meaning |
|---|---|---|
| `no_flags` | `low` | No identity-integrity issues found |
| `marital_status_mismatch` | `high` | An unexpected marriage is on record |
| `duplicate_id` | `medium` | The ID number appears more than once, linked to different details |
| `deceased_flag` | `high` | Record incorrectly shows the person as deceased |
| `blocked_id` | `high` | The ID number is flagged as blocked |

### Demo ID numbers

These 5 synthetic 13-digit IDs are seeded in the demo dataset (`data/synthetic/marriages.json`) and exercise each scenario:

| ID number | Scenario |
|---|---|
| `9001015800083` | Clean record |
| `8505124800086` | Fraudulent marriage (`marital_status_mismatch`) |
| `7712089800081` | Duplicate ID (`duplicate_id`) |
| `6003215800084` | Deceased flag (`deceased_flag`) |
| `9506306800082` | Blocked ID (`blocked_id`) |

Any other syntactically valid 13-digit ID not in the dataset returns the "ID not found" response above.

---

## POST /api/chat

"Home Affairs Explained" — a branching conversation across 4 Home Affairs services (birth registration, Smart ID, passport, name/surname amendment) that asks one question at a time and returns a document checklist grounded in `backend/data/home_affairs_reference.json` and `document_sources.json`. See the main [README](../README.md#how-it-works) for how the conversation flow and Groq integration work.

### Request

```json
{
  "message": "I need to register my baby's birth",
  "conversationId": "b3a1e6b2-4b3e-4f9a-9c1a-4e8f6b2a1d3e",
  "location": { "lat": -33.9249, "lng": 18.4241 }
}
```

- `message` — required, free text.
- `conversationId` — a UUID the frontend generates once per chat session and sends on every turn, so the backend can track which question it's mid-way through asking. If omitted, the call is treated as an isolated one-off (no multi-turn continuity, but never shares state with another caller).
- `location` — optional, currently unused by the response (see **Known Limitations** in the README — there's no branch-location data source yet).

### Response — mid-conversation (clarifying question)

```json
{
  "reply": "Is this within 30 days of the birth, or more than 30 days (late registration)?",
  "documentsNeeded": [],
  "estimatedCost": "",
  "estimatedTime": "",
  "nearestBranch": null,
  "conversationId": "b3a1e6b2-4b3e-4f9a-9c1a-4e8f6b2a1d3e"
}
```

### Response — final checklist

```json
{
  "reply": "Here's what you'll typically need for Birth registration — Registering within 30 days of birth: ...",
  "documentsNeeded": [
    "Proof of birth (Form DHA-24/PB) — from Hospital, clinic, or other health facility; ...",
    "Parents' IDs or passports — from The parents; original not required, certified copy acceptable; ..."
  ],
  "estimatedCost": "Generally free — The first birth registration and first birth certificate are generally free. ...",
  "estimatedTime": "Not specified in our reference material — confirm processing times with Home Affairs.",
  "nearestBranch": null,
  "conversationId": "b3a1e6b2-4b3e-4f9a-9c1a-4e8f6b2a1d3e"
}
```

`documentsNeeded` entries are always rendered deterministically from the reference data, whether or not Groq phrased the `reply` text — a document, issuer, or fee is never invented or altered by the LLM step. `estimatedCost` states a real figure when the reference data has one (always flagged for demo-day verification if tariffs can change), or an honest "not specified" note when it doesn't. `estimatedTime` and `nearestBranch` are always the same honest placeholders today — see **Known Limitations** in the README.

### Off-topic or unrecognized message

```json
{
  "reply": "I can help with 4 Home Affairs services: birth registration, Smart ID, passport, or a name/surname amendment. Which one do you need help with? I don't have information outside these four services.",
  "documentsNeeded": [],
  "estimatedCost": "",
  "estimatedTime": "",
  "nearestBranch": null,
  "conversationId": "b3a1e6b2-4b3e-4f9a-9c1a-4e8f6b2a1d3e"
}
```

---

## Test Coverage

66 tests across `tests/test_api.py`, `tests/test_identity_checker.py`, and `tests/test_home_affairs_guide.py` — validation, the mock/real detection-service adapter and its fallback, SQLite seeding, the chatbot's state machine and checklist fidelity (including a scan that no fee is ever stated without a verify-before-demo caution), and Groq classification/phrasing including their fallback paths, mocked so no test needs network access. Run with:

```bash
pytest tests/ -v
```

> All identifiers shown in this documentation are synthetic demo identifiers.
