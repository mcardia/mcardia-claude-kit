---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Write, Edit, Read, Glob, Grep]
runs: 3
---

/sdd-generators:traceability

First create this corpus exactly as described, then build the matrix from it:

- `docs/prd.md`: Ledger, a self-hosted expense tracker. FR-001 import bank CSV;
  FR-002 categorise a transaction; FR-003 export a monthly report. Non-functional
  target: p95 API latency under 200 ms.
- `specs/csv-import/spec.md`: owns FR-001.
- `specs/categorise/spec.md`: owns FR-002.

Nothing owns FR-003. Write the matrix to `docs/traceability.md`.
