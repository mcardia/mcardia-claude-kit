---
description: "Generate C4 PlantUML diagrams: platform scope (canonical C1+C2 from ADRs) or feature scope (C3 from a spec)."
disable-model-invocation: true
---

# Generator: C4 structural diagrams from an SDD corpus

Generate C4 structural diagrams in PlantUML from an SDD corpus.

Usage: `/sdd-generators:c4 [--scope=platform|feature] <source> [output-folder] [--registry=PATH] [--no-images]`

## Arguments (bind these first)

- `--scope` — `platform` or `feature`. Default `feature`.
- `<source>` (required) — for `platform`, the architecture sources: the ADRs folder plus
  the architecture overview (e.g. `AGENTS.md`). For `feature`, the spec folder
  `specs/<feature>/` containing spec.md and plan.md.
- `[output-folder]` — default `architecture/diagrams` for `platform`,
  `specs/<feature>/diagrams` for `feature`.
- `--registry=PATH` — the naming registry to write (`platform`) or read (`feature`).
  Default `architecture/diagrams/naming-registry.md`.
- `--no-images` — skip PNG generation.

Below, `[output]` means the resolved output folder and `[registry]` the resolved registry
path. `[name]` is the feature slug under `feature` scope and `platform` under `platform`
scope — every output file is named `[name]-c[N]`.

## Scope (decide first)

A run has exactly one **scope**. Take it from the arguments; default to `feature`.

- **`platform`** — author the canonical **C1 (System Context) + C2 (Container)** **once** for the whole project, from the project's **ADRs** and **architecture overview** (e.g. `AGENTS.md` or an architecture doc), **not** from any single feature spec. Also emit the **naming registry**. Output folder default `architecture/diagrams`; registry default `architecture/diagrams/naming-registry.md`.
- **`feature`** — author **C3 (Component)** for one feature from its `spec.md` + `plan.md`, reading the cited ADRs and the existing naming registry. **Skip C1/C2** when a platform model already exists; generate them only as a fallback when none is found. **C4 (Code)** only when code-level detail is present. Output folder default `specs/<feature>/diagrams`.

Generating C1/C2 per feature would produce N drifting copies of the same picture — the contradiction this corpus forbids. That is why C1/C2 live at platform scope and C3 reuses them.

## Naming authority (single source of truth)

The `platform` run writes the **naming registry**: the canonical list of system/container aliases → labels. Every later run reuses those aliases and labels **verbatim**, so an implementing agent is never handed two divergent names for the same thing.

## Language

- Detect the source's primary language; write the diagrams in that same language with correct accents.
- Keep technical and product names in English (Service, Container, Database, API, REST, Redis, etc.).

## Steps

### Scope: platform

1. Read the ADRs and the architecture overview. Do NOT base C1/C2 on a single feature spec.
2. Generate **C1 (System Context)** and **C2 (Container)** for the whole project.
3. Write the canonical **naming registry** (below) listing every system/container alias → label.
4. Call the Write tool for:
   - `[output]/[name]-c1.puml`
   - `[output]/[name]-c2.puml`
   - `[registry]` (the naming registry, Markdown — NO PlantUML code)

   If you do not Write the .puml files and the registry, the task failed.

### Scope: feature

1. Read spec.md and plan.md. Read the ADRs they cite. Read the **naming registry** if it exists.
2. Generate **C3 (Component)** whenever possible; generate **C4 (Code)** only if plan.md or cited contracts carry code-level detail.
3. **C1/C2**: skip them when a platform model (or registry) already exists — C3 must connect to the registry's containers by their canonical aliases. Generate C1/C2 here **only as a fallback** when no platform model is found, and say so in the report.
4. Reuse registry `alias`/`label` values **verbatim** for every system/container a C3 component talks to. Never coin a new alias for something already in the registry.
5. Call the Write tool for each generated level:
   - `[output]/[name]-c3.puml`
   - `[output]/[name]-c4.puml` (only if C4 generated)
   - `[output]/[name]-c4.md` (analysis only, NO PlantUML code)
   - fallback only (no platform model found): `[output]/[name]-c1.puml`, `[output]/[name]-c2.puml`

   If you generate a level but do not Write its .puml file, the task failed.

## Level sufficiency

- **C1 System Context** (platform): system purpose + external actors + external systems. From ADRs + architecture overview.
- **C2 Container** (platform): technology stack + deployment units + how they communicate. From ADRs (stack/topology) + architecture overview.
- **C3 Component** (feature): internal components, responsibilities, interfaces. From plan.md touchpoints; connect to registry containers by canonical alias.
- **C4 Code** (feature): interfaces, structs, signatures. Only if plan.md or cited contracts carry code-level detail.

## Naming registry (platform writes it; feature reads it)

A small machine- and human-readable Markdown file. One row per system/container the project exposes. Columns: `alias` (PlantUML identifier, ASCII, stable), `label` (display name, may carry accents), `kind` (`System` | `System_Ext` | `Container`), `technology` (containers only), `description` (one line). Example:

| alias | label | kind | technology | description |
|---|---|---|---|---|
| webapp | Web App | Container | TypeScript, React | Browser single-page app |
| api | API | Container | Go | REST backend |
| db | Database | Container | PostgreSQL | Primary datastore |
| idp | Identity Provider | System_Ext | — | External SSO |

Feature C3 runs MUST use these `alias` and `label` values verbatim. If a feature needs a container absent from the registry, add the row during a `platform` run rather than inventing a divergent name in a feature diagram.

## Quality rules

- UTF-8: every .puml second line is `!pragma charset UTF-8`.
- Titles: `title C[N] • [Level Name] - [Feature Name]` (feature scope) or `title C[N] • [Level Name] - [Project Name]` (platform scope).
- C1-C3 use `!include <C4/C4_Context|C4_Container|C4_Component>`; C4 uses plain PlantUML class diagrams (`@startuml`, `!pragma charset UTF-8`, `skinparam packageStyle rectangle`).
- Parameter order: `System_Ext($alias,$label,$descr)`; `Container/Component($alias,$label,$techn,$descr)`. Never put tech in the $descr slot.
- Notes: bullet points (•), 3-5 max, one line each. No spec/ADR section references inside diagram notes.
- Embedded libraries are part of the host, not separate System()/Container().
- Layout: C1 LAYOUT_LEFT_RIGHT(); C2 LAYOUT_TOP_DOWN(); C3 by complexity. SHOW_LEGEND() on C1-C3, not on C4.
- No emojis.

## No fabrication

- Every element traces to the active scope's sources: platform → ADRs / architecture overview; feature → spec.md / plan.md / cited ADRs / naming registry. Document any inference and its source.
- Items marked out of scope / non-goals never appear.

## Internal review (mandatory, silent)

After writing all files: re-read the sources and every .puml, list inconsistencies (missing elements, fabricated elements, wrong tech, wrong relationships, missing accents, wrong detail level, excluded items present), and fix each with the Edit tool. Do not document this review in the .md file.

## PNG generation (unless `--no-images`)

1. Check availability: `plantuml -version`. If absent, report it with install instructions (`apt-get install plantuml` or `brew install plantuml`) and continue without failing the task.
2. Render each generated level: `plantuml [output]/[name]-c[N].puml` (produces the matching .png).
3. On a syntax error, do not skip the diagram: read the error, fix the .puml with the Edit tool, and re-run, up to 3 attempts per file. Common causes: SHOW_LEGEND() in the C4 code level, unbalanced parentheses, invalid relationship syntax.
4. After 3 failed attempts on a file, log it and move on.

## Report

- Scope (platform | feature) and detected language.
- List of created files (.puml, and for `feature` the `[name]-c4.md` analysis; for `platform` the registry).
- For feature: whether C1/C2 were skipped (platform model found) or generated as a fallback.
- Skipped levels with reasons.
- "Created N .puml files for N diagrams."
- PNG results (if enabled): generated, and any failed after 3 attempts.
