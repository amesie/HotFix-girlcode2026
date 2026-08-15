# Security

Verifi is a hackathon demo running against synthetic data — it does not connect to real Home Affairs records, and this document is an honest account of what's actually implemented today versus what would be needed for a real deployment. If a pitch or a judging conversation claims more than what's listed here as "Implemented," the code doesn't back it up yet — please don't oversell it.

## Implemented

- **Synthetic data only.** Every ID number, name, and record in this repo is fabricated for the demo (`data/synthetic/marriages.json`). Verifi never connects to a real Home Affairs system.
- **ID numbers are never persisted.** `POST /api/check-identity` only reads (`SELECT`) against the seeded dataset — the ID a user submits is never written to any table.
- **ID numbers are masked in logs.** `backend/database/database.py`'s `mask_id()` reduces every logged ID to its first 6 and last 2 digits (e.g. `900101******83`) before it reaches a log line. The full ID is never written out in application logs.
- **One consistent, non-leaky error shape.** Every failure path — validation error, unhandled exception, unknown route — returns `{"error": true, "message": "..."}` via global FastAPI exception handlers. Stack traces and internal exception text are logged server-side only, never returned to the caller.
- **Grounded LLM use.** Where Groq is used (chatbot classification and phrasing — see the [README](../README.md#grounded-llm-use-not-free-generation)), it's constrained to an exact enum pulled from reference data, and its phrasing output is validated against that same data before use. It cannot fabricate a document, fee, or process detail.

## Not implemented (aspirational — do not claim these in a demo)

- **No encryption at rest.** `data/verifi.db` is a plain, unencrypted SQLite file on disk.
- **No enforced encryption in transit at the application layer.** TLS would need to be handled by whatever hosts this in production; nothing in this repo terminates or enforces it.
- **No authentication or authorization on any endpoint.** Every route is open to anyone who can reach it. CORS (`ALLOWED_ORIGINS`) restricts which *browser origins* a browser will let call the API by default — it is not an access-control mechanism, and any direct HTTP client (`curl`, a script, another server) can call every endpoint regardless of origin.
- **No PII redaction on chatbot messages.** `POST /api/chat`'s free-text `message` field is sent to Groq for classification/phrasing as-is. If a user types their ID number or other personal details into a chat message, it is not stripped before reaching the LLM API. (This is distinct from `/api/check-identity`, whose ID number never reaches an LLM at all — no AI call is made on that path.)
- **No formal data-retention policy or auto-delete mechanism.** The ID number happening to never be persisted (above) is a property of how the check-identity code is written today, not an enforced, documented retention policy.
- **No structured or persisted audit logging.** `logger.info`/`logger.warning` calls exist for operational visibility (masked ID, result summary, which detection/chat mode is active) but write to process stdout only — not a queryable audit trail, and not tied to any user identity, since there's no authentication to tie it to.
- **No threat detection or monitoring.** Rate limiting, anomaly detection, and intrusion monitoring are not implemented.
- **No deployment hardening.** There's no production CORS configuration, no WAF, no secrets manager — `GROQ_API_KEY` and friends are local `.env` values only, appropriate for local development, not a deployed environment.

## Reporting

This is a hackathon project with no production deployment. If you find something concerning while reviewing the code, please raise it with the team directly rather than filing a public report.
