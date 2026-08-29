# mcardia-claude-kit

A personal **Claude Code marketplace** of design and architecture tooling. It ships two
plugins:

- **`sdd-generators`** — interview-style generators that bootstrap the governance and
  design documents of any **Spec-Driven Development (SDD)** project.
- **`dependency-auditor`** — a read-only audit of a project's direct dependencies.

The generators encode one core discipline — **one authority per fact**: every concrete
fact is *defined* in exactly one document; every other mention is a reference or a
clearly subordinate illustration. That is what keeps a document set from drifting apart
as it grows.

## Install (marketplace)

```sh
/plugin marketplace add mcardia/mcardia-claude-kit
/plugin install sdd-generators@mcardia-claude-kit
/plugin install dependency-auditor@mcardia-claude-kit
```

Installing once makes the commands available to you across **all** your projects.

## Commands

### sdd-generators

Each generator runs a focused, one-question-at-a-time interview and emits ready-to-use
Markdown (and, on request, a JSON twin with English keys). A typical project runs them
roughly in this order. See [plugins/sdd-generators/USAGE.md](plugins/sdd-generators/USAGE.md).

| Command | Produces | Role |
|---|---|---|
| `/sdd-generators:constitution` | `methodology.md` + `AGENTS.md` | method pillars, source-of-truth hierarchy, artifact taxonomy (the anti-drift core) |
| `/sdd-generators:prd` | a PRD | problem, goals + metrics, scope, behavior, non-functional targets |
| `/sdd-generators:adr` | one `adr-NNN.md` | a single architecture decision: context, options, decision, trade-offs |
| `/sdd-generators:spec` | `specs/<feature>/{spec,plan,tasks}.md` | per-feature WHAT → HOW → tasks |
| `/sdd-generators:c4` | C4 PlantUML diagrams | canonical C1+C2 and the naming registry at platform scope; C3 per feature |
| `/sdd-generators:traceability` | `docs/traceability.md` | requirement/criterion/target → owning spec/task |
| `/sdd-generators:doclint` | `scripts/check-docs.sh` | project-tailored docs lint: dead references, stale markers, name drift, coverage |
| `/sdd-generators:readiness-audit` | audit verdict + fix plan | multi-lens agent audit → cross-verified fix plan → fresh-eyes re-verification |

Authority flows top-down: **ADRs > standards > reference docs > running system**. Specs
derive from ADRs and never override them.

### What `sdd-generators` deliberately does not do

Every component costs context tokens in **every** session, whether or not it fires. So a
component only survives here when Claude Code ships nothing that does its job. These jobs
were removed from the plugin because a built-in already does them — use the built-in:

| Job | Use this built-in instead | Removed from the plugin |
|---|---|---|
| Review a diff before it merges | `/code-review` (`low`…`max`), `/code-review ultra` for a multi-agent cloud review of a branch or PR | `cascade-reviewer` |
| Validate a review's findings against the design corpus (ADRs, standards, specs) | **No built-in does this** — it is a project-policy step, so it belongs in the consuming project's own `.claude/agents/`, not in a cross-project plugin. `/code-review`'s verify pass is a different axis: it rules a finding `CONFIRMED`/`PLAUSIBLE` against the *code*, not against the corpus | `cascade-validator` |
| Security review of pending changes | `/security-review` | — |
| Execute tasks as orchestrated multi-agent work | the **Workflow** tool (phases, `pipeline()`, `parallel()`, resume that reuses unchanged agent calls) and the **Agent** tool for a single task | `sdd-executor` |
| Author Mermaid behavior diagrams (sequence, state, flowchart, class, ER) | Claude writes Mermaid from a spec unaided; Artifacts render ` ```mermaid ` fences natively, and the built-in `artifact-diagramming` skill covers when a diagram earns its place | `mermaid`, `mermaid-diagram-generator` |
| Scope and run deep research | the built-in `deep-research` skill — it asks its own clarifying questions, fans out searches, adversarially verifies claims, and synthesizes a cited report | `research-briefing`, `research-document` |

Two further reductions were internal rather than delegated to a built-in: the
`c4-diagram-generator` agent was folded into the `/sdd-generators:c4` skill, and the lens
definitions duplicated in `readiness-audit` now live only in the `docs-auditor` agent —
one authority per fact, applied to the plugin itself.

What remains is the part no built-in covers: the **SDD corpus discipline** — a
constitution that fixes the source-of-truth hierarchy, the document generators that obey
it, a traceability matrix, a generated docs lint, and a multi-lens adversarial readiness
audit. TDD rules, review conventions and model assignments are *project* policy: they
belong in the `AGENTS.md` / `methodology.md` that `/sdd-generators:constitution` writes,
not in a cross-project plugin.

### dependency-auditor

```sh
/dependency-auditor:dependency-audit [--project-folder=PATH] [--output-folder=PATH] [--ignore-folders=a,b,c]
```

A read-only report on outdated, vulnerable, deprecated, unmaintained, or license-risky
**direct** dependencies. Severity thresholds mirror a strict dependency-currency policy
(security advisory ≥ moderate or any available patch → immediate; minor/major older
than 30 days → due; no activity for over a year → stale). See
[plugins/dependency-auditor/USAGE.md](plugins/dependency-auditor/USAGE.md).

## Sharing with a project or team

A consuming project can declare this marketplace in its own `.claude/settings.json` so
that teammates are prompted to install it when they trust the workspace:

```json
{
  "extraKnownMarketplaces": {
    "mcardia-claude-kit": { "source": { "source": "github", "repo": "mcardia/mcardia-claude-kit" } }
  },
  "enabledPlugins": {
    "sdd-generators@mcardia-claude-kit": true,
    "dependency-auditor@mcardia-claude-kit": true
  }
}
```

## Where customizations can live (scopes)

| Scope | Location | Who gets it |
|---|---|---|
| Project | `<repo>/.claude/` | only sessions opened inside that repo |
| User | `~/.claude/` | all of your projects, your machine only |
| Plugin / marketplace | this kit, once installed | global for you, versioned, namespaced, shareable |

Paste-the-prompt still works: open a generator's `plugins/sdd-generators/skills/<name>/SKILL.md`,
skip the YAML frontmatter, and paste the body into any AI tool.

## Credits

The plugin/marketplace packaging and the `dependency-auditor` were inspired by the
[Full Cycle Claude Marketplace](https://github.com/devfullcycle/claude-mkt-place) by
Wesley Willians / Full Cycle. The marketplace structure and the dependency-audit
workflow are adapted from that project; the SDD generators themselves are original to
this repository. (The upstream repository carried no license at the time of writing, so
the `dependency-auditor` was reimplemented from scratch rather than copied.)

## License

MIT — see [LICENSE](LICENSE).
