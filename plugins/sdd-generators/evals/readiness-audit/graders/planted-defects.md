---
type: llm
focus: last_message
weight: 2
---

The audit reports BOTH planted defects: (1) `specs/csv-import/spec.md` names module
`ledger-importer`, contradicting the canonical modules `ledger-api` / `ledger-web`
declared in `AGENTS.md`; (2) `specs/categorise/spec.md` cites ADR-007, which does
not exist. Each finding names the file it came from. The verdict is NOT READY.
