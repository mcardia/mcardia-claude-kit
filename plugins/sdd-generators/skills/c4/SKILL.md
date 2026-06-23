---
description: "Generate C4 PlantUML diagrams: platform scope (canonical C1+C2 from ADRs) or feature scope (C3 from a spec)."
disable-model-invocation: true
---

# Prompt to Generate C4 Diagrams from an SDD Corpus (Subagent / Command)

> This is a prompt that can run in Claude Code or any AI agent. It generates C4 structural diagrams in PlantUML from an SDD corpus, not from a legacy FDD.

## Scope (decide first)

A run has exactly one **scope**. Take it from the task prompt; default to `feature`.

- **`platform`** — author the canonical **C1 (System Context) + C2 (Container)** **once** for the whole project. Source them from the project's **ADRs** and **architecture overview** (e.g. `AGENTS.md` or an architecture doc), **not** from any single feature spec. Also emit the **naming registry** (below). Output to the platform diagrams folder (default `docs/c4/platform`, overridable).
- **`feature`** — author **C3 (Component)** for one feature from its `spec.md` + `plan.md`. By default **skip C1/C2** when a platform model already exists; generate them only as a fallback when no platform model is found. **C4 (Code)** only when code-level detail is present. Output to the feature diagrams folder (default `docs/c4`, overridable).

Generating C1/C2 per feature would produce N drifting copies of the same picture — the contradiction this corpus forbids. That is why C1/C2 live at platform scope and C3 reuses them.

## One owner per diagram type (no overlap)

- **Structure** (C1/C2/C3/C4) → **this skill** (C4 in PlantUML).
- **Behavior / relationships** (sequence, state, flowchart, class, ER) → the **`sdd-mermaid`** skill.

This skill never emits behavioral diagrams; `sdd-mermaid` never emits C4 structural views.

## Naming authority (single source of truth)

The `platform` run writes a **naming registry**: the canonical list of system/container aliases → labels (with kind, technology, description). Every later run — `feature` C3 here, and all `sdd-mermaid` participants/entities — **reuses those aliases and labels verbatim**, so an implementing AI agent is never handed two divergent names for the same thing. Default registry path: `docs/c4/platform/naming-registry.md` (overridable).

## Input (read first)

By scope:

- **platform**: the project's **ADRs** and **architecture overview** (`AGENTS.md` or an architecture doc). Never base C1/C2 on a single feature spec.
- **feature**: the SDD spec set —
  - **`specs/<feature>/spec.md`** — WHAT and acceptance criteria.
  - **`specs/<feature>/plan.md`** — HOW: components, files, contracts.
  - the cited **ADRs** for architectural context, and the existing **naming registry** if present.

Never invent elements that are not present in the sources for the active scope.

# Subagent

This skill ships a registered subagent, **`c4-diagram-generator`** (`model: opus`), defined in [`../../agents/c4-diagram-generator.md`](../../agents/c4-diagram-generator.md) — the single source of truth for its behavior (scope handling, naming registry, level sufficiency, quality rules, internal review, optional PNG rendering).

When this skill runs inside Claude Code with the plugin installed, the command below invokes that registered agent directly (no fallback). To run this prompt in any other AI tool, open the agent file and paste its body (skip the YAML frontmatter).

# Command

```markdown
---
description: Generate C4 diagrams from an SDD corpus. Usage: /generate-c4 [--scope=platform|feature] <source> [output-folder] [--registry=PATH] [--no-images]
---

Invoke the c4-diagram-generator subagent.

Extract from arguments:
- `--scope` (optional, default `feature`): `platform` or `feature`.
- Source (required):
  - platform: the architecture sources — ADRs folder + architecture overview (e.g. `AGENTS.md`).
  - feature: the spec folder `specs/<feature>/` containing spec.md and plan.md.
- Output folder (optional): default `docs/c4/platform` for platform, `docs/c4` for feature.
- `--registry` (optional, default `docs/c4/platform/naming-registry.md`): naming-registry path to write (platform) or read (feature).
- `--no-images` (optional): skip PNG generation.

Pass (platform):

"Generate platform-scope C4 from the project architecture sources [SOURCES] (ADRs + architecture overview; NOT a feature spec).
Output folder: [OUTPUT_FOLDER]. Registry path: [REGISTRY].
PNG: [ENABLED|DISABLED].
Author the canonical C1 + C2 once for the whole project and write the naming registry. Never fabricate elements absent from the ADRs/architecture overview. Report scope, detected language, files created, and the count."

Pass (feature):

"Generate feature-scope C4 from the SDD spec at [SPEC_FOLDER] (spec.md + plan.md; read cited ADRs and the naming registry at [REGISTRY]).
Output folder: [OUTPUT_FOLDER].
PNG: [ENABLED|DISABLED].
Author C3 (and C4 only if code-level detail exists). Skip C1/C2 when a platform model exists; generate them only as a fallback if none is found. Reuse registry aliases/labels verbatim. Never fabricate elements absent from the spec/plan/ADRs. Report scope, detected language, files created, whether C1/C2 were skipped, skipped levels with reasons, and the count."
```
