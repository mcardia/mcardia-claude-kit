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
| `/sdd-generators:research-briefing` | a research briefing | scopes an investigation that feeds candidate ADRs |
| `/sdd-generators:research-document` | a deep-research document | the evidence (not authority) that ADRs cite |
| `/sdd-generators:c4` | C4 PlantUML diagrams | architecture diagrams from a spec |
| `/sdd-generators:mermaid` | Mermaid diagrams | high-value diagrams from a spec |

Authority flows top-down: **ADRs > standards > reference docs > running system**. Specs
derive from ADRs and never override them. Deep-research is evidence that feeds
decisions; it is never an authority.

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
