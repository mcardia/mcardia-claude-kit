# sdd-generators

Interview-style generators that bootstrap the governance and design documents of a
**Spec-Driven Development (SDD)** project. Each generator runs a focused,
one-question-at-a-time interview and emits ready-to-use Markdown (and, on request, a
JSON twin with English keys).

They encode one core discipline — **one authority per fact**: every concrete fact is
*defined* in exactly one document; every other mention is a reference or a clearly
subordinate illustration.

## Commands

Each skill is invoked explicitly (it never auto-triggers). A typical project runs them
roughly in this order.

| Command | Produces | Role |
|---|---|---|
| `/sdd-generators:constitution` | `methodology.md` + `AGENTS.md` | method pillars, source-of-truth hierarchy, artifact taxonomy (the anti-drift core) |
| `/sdd-generators:prd` | a PRD | problem, goals + metrics, scope, behavior, non-functional targets |
| `/sdd-generators:adr` | one `adr-NNN.md` | a single architecture decision: context, options, decision, trade-offs |
| `/sdd-generators:spec` | `specs/<feature>/{spec,plan,tasks}.md` | per-feature WHAT → HOW → tasks |
| `/sdd-generators:research-briefing` | a research briefing | scopes an investigation that feeds candidate ADRs |
| `/sdd-generators:research-document` | a deep-research document | the evidence (not authority) that ADRs cite |
| `/sdd-generators:c4` | C4 PlantUML diagrams | architecture diagrams from a spec |
| `/sdd-generators:mermaid` | Mermaid diagrams | high-value diagrams from a spec |
| `/sdd-generators:traceability` | `docs/traceability.md` | requirement/criterion/target → owning spec/task; cross-feature criteria registry |
| `/sdd-generators:doclint` | `scripts/check-docs.sh` | project-tailored docs lint: dead references, stale markers, name drift, coverage, diagram integrity |
| `/sdd-generators:readiness-audit` | audit verdict + fix plan | multi-lens agent audit → cross-verified fix plan → fresh-eyes re-verification that declares READY |

Authority flows top-down: **ADRs > standards > reference docs > running system**. Specs
derive from ADRs and never override them. Deep-research is evidence that feeds
decisions; it is never an authority.

`/sdd-generators:spec` begins by **scanning the repository for existing documentation**
— PRD, ADRs, standards/methodology, reference and data-model docs, API/wire contracts,
C4/Mermaid diagrams, and sibling specs — then shows a short context map and confirms it
before the interview. It cites and references those authorities rather than restating
them, so you do not need to paste them in by hand.

## Using a generator

Invoke the command, answer the interview one question at a time, and the tool emits the
document(s) in the standard format — and, on request, a JSON twin with English keys.

Each generator is also a plain prompt: open its `skills/<name>/SKILL.md`, skip the YAML
frontmatter, and paste the body into any AI tool.

## Registered agents

The plugin registers six subagents usable directly (or by the skills that orchestrate
them): `c4-diagram-generator` and `mermaid-diagram-generator` (diagram authoring),
`docs-auditor` (lens-based corpus audits for `/sdd-generators:readiness-audit`),
`cascade-reviewer` and `cascade-validator` (stages 1 and 2 of the cascade code review;
the coordinating session is stage 3), and `sdd-executor` (one `tasks.md` task per spawn,
strict TDD, honoring the project's model-assignment standard). Each pins its model and
reasoning effort in its definition, so spawns do not silently inherit a lower session
effort.
