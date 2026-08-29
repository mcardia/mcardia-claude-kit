---
type: llm
focus: {source: file, path: scripts/check-docs.sh}
weight: 2
---

This is a runnable lint script that checks at least three things: repository paths
cited in documents that do not exist; canonical-name drift against the module names
`ledger-api`, `ledger-web` and `ledger-import`; and the forbidden term MySQL
appearing outside exclusion phrasing. It exits non-zero when a check fails.
