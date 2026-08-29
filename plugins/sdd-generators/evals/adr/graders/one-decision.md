---
type: llm
focus: {source: file, path: docs/adr/adr-001-datastore.md}
weight: 2
---

This ADR records exactly ONE decision — the primary datastore choice — and decides
nothing unrelated. It names the rejected options SQLite and MySQL with a reason for
each rejection, and records the accepted trade-off (heavier local dev setup than
SQLite) as a consequence rather than omitting it.
