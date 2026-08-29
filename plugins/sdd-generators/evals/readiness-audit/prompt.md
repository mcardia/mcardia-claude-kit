---
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Skill, Agent, Write, Edit, Read, Glob, Grep]
runs: 3
---

/sdd-generators:readiness-audit
First create the corpus below exactly as described, then audit it.
- `AGENTS.md`: Ledger; source-of-truth hierarchy ADRs > standards > specs.
  Canonical modules: `ledger-api`, `ledger-web`.
- `docs/prd.md`: FR-001 import bank CSV; FR-002 categorise a transaction.
- `specs/csv-import/spec.md`: owns FR-001; says it lives in module `ledger-importer`.
- `specs/categorise/spec.md`: owns FR-002; cites ADR-007, which does not exist.
Report the audit findings. Do not fix anything.
