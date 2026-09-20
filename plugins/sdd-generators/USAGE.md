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
| `/sdd-generators:constitution` | `methodology.md` + `AGENTS.md` | method pillars, source-of-truth hierarchy, artifact taxonomy (the anti-drift core), and the optional operator-decision section |
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
- **At the end of a turn** that hands the operator a decision, or states a grade the
  constitution puts above its own line — the turn does not end without the record.

**Both read the rule out of the project's own constitution, and refuse nothing in a
project whose constitution has no operator-decision section.** They walk up from the
working directory looking for one — stopping below `$HOME`, because a `CLAUDE.md` in the
home directory is a person's standing instructions and not a project's constitution — and
finding none, they do nothing. That predicate is deliberate: a plugin's hooks load in
*every* project, and a gate that refused ordinary work in repositories which never
adopted the rule would be a gate people switch off. A project opts in by having the rule,
and by nothing else — no flag, no settings entry, no second file to drift.

**Where that section comes from.** `/sdd-generators:constitution` has an
operator-decisions stage that collects the whole rule — what counts as one, the gate, the
grade scale and the line, the categories reserved whatever the grade, the record's fields,
and where a record lands for each outcome — and an `AGENTS.md` template that renders it.
The stage is skippable, and the interview talks nobody out of skipping it: a project that
declines gets no section, `/sdd-generators:od` has no rule to apply, and both hooks stay
inert. A project whose constitution predates the stage runs that stage alone and adds the
section to the document it already has.

Inert is not free. Each hook is a `python3` process: **about 17 ms on every Bash call and
every turn end, in every project, adopted or not.** The Stop hook uses the
`last_assistant_message` the host supplies rather than re-reading the transcript, which on
a 35.4 MB transcript is 17 ms instead of 66 ms.

### Is this project gated, and by what?

```sh
python3 "$CLAUDE_PLUGIN_ROOT/hooks/check-od-record.py" --explain [DIR]
```

Prints the constitution the walk resolved, the grade vocabulary parsed out of it and the
threshold word, or says `INERT` and lists the filenames it looked for. It is the only way
to tell a project that is gated and quiet from one whose section heading the hooks do not
recognise, and the only way to see what the vocabulary parser actually read.

`hooks/test_hooks.py` ships inside the installed payload too. It never runs on its own; it
is there so that `python3 "$CLAUDE_PLUGIN_ROOT/hooks/test_hooks.py"` proves the *installed*
copy behaves, not only the one in this repository.

### What the hooks cannot see

They read a command string; they do not run a shell. Two classes of write are therefore
invisible to them, and no amount of pattern work closes either:

- **A wrapper that takes its own arguments** — `timeout 60 gh …`, `xargs gh …`,
  `bash -c "gh …"`. (`/usr/bin/gh` and `GH_TOKEN=x gh …` *are* handled: both are lexical.)
- **A body the shell expands** — `--body "$(cat record.md)"`, `--body "$VAR"`. The hook
  sees the literal `$(cat record.md)`.

The honest claim is not that the gate cannot be bypassed. It is that it makes the correct
path the cheap one and makes skipping it visible.

### Why this is in the plugin and not in the project

**What the plugin reads, and what it states.** The rule is the constitution's: what counts
as a decision, the grade words, the line those words are measured against, which
categories are the operator's at every grade, the record's fields, and where a record
lands. `/sdd-generators:od` reads them there every run, and the hooks *parse* the grade
words and the threshold out of that same section rather than carrying a copy — which is
why a project grading `trivial|small|large|sweeping` is gated in its own vocabulary and
never asked for another's. Where that parse fails, the hooks fall back to "a grade label
carries some value" and skip the threshold test entirely, rather than guessing.

Four things ARE the plugin's, and are named here so they are not mistaken for yours: the
adversarial panel; **two distinct `file:line` anchors** as the operational test that a
cause and a remedy were both verified; `grade: n/a` as the spelling for a record of a
decision taken elsewhere; and the **four-rung sizing ladder** the `od-lens` remedy lens
prices a fix against — used only where your constitution states no sizing policy of its
own, and reported as the plugin's whenever it is used. None of the four is in anybody's
constitution. They are how a text gate checks a sentence that is.

The cheaper options, named and refused, because this kit's discipline is to write them
down rather than to have weighed them privately:

1. **Accept it** — leave the rule as prose in each project's constitution. Refused by
   evidence: it was prose, in the constitution *and* in memory, and it still lost to a
   more specific competing instruction in the same context window.
2. **Make the case unreachable** — nothing to remove; the failure is in how a session
   routes a decision, not in a surface anyone touches.
3. **One thing in something that already exists** — there is no such thing here. The
   cheapest shape that could work would be a skill alone, and a skill is advice: the
   recorded failure is a session reading the rule and routing past it anyway. What closes
   that is a refusal at the boundary, and a refusal needs a hook, which needs a parser
   for the project's own vocabulary, which needs tests. Tier 3 does not reach the case.
4. **A new mechanism** — a skill, an agent, a workflow and two hooks, carrying this
   repository's first executable code and its own test suite. **This is the tier shipped,
   and it is tier 4.** It lands in *this* plugin rather than in a new one, because a
   second install, a second version to track and a second USAGE would buy nothing for a
   rule belonging to the discipline this plugin already serves. Sharing a version number
   does not make a new mechanism a small one.

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
  `pipeline()`, `parallel()`, resume) and the Agent tool for a single task. `od-gate` is
  the exception that proves it: not general execution, but one fixed adversarial shape
  the operator-decision rule needs on every use, saved so that running it costs one call.
- **Author Mermaid behavior diagrams** → Claude writes Mermaid from a spec unaided;
  Artifacts render it natively, and the built-in `artifact-diagramming` skill covers when a
  diagram earns its place.
- **Scope and run deep research** → the built-in `deep-research` skill.

TDD rules, review conventions and model assignments are *project* policy: they belong in
the `AGENTS.md` / `methodology.md` that `/sdd-generators:constitution` writes, not here.
