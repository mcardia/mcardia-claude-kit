---
max_turns: 45
timeout_seconds: 900
allowed_tools: [Skill, Write, Edit, Read, Glob, Grep, Bash]
runs: 3
---

/sdd-generators:doclint

First create this corpus and commit it, so the lint has tracked documents to scan:

- `git init`, then after writing the files `git add -A` and
  `git -c user.email=eval@example.invalid -c user.name=Eval commit -m corpus`.
- `AGENTS.md`: Ledger, a self-hosted expense tracker. Canonical module names are
  `ledger-api`, `ledger-web`, `ledger-import`. The project forbids MySQL outside
  exclusion phrasing. Stack: Go API, PostgreSQL, React web app.
- `docs/prd.md`: FR-001 import bank CSV; FR-002 categorise a transaction.
- `docs/adr/adr-001-datastore.md`: PostgreSQL as the primary datastore.
- `specs/csv-import/spec.md`: owns FR-001, lives in `ledger-import`, cites ADR-001.

Do not ask me anything — derive the configuration from the corpus above, state what you
derived, and proceed. Then author the lint and run it once against this corpus.
