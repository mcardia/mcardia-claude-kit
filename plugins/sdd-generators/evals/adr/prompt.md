---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Write, Read, Glob, Grep]
runs: 3
---

/sdd-generators:adr
Record the decision to use PostgreSQL as Ledger's primary datastore, over SQLite
and MySQL. Drivers: the team already runs Postgres, and we need row-level security
for per-team isolation. Accepted trade-off: heavier local dev setup than SQLite.
Answer every interview question yourself from this context; do not ask me anything.
Write the ADR to `docs/adr/adr-001-datastore.md`.
