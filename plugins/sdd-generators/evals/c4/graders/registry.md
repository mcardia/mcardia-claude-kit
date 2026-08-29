---
type: llm
focus: {source: file, path: architecture/diagrams/naming-registry.md}
weight: 4
---

This is a naming registry: a table whose rows each give an alias, a display label,
a kind (System, System_Ext or Container) and, for containers, a technology. It
covers the Go API, the PostgreSQL datastore, the React web app, and the external
identity provider as a System_Ext. The aliases are stable ASCII identifiers usable
verbatim in PlantUML.
