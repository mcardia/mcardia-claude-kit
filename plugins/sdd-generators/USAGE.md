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
its model and effort in its definition, so an audit spawn runs at the pinned setting
rather than inheriting whatever the calling session happens to use.

## What this plugin deliberately does not do

Every component costs context tokens in **every** session, whether or not it fires, so a
component only survives here when Claude Code ships nothing that does its job. These jobs
were removed on purpose — use the built-in instead:

- **Review a diff before it merges** → `/code-review` (`low`…`max`), or `/code-review ultra`
  for a multi-agent cloud review of a branch or PR. **Security review** → `/security-review`.
- **Validate a review's findings against the design corpus** (ADRs, standards, specs) → no
  built-in does this. It is project policy, so it belongs in the consuming project's own
  `.claude/agents/`, not in a cross-project plugin.
- **Execute tasks as orchestrated multi-agent work** → the Workflow tool (phases,
  `pipeline()`, `parallel()`, resume) and the Agent tool for a single task.
- **Author Mermaid behavior diagrams** → Claude writes Mermaid from a spec unaided;
  Artifacts render it natively, and the built-in `artifact-diagramming` skill covers when a
  diagram earns its place.
- **Scope and run deep research** → the built-in `deep-research` skill.

TDD rules, review conventions and model assignments are *project* policy: they belong in
the `AGENTS.md` / `methodology.md` that `/sdd-generators:constitution` writes, not here.
