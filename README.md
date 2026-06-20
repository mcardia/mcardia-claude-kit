# sdd-generators

Interview-style prompts that bootstrap the governance and design documents of any
**Spec-Driven Development (SDD)** project. Paste a generator into your AI tool; it
runs a focused, one-question-at-a-time interview and emits ready-to-use Markdown
(and optionally JSON).

The generators encode one core discipline — **one authority per fact**: every
concrete fact is *defined* in exactly one document; every other mention is a
reference or a clearly subordinate illustration. That is what keeps a document set
from drifting apart as it grows.

## The generators

Each is independent and can be re-run. A typical project runs them roughly in this
order.

| # | Generator | Produces | Role |
|---|---|---|---|
| 01 | `01-constitution.md` | `methodology.md` + `AGENTS.md` | the root: method pillars, source-of-truth hierarchy, artifact taxonomy (the anti-drift core) |
| 02 | `02-prd.md` | a PRD | product intent: problem, goals + metrics, scope, behavior, non-functional targets |
| 03 | `03-adr.md` | one `adr-NNN.md` | a single architecture decision: context, options, decision, trade-offs |
| 04 | `04-spec.md` | `specs/<feature>/{spec,plan,tasks}.md` | per-feature WHAT → HOW → tasks |
| 05 | `05-deep-research-briefing.md` | a research briefing | scopes an investigation that feeds candidate ADRs |
| 06 | `06-deep-research-document.md` | a deep-research document | the evidence (not authority) that ADRs cite |
| 07 | `07-c4.md` | C4 PlantUML diagrams | architecture diagrams from a spec |
| 08 | `08-mermaid.md` | Mermaid diagrams | high-value diagrams from a spec |

Authority flows top-down: **ADRs > standards > reference docs > running system**.
Specs derive from ADRs and never override them. Deep-research is evidence that
feeds decisions; it is never an authority.

## Using a generator

1. Open a generator file and paste its full content into your AI tool (Claude,
   etc.) as the first prompt.
2. Answer the interview, one question at a time.
3. The tool emits the document(s) in the standard format, and on request a JSON
   twin with English keys.

## Bootstrapping a project

These generators are meant to sit alongside a project as local, git-ignored
tooling. To snapshot them into a project:

```sh
./bootstrap.sh /path/to/your-project
```

That copies the generators into `<project>/_generators/` so the project gets a
frozen snapshot while this repo keeps evolving on its own. Add `_generators/` to
the project's `.gitignore`.

## License

MIT — see [LICENSE](LICENSE).
