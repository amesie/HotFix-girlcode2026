# Verifi

> Plain-language identity-fraud detection and Home Affairs guidance for South Africans.
> Built on **FastAPI + SQLite** (backend) and **React + Vite** (frontend).
> Developed for the **GirlCode Hackathon 2026**.

---

### Team Name: Hot Fix

**Team Members:**
- Amy Felix
- Thiana Moodley
- Nyiko Shipalana
- Inathi Koli

---

## Overview

Verifi helps South Africans deal with Home Affairs through two features.

**Identity Checker** — a user enters their SA ID number and Verifi returns plain-language flags for identity-integrity problems on record: a fraudulent marriage, a duplicate ID, a deceased flag, or a blocked ID. Each flag comes with a clear explanation of what it means and concrete next steps to resolve it, not just a raw status code.

**Home Affairs Explained** — a branching conversation for 4 common Home Affairs processes (birth registration, Smart ID, passport, name/surname amendment). It asks one question at a time — application type, applicant status, then any complications — and returns a document checklist assembled entirely from a structured reference dataset, not invented on the fly. Classification and phrasing are LLM-backed (Groq) when configured, with an automatic, tested fallback to deterministic keyword matching and templated text when it isn't.

Both features are demo-only and run entirely against a synthetic dataset — Verifi does not connect to real Home Affairs records.

---

## Problem Statement

Identity-related errors and fraud at Home Affairs are not abstract inconveniences — they can lock people out of everyday life. A marriage fraudulently registered against someone's ID can affect their legal and financial standing without them knowing until it surfaces somewhere unexpected. A duplicate ID number linked to someone else's details is a common sign of identity theft. An incorrect deceased flag can cut a living person off from banking and social grants. A blocked ID number can silently prevent someone from accessing services that rely on ID verification.

On top of that, Home Affairs processes themselves — what documents are needed, what something costs, how long it takes, where to go — are not always easy to find in plain language when someone needs them.

Verifi addresses both halves of this: surfacing identity-integrity problems in language a non-expert can act on, and answering common Home Affairs process questions directly.

---

## Our Solution

| Feature | Description |
|---|---|
| **Identity Checker** | Enter an SA ID number and get plain-language flags for known identity-integrity issues, each with a severity level and concrete next steps |
| **Home Affairs Explained** | A branching conversation across 4 Home Affairs services that asks one question at a time, then returns a document checklist and estimated cost grounded in structured reference data (LLM-backed via Groq when configured, keyword-matched otherwise) |

---

## How It Works

**Identity Checker:**

1. The ID number is cleaned (whitespace/dashes stripped) and validated: exactly 13 digits, a valid embedded date, and a Luhn checksum.
2. The validated ID is looked up against the synthetic demo dataset.
3. If found, the detection logic checks it against known issue types (fraudulent marriage, duplicate ID, deceased flag, blocked ID).
4. Any issues found are translated into plain-language flags — a title, an explanation, a severity, and next steps — rather than raw internal codes.

**Home Affairs Explained:**

1. The user's message is classified against one of the 4 supported services — via Groq if `GROQ_API_KEY` is configured, or a deterministic keyword matcher otherwise. An off-topic or unrecognized message gets an honest "I don't have information on that," never a guess.
2. The conversation then asks the remaining branching questions (application type, applicant status, then any complications) one at a time rather than all at once, tracking what's already known via a `conversationId` the frontend generates once per chat session and sends on every turn.
3. Once enough is known, a checklist is assembled entirely from `backend/data/home_affairs_reference.json` and `document_sources.json` — every document, issuer, and fee traces back to that reference data. If Groq is configured, it rephrases the checklist conversationally, but only after its output is validated against the same data (e.g. it can't state a fee figure that isn't in the source, or claim a plainly-stated fee "needs confirming"); anything that fails validation falls back to a deterministic template instead.
4. The response includes the documents needed and an estimated cost (or an honest "not specified — confirm with Home Affairs" where the source material doesn't give one). Estimated processing time and a nearest-branch lookup aren't backed by real data yet, so those are returned honestly empty rather than guessed — see **Known Limitations** below.

---

## Tech Stack

### Frontend

* React 19
* TypeScript
* Vite
* Tailwind CSS v4

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* SQLite (stdlib `sqlite3`, no ORM)
* [Groq](https://groq.com/) — optional LLM backend for the chatbot's classification and phrasing; the app runs fully without it

---

## Repository Structure

```text
Verifi/
├── backend/
│   ├── main.py                           # FastAPI app, CORS, exception handlers, /health
│   ├── api/
│   │   └── routes.py                     # /api/check-identity, /api/chat, validation, adapter
│   ├── data/
│   │   ├── home_affairs_reference.json   # Decision tree: 4 services × sub-cases × complications
│   │   └── document_sources.json         # Shared affidavit / certified-copy / court-order lookups
│   ├── database/
│   │   └── database.py                   # SQLite access layer, seeding from marriages.json
│   ├── models/
│   │   └── schemas.py                    # Placeholder — currently empty and not imported anywhere
│   └── services/
│       ├── identity_checker.py           # Identity fraud detection logic
│       └── home_affairs_guide.py         # Home Affairs Explained: state machine + Groq/keyword classification
│
├── frontend/
│   └── src/
│       ├── App.tsx, main.tsx
│       ├── api/
│       │   └── client.ts                 # Typed API client
│       └── screens/
│           ├── LoginScreen.tsx
│           ├── DashboardScreen.tsx
│           ├── ResultsScreen.tsx         # Identity Checker results
│           └── ChatbotScreen.tsx         # Home Affairs Explained
│
├── data/
│   └── synthetic/
│       └── marriages.json                # Synthetic demo dataset (source of truth)
│
├── docs/
│   ├── API.md
│   ├── PROBLEM.md                        # Placeholder — not yet written
│   └── SECURITY.md                       # Placeholder — not yet written
│
└── tests/
    ├── conftest.py                       # Shared fixtures — stubs Groq for the whole suite by default
    ├── test_api.py                       # API layer tests
    ├── test_identity_checker.py          # Detection logic tests
    └── test_home_affairs_guide.py        # Chatbot state-machine, classification, and phrasing tests
```

---

## Installation & Setup

### Prerequisites

- **Python 3.10+**
- **Node 18+** (Node 22+ recommended, matching the `@types/node` version the frontend is built against)
- **git**

### Clone the repo

```bash
git clone https://github.com/amesie/Verifi.git
cd Verifi
```

### Backend

From the repo root, optionally in a virtual environment (`python -m venv .venv && source .venv/bin/activate`, or `.venv\Scripts\activate` on Windows):

```bash
pip install -r requirements.txt
cp .env.example .env
```

Then set in `.env`:

| Variable | Purpose |
|---|---|
| `ALLOWED_ORIGINS` | Comma-separated extra CORS origins, beyond the built-in defaults (`localhost:3000`, `localhost:5173`, `127.0.0.1:5173`, `127.0.0.1:3000`). Leave blank for local dev. |
| `ALLOW_DEMO_IDS` | `true` (default) lets the 5 synthetic demo ID numbers bypass the Luhn checksum for the Identity Checker demo. Set `false` to enforce it strictly on every ID. |
| `GROQ_API_KEY` | Enables Groq-backed classification/phrasing for the chatbot. Leave blank and the chatbot still works end-to-end — it runs on the deterministic keyword classifier and templated phrasing instead. |

Start the server:

```bash
python -m uvicorn backend.main:app --reload
```

Runs on `http://localhost:8000`. Confirm with `curl http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and talks to the backend at `http://localhost:8000` by default — set `VITE_API_BASE_URL` in `frontend/.env` to point elsewhere.

### Tests

```bash
pytest tests/ -v
```

66 tests, none of which need a live Groq API key or network access — `tests/conftest.py` stubs Groq to "unavailable" for the whole suite by default, so classification/phrasing tests exercise the deterministic fallback unless a specific test opts into mocking a Groq response.

---

## Key Design Decisions

### Mock-Data-First Development

The API layer (validation, database, response contract) was built and fully tested — including all demo scenarios — against a fixed set of mock detection results before the real detection logic existed. This let the two backend workstreams (API layer and detection logic) proceed in parallel without either side blocking on the other.

### SQLite as a Derived Cache, Not a Source of Truth

`data/synthetic/marriages.json` is the source of truth for demo data. SQLite is rebuilt from it on every startup and is never written back to. This keeps the datastore disposable — delete the `.db` file and restart, and it rebuilds identically — while still giving the API a proper query interface instead of re-parsing JSON on every request.

### Resilient Service Binding

The API layer binds to both the identity-detection service and the Home Affairs guidance service dynamically by function name at startup, rather than assuming either already exists. If a module isn't available yet, is mid-development, or — for the chatbot — Groq isn't configured, the API falls back automatically (mock detection data, or the deterministic keyword classifier/templated phrasing) and logs which mode it's running in, so the frontend is never blocked on backend integration timing.

### Grounded LLM Use, Not Free Generation

Where Groq is used — chatbot classification and phrasing — it never has open-ended latitude. Classification is constrained to the exact set of service/sub-case/complication ids defined in `home_affairs_reference.json` at call time; any output outside that set is treated as unclear and rejected, not used. Phrasing takes the exact checklist data already assembled from the reference files and is only asked to rephrase it conversationally — its output is validated afterward (it can't state a fee figure absent from the source data, or claim a plainly-stated fee "needs confirming") before being used, falling back to a deterministic template otherwise. Every Groq call has a non-LLM fallback if the API is unavailable, slow, or returns something that fails validation, and the fallback is exercised by tests, not just assumed to work.

### One Consistent Error Shape

Every failure path — bad input, an unhandled exception, an unknown route — returns the same `{"error": true, "message": ...}` shape, registered globally rather than left to each endpoint to implement individually. ID numbers are masked in every log line, never written out in full.

---

## Known Limitations

- **No authentication** on any backend endpoint — this is a synthetic-data demo, not a production identity system.
- **Nearest-branch lookup isn't implemented.** The chatbot's `nearestBranch` field is always `null` — there's no real branch-location data behind it yet.
- **Estimated processing time isn't available.** The chatbot's `estimatedTime` field always says "not specified" — the source reference material has no timing data for any of the 4 services, so it says so honestly rather than inventing a number.
- **Chatbot session state is in-memory only**, keyed by a `conversationId` the frontend generates per chat session. It's lost on backend restart and isn't shared across multiple backend instances — fine for a single-demo-machine hackathon setup, not a real multi-instance deployment.
- **No deployment configuration yet** — no Vercel/Render config, no production CORS setup. This repo runs locally only for now.

---

## AI-Tool Disclosure

Portions of this codebase were developed with AI assistance under direct human direction and review.

The frontend began as wireframes in Figma, which were then turned into a working React application with Claude. The backend API layer, the identity-checker integration fixes, and the Home Affairs Explained chatbot (including its reference dataset, built from a provided source document, and its Groq integration) were built with Claude Code, working from written specifications and verified at each step with an automated test suite (`pytest`, 66 tests) and live manual testing of every endpoint — not just written, but run and checked.

Separately from development tooling, the **product itself** optionally calls an LLM at runtime: the Home Affairs Explained chatbot uses Groq for message classification and reply phrasing when `GROQ_API_KEY` is configured, constrained as described under **Grounded LLM Use, Not Free Generation** above. Without a key set, the chatbot runs on deterministic logic only.

---

## Built With

* [FastAPI](https://fastapi.tiangolo.com/)
* [Uvicorn](https://www.uvicorn.org/)
* [React](https://react.dev/) + [Vite](https://vitejs.dev/)
* [Tailwind CSS](https://tailwindcss.com/)
* [Groq](https://groq.com/)
* [Figma](https://figma.com/)
* [Claude](https://claude.com/) / [Claude Code](https://claude.com/claude-code)

---

<p align="center">
  <strong>Verifi</strong><br>
  GirlCode Hackathon 2026<br>
  Team Hot Fix
</p>
