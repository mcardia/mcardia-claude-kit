---
max_turns: 45
timeout_seconds: 1200
allowed_tools: [Agent, Write, Edit, Read, Glob, Grep]
runs: 3
---

Create these two files, then use the `docs-auditor` subagent with the
**consistency** lens to audit them. Report its findings verbatim.
- `AGENTS.md`: "Ledger. Canonical modules: `ledger-api`, `ledger-web`.
  Source-of-truth hierarchy: ADRs > standards > specs."
- `specs/csv-import/spec.md`: "CSV import for Ledger. Implemented in module
  `ledger-importer`. Backed by ADR-007."
