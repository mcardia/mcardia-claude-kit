---
description: "Generate high-value Mermaid behavior/relationship diagrams from a feature spec (never C4 structural views)."
disable-model-invocation: true
---

# Prompt to Generate Mermaid Diagrams from a Spec (Subagent / Command)

> This is a prompt that can run in Claude Code or any AI agent. It generates Mermaid behavior/relationship diagrams from an SDD spec, not from a legacy FDD.

## Lane: behavior only (one owner per diagram type)

This skill owns **behavior and relationships** — sequence, state, flowchart, class, ER. It **MUST NOT** emit **C4 structural views** (`C4Context`, `C4Container`, `C4Component`): structure is owned by the **`sdd-c4`** skill (C4 in PlantUML). Mermaid's C4 support is experimental and would duplicate — and inevitably drift from — the canonical C4 model. Structure has exactly one owner; this is not it.

## Naming authority (single source of truth)

If a C4 **platform naming registry** exists (default `architecture/diagrams/naming-registry.md`, overridable), it is the single source of truth for names. Name sequence **participants** and class/ER **entities** from its `alias`/`label` values **verbatim**, so behavioral diagrams never invent divergent names for things the C4 model already named.

## Input (read first)

The source of truth is the SDD spec set:

- **`specs/<feature>/spec.md`** — WHAT, flows, acceptance criteria.
- **`specs/<feature>/plan.md`** — HOW: components, contracts, data touchpoints.

For architectural context consult the cited **ADRs**; read the **naming registry** if present. Never invent elements absent from the spec/plan or its cited ADRs.

# Subagent

This skill ships a registered subagent, **`mermaid-diagram-generator`** (`model: opus`), defined in [`../../agents/mermaid-diagram-generator.md`](../../agents/mermaid-diagram-generator.md) — the single source of truth for its behavior (behavior-only lane, naming authority, significance filter, syntax guardrails, internal review).

When this skill runs inside Claude Code with the plugin installed, the command below invokes that registered agent directly (no fallback). To run this prompt in any other AI tool, open the agent file and paste its body (skip the YAML frontmatter).

# Command

```markdown
---
description: Generate Mermaid behavior diagrams from an SDD spec. Usage: /generate-mermaid <specs/feature/> [output-folder] [--registry=PATH]
---

Invoke the mermaid-diagram-generator subagent with the spec folder path.

Extract from arguments:
- Spec folder (required): `specs/<feature>/` containing spec.md and plan.md.
- Output folder (optional, default `specs/<feature>/diagrams`).
- `--registry` (optional, default `architecture/diagrams/naming-registry.md`): C4 naming registry to read for canonical names.

Pass:

"Generate Mermaid behavior/relationship diagrams from the SDD spec at [SPEC_FOLDER] (spec.md + plan.md; read cited ADRs for context, and the C4 naming registry at [REGISTRY] if present).
Output folder: [OUTPUT_FOLDER].
Stay in the behavior/relationship lane (sequence, state, flowchart, class, ER) — never emit C4 structural views. Execute the full workflow: detect language, extract explicit elements, apply the significance filter, select types, prune redundancy, and generate ONE self-contained Markdown file with all diagrams (typically 6-8, max 10). When the registry exists, name participants/entities from it verbatim. Never fabricate elements absent from the spec/plan/ADRs. Run the mandatory internal review. Report detected language, file path, diagram count and rationale, whether the registry was used, and validation results."
```
