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

**Home Affairs Explained** — a chatbot that answers practical questions like "I need to register my baby" with the documents needed, the cost, the expected time, and the nearest branch.

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
| **Home Affairs Explained** | Ask a question about a Home Affairs process and get the documents needed, estimated cost, estimated time, and nearest branch |

---

## How It Works

**Identity Checker:**

1. The ID number is cleaned (whitespace/dashes stripped) and validated: exactly 13 digits, a valid embedded date, and a Luhn checksum.
2. The validated ID is looked up against the synthetic demo dataset.
3. If found, the detection logic checks it against known issue types (fraudulent marriage, duplicate ID, deceased flag, blocked ID).
4. Any issues found are translated into plain-language flags — a title, an explanation, a severity, and next steps — rather than raw internal codes.

**Home Affairs Explained:**

1. The user asks a question in plain language (e.g. "I need to register my baby's birth").
2. The relevant process is matched from the Home Affairs guidance data.
3. The response returns the documents needed, estimated cost, estimated time, and (if location is shared) the nearest branch.

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

---

## Repository Structure

```text
Verifi/
├── backend/
│   ├── main.py                       # FastAPI app, CORS, exception handlers, /health
│   ├── api/
│   │   └── routes.py                 # /api/check-identity, /api/chat, validation, adapter
│   ├── database/
│   │   └── database.py               # SQLite access layer, seeding from marriages.json
│   ├── models/
│   │   └── schemas.py                # Shared Pydantic models
│   └── services/
│       ├── identity_checker.py       # Identity fraud detection logic
│       └── home_affairs_guide.py     # Home Affairs Explained chatbot logic
│
├── frontend/
│   └── src/
│       ├── App.tsx, main.tsx
│       ├── api/
│       │   └── client.ts             # Typed API client
│       └── screens/
│           ├── LoginScreen.tsx
│           ├── DashboardScreen.tsx
│           ├── ResultsScreen.tsx     # Identity Checker results
│           └── ChatbotScreen.tsx     # Home Affairs Explained
│
├── data/
│   └── synthetic/
│       └── marriages.json            # Synthetic demo dataset (source of truth)
│
├── docs/
│   ├── API.md
│   ├── PROBLEM.md
│   └── SECURITY.md
│
└── tests/
    ├── test_api.py                   # API layer tests
    └── test_identity_checker.py      # Detection logic tests
```

---

## Key Design Decisions

### Mock-Data-First Development

The API layer (validation, database, response contract) was built and fully tested — including all demo scenarios — against a fixed set of mock detection results before the real detection logic existed. This let the two backend workstreams (API layer and detection logic) proceed in parallel without either side blocking on the other.

### SQLite as a Derived Cache, Not a Source of Truth

`data/synthetic/marriages.json` is the source of truth for demo data. SQLite is rebuilt from it on every startup and is never written back to. This keeps the datastore disposable — delete the `.db` file and restart, and it rebuilds identically — while still giving the API a proper query interface instead of re-parsing JSON on every request.

### Resilient Service Binding

The API layer binds to the detection service dynamically by function name at startup, rather than assuming it already exists. If the detection module isn't available yet, or is mid-development, the API falls back to mock data automatically and logs which mode it's running in — so the frontend is never blocked on backend integration timing.

### One Consistent Error Shape

Every failure path — bad input, an unhandled exception, an unknown route — returns the same `{"error": true, "message": ...}` shape, registered globally rather than left to each endpoint to implement individually. ID numbers are masked in every log line, never written out in full.

---

## AI-Tool Disclosure

Portions of this codebase were developed with AI assistance under direct human direction and review.

The frontend began as wireframes in Figma, which were then turned into a working React application with Claude. The backend API layer was built with Claude Code, working directly from a detailed written specification, and verified at each step with an automated test suite (`pytest`) and live manual testing of every endpoint — not just written, but run and checked.

---

## Built With

* [FastAPI](https://fastapi.tiangolo.com/)
* [Uvicorn](https://www.uvicorn.org/)
* [React](https://react.dev/) + [Vite](https://vitejs.dev/)
* [Tailwind CSS](https://tailwindcss.com/)
* [Figma](https://figma.com/)
* [Claude](https://claude.com/) / [Claude Code](https://claude.com/claude-code)

---

## Coming Soon

A couple of sections are intentionally left out of this README for now, to be added once they're finalized:

- **Installation & Setup** — step-by-step setup instructions for both the backend and frontend, including copying `.env.example` to `.env` and setting `ALLOWED_ORIGINS` and `ALLOW_DEMO_IDS`
- **Known Limitations** — an honest rundown of current rough edges

---

<p align="center">
  <strong>Verifi</strong><br>
  GirlCode Hackathon 2026<br>
  Team Hot Fix
</p>
