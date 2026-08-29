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
| `/sdd-generators:c4` | C4 PlantUML diagrams | canonical C1+C2 and the naming registry at platform scope; C3 per feature |
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

## Registered agent

The plugin registers one subagent: **`docs-auditor`** — the single-lens, context-isolated
corpus auditor that `/sdd-generators:readiness-audit` spawns N ≥ 4 times in parallel, and
again as the fresh-eyes re-verifier. It is the authority on what each lens means. It pins
its model and reasoning effort in its definition, so audit spawns do not silently inherit
a lower session effort.

## What this plugin deliberately does not do

See the same section in the [repository README](../../README.md#what-sdd-generators-deliberately-does-not-do)
— every job listed there is left to a Claude Code built-in on purpose.
