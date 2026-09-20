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
| `/sdd-generators:od` | an operator-decision record | applies the project's operator-decision rule: verify cause and remedy at source → adversarial panel → grade → execute it or hand it over, as one fixed record either way |

Authority flows top-down: **ADRs > standards > reference docs > running system**. Specs
derive from ADRs and never override them.

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

The plugin registers two subagents. Each is the authority on what its own lenses mean —
the skills name a lens and never restate it, so there is one definition to keep true.
Each pins its effort in its definition; neither pins a model, because what a fleet of
agents costs is the operator's call, not the plugin's.

- **`docs-auditor`** — the single-lens, context-isolated corpus auditor that
  `/sdd-generators:readiness-audit` spawns N ≥ 4 times in parallel, and again as the
  fresh-eyes re-verifier.
- **`od-lens`** — the adversarial examiner behind `/sdd-generators:od`: the cause, remedy
  and ownership lenses, the synthesis role that writes the record, and the critic role
  that reads a whole set of records at once.

## Registered workflow

**`od-gate`** (`/sdd-generators:od-gate`) runs the operator-decision panel: three lenses
per finding, a synthesiser, then one critic across the set — `4N + 1` agents. It is saved
as a workflow rather than re-authored per use because the cheapest path has to be the
correct one, or it loses to the shortcut. `/sdd-generators:od` invokes it; you can also
run it directly on a list of issue numbers.

## Registered hooks

Two, and they are why the operator-decision rule binds instead of advising:

- **On a tracker write** that files a defect, claims the operator owns something, or
  already carries a grade — the write is refused unless it carries a grade, two
  `file:line` anchors (cause and remedy are two places), and the panel it went through.
- **At the end of a turn** that hands the operator a decision, or states a grade above
  the line the constitution draws — the turn does not end without the record.

**Both are inert unless the project's own constitution carries an operator-decision
section.** They walk up from the working directory looking for one; finding none, they do
nothing. That predicate is deliberate: a plugin's hooks load in *every* project, and a
gate that refused ordinary work in repositories which never adopted the rule would be a
gate people switch off. A project opts in by having the rule, and by nothing else — no
flag, no settings entry, no second file to drift.

### Why this is in the plugin and not in the project

The section below says project policy belongs in the constitution, not here, and that
still holds: **the plugin ships no rule.** What the constitution states — what counts as
a decision, the grade words, which categories are the operator's, the record's fields —
stays the project's, and `/sdd-generators:od` reads it there every run. What ships here
is only the procedure that applies whatever the constitution says, and the enforcement
that makes skipping it visible. That split is the same one everywhere in this kit: one
authority per fact, and the mechanism somewhere it cannot drift from.

The cheaper options, named and refused, because this kit's discipline is to write them
down rather than to have weighed them privately:

1. **Accept it** — leave the rule as prose in each project's constitution. Refused by
   evidence: it was prose, in the constitution *and* in memory, and it still lost to a
   more specific competing instruction in the same context window.
2. **Make the case unreachable** — nothing to remove; the failure is in how a session
   routes a decision, not in a surface anyone touches.
3. **One thing in something that already exists** — a skill, an agent, a workflow and two
   hooks added to *this* plugin, which is already installed, already carries governance
   skills that generate nothing (`readiness-audit`, `doclint`, `traceability`), and
   updates by a version bump. **This is the tier shipped.**
4. **A new plugin** — a second install, a second version to track, a second USAGE, for a
   rule belonging to the same discipline this plugin already serves. Rejected as tier 3
   reaches it.

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
