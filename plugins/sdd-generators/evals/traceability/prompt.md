---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Write, Read, Glob, Grep]
runs: 3
---

/sdd-generators:traceability

Project context — answer every interview question yourself from it and write the
files without asking me anything:

- Product: "Ledger", a self-hosted expense tracker for small teams.
- Stack decided: Go API, PostgreSQL, React web app, SSO via an external IdP.
- Requirements: FR-001 import bank CSV; FR-002 categorise a transaction;
  FR-003 export a monthly report.
- Non-functional target: p95 API latency under 200 ms.
- Out of scope for now: mobile app, multi-currency.

The repository has specs for FR-001 (`specs/csv-import/`) and FR-002
(`specs/categorise/`). Nothing owns FR-003 yet. Write `docs/traceability.md`.
