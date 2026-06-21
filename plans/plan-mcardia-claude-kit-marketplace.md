# Plan: Turn this repo into the `mcardia-claude-kit` Claude Code marketplace

You are an AI agent implementing this plan end-to-end. Execute the phases in order.
Each step is concrete and actionable. Do not skip the pre-execution snapshot or the
validation phase. Stop and ask the operator only at the explicit decision gate.

---

## 1. Goal

Convert this repository from a set of paste-into-the-chat interview prompts into an
installable **Claude Code plugin marketplace** named **`mcardia-claude-kit`**,
preserving the project's core discipline (**one authority per fact**), and add a new
**dependency-auditor** capability inspired by the upstream marketplace we studied.

The repository *is* the marketplace. It ships two plugins:

1. **`sdd-generators`** — the 8 existing generators exposed as `/sdd-*` slash commands.
2. **`dependency-auditor`** — a read-only dependency audit command + subagent whose
   thresholds match the operator's global Dependency Management policy.

Distribution is via the plugin system only (`/plugin marketplace add` +
`/plugin install`). There is **no `install.sh`** and **no `~/.claude` copying** —
installing a plugin once is already global for the user across all projects, and a
consuming project can auto-prompt teammates via its own `.claude/settings.json`.

Credit the upstream project (`devfullcycle/claude-mkt-place`, Full Cycle /
Wesley Willians) in the README — its patterns inspired this work.

---

## 2. Resolved decisions (baked in — do not re-ask)

- **Distribution model:** marketplace/plugins only. No user-scope copy script.
- **Marketplace name:** `mcardia-claude-kit`.
- **GitHub slug:** `mcardia/mcardia-claude-kit` (repo currently
  `mcardia/sdd-generators` — see Phase E for the rename).
- **Source of truth for generators:** they live **once**, inside
  `plugins/sdd-generators/generators/`. No root copies, so no drift gate is needed.
- **`bootstrap.sh` is removed** — the marketplace replaces its `_generators/` copy
  purpose.

---

## 3. Context and source material

- Patterns come from a temporary clone at `tmp-cloud-mkt-place/` (a fork of
  `devfullcycle/claude-mkt-place`). Treat it as **read-only reference**, never a
  dependency. It must stay untracked — do not `git add` it; git-ignore it (Phase D).
- Upstream structure we adapt:
  - `.claude-plugin/marketplace.json` at repo root listing plugins.
  - `plugins/<name>/.claude-plugin/plugin.json` per plugin.
  - `plugins/<name>/commands/*.md` (slash commands: frontmatter + body).
  - `plugins/<name>/agents/*.md` (subagents: frontmatter `name`, `description`,
    `model`, `color` + body).
  - `plugins/<name>/USAGE.md` per plugin.
- The 8 canonical generators are currently at repo root: `01-constitution.md` …
  `08-mermaid.md`.

### Licensing gate (do FIRST — it changes Phase B)

The upstream repo studied has **no LICENSE file**. Before reusing any agent text:

1. Check the public upstream `devfullcycle/claude-mkt-place` on GitHub for a license
   (WebFetch the repo root and a `LICENSE`/`LICENSE.md` path).
2. **Permissive license (MIT/Apache/BSD):** you may adapt the `dependency-auditor`
   agent text, keeping required attribution.
3. **No license / unclear / restrictive:** do NOT copy text verbatim. Reimplement the
   agent from scratch in our own words (the capability and section list are not
   copyrightable; the prose is). Credit as "inspired by" regardless.

Record which branch you took in the PR/commit message.

---

## 4. Constraints (non-negotiable)

- **One authority per fact:** generator bodies are defined in exactly ONE place
  (`plugins/sdd-generators/generators/NN-*.md`). Command files MUST NOT duplicate
  generator prose — they reference it via `${CLAUDE_PLUGIN_ROOT}`.
- **English only** for all files, identifiers, comments, commit/tag messages.
- **Edit existing files with `Edit`; create new files with `Write`.** Move files with
  `git mv`. Never use `sed`/`awk` to edit file contents.
- All tooling introduced must be free and OSS.
- Do not estimate effort anywhere in the deliverables.
- Keep `tmp-cloud-mkt-place/` out of version control.

---

## 5. Target structure

```
mcardia-claude-kit/                       (repo root = the marketplace)
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── sdd-generators/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── commands/
│   │   │   ├── sdd-constitution.md
│   │   │   ├── sdd-prd.md
│   │   │   ├── sdd-adr.md
│   │   │   ├── sdd-spec.md
│   │   │   ├── sdd-research-briefing.md
│   │   │   ├── sdd-research-document.md
│   │   │   ├── sdd-c4.md
│   │   │   └── sdd-mermaid.md
│   │   ├── generators/                   (canonical 01..08 — single source of truth)
│   │   │   ├── 01-constitution.md … 08-mermaid.md
│   │   └── USAGE.md
│   └── dependency-auditor/
│       ├── .claude-plugin/plugin.json
│       ├── commands/dependency-audit.md
│       ├── agents/dependency-auditor.md
│       └── USAGE.md
├── plans/
├── README.md
└── LICENSE
```

---

## 6. Pre-execution snapshot (mandatory, before any change)

1. Ensure the working tree is clean except for untracked `tmp-cloud-mkt-place/`.
2. Commit anything staged so the snapshot is faithful.
3. Tag the snapshot:
   ```sh
   git tag before-plan-mcardia-claude-kit-marketplace
   ```
4. Work on a feature branch:
   ```sh
   git switch -c feat/mcardia-claude-kit-marketplace
   ```

---

## 7. Phase A — Scaffold the marketplace and the `sdd-generators` plugin

### 7.1 Verify the plugin spec first

Confirm current Claude Code plugin conventions against the official docs (spawn the
`claude-code-guide` agent or WebFetch the docs) before authoring:
- Exact filenames/locations of `marketplace.json` and `plugin.json`.
- Command frontmatter keys honored (`description`, `argument-hint`, `allowed-tools`)
  and how arguments are passed (`$ARGUMENTS`).
- The exact plugin-root environment variable (expected `${CLAUDE_PLUGIN_ROOT}`).
- How plugin command names are namespaced (e.g. `/sdd-generators:sdd-adr`).

If any assumed token differs from the docs, use the documented form and note it.

### 7.2 Move generators into the plugin (single source of truth)

```sh
mkdir -p plugins/sdd-generators/generators
git mv 01-constitution.md          plugins/sdd-generators/generators/01-constitution.md
git mv 02-prd.md                   plugins/sdd-generators/generators/02-prd.md
git mv 03-adr.md                   plugins/sdd-generators/generators/03-adr.md
git mv 04-spec.md                  plugins/sdd-generators/generators/04-spec.md
git mv 05-deep-research-briefing.md plugins/sdd-generators/generators/05-deep-research-briefing.md
git mv 06-deep-research-document.md plugins/sdd-generators/generators/06-deep-research-document.md
git mv 07-c4.md                    plugins/sdd-generators/generators/07-c4.md
git mv 08-mermaid.md               plugins/sdd-generators/generators/08-mermaid.md
git rm bootstrap.sh
```

### 7.3 Marketplace + plugin manifests

Create with `Write`:

1. `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "mcardia-claude-kit",
     "owner": { "name": "Mario Cardia" },
     "description": "Mario Cardia's Claude Code kit: Spec-Driven Development generators and architecture tooling",
     "version": "1.0.0",
     "plugins": [
       {
         "name": "sdd-generators",
         "description": "Interview-style generators for SDD governance and design documents (constitution, PRD, ADR, spec, deep-research, C4, Mermaid)",
         "source": "./plugins/sdd-generators",
         "version": "1.0.0"
       },
       {
         "name": "dependency-auditor",
         "description": "Read-only dependency health and security audit aligned with the project dependency-currency policy",
         "source": "./plugins/dependency-auditor",
         "version": "1.0.0"
       }
     ]
   }
   ```
2. `plugins/sdd-generators/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "sdd-generators",
     "description": "Interview-style generators for SDD governance and design documents",
     "version": "1.0.0",
     "author": { "name": "Mario Cardia" }
   }
   ```

### 7.4 One thin command launcher per generator

For each generator create `plugins/sdd-generators/commands/<cmd>.md`. The body MUST
NOT contain generator prose — it loads and runs the canonical copy. Mapping:

| Command file | Slash command | Loads |
|---|---|---|
| `sdd-constitution.md` | `/sdd-constitution` | `generators/01-constitution.md` |
| `sdd-prd.md` | `/sdd-prd` | `generators/02-prd.md` |
| `sdd-adr.md` | `/sdd-adr` | `generators/03-adr.md` |
| `sdd-spec.md` | `/sdd-spec` | `generators/04-spec.md` |
| `sdd-research-briefing.md` | `/sdd-research-briefing` | `generators/05-deep-research-briefing.md` |
| `sdd-research-document.md` | `/sdd-research-document` | `generators/06-deep-research-document.md` |
| `sdd-c4.md` | `/sdd-c4` | `generators/07-c4.md` |
| `sdd-mermaid.md` | `/sdd-mermaid` | `generators/08-mermaid.md` |

Template (adjust description/tags per generator):
```markdown
---
description: <one-line purpose of this generator>
tags: [sdd, <constitution|prd|adr|spec|research|diagrams>]
---

Read the generator at `${CLAUDE_PLUGIN_ROOT}/generators/<NN-name>.md` and adopt its
full content as your operating prompt for this session. Then run the interview exactly
as that prompt specifies — one question at a time — and emit the documents in the
standard format it defines.

User's starting context (optional): $ARGUMENTS
```
(Use the verified argument token from 7.1 if `$ARGUMENTS` is not correct.)

### 7.5 Plugin USAGE.md

Create `plugins/sdd-generators/USAGE.md`: list the 8 commands, what each produces
(reuse the table from the old root README), and the "one authority per fact" note.

---

## 8. Phase B — `dependency-auditor` plugin

Honor the licensing gate (Section 3): adapt vs. reimplement accordingly.

### 8.1 Manifest

`plugins/dependency-auditor/.claude-plugin/plugin.json` (same shape as 7.3, name
`dependency-auditor`).

### 8.2 Command

`plugins/dependency-auditor/commands/dependency-audit.md`:
- Frontmatter `allowed-tools: Task, Read, Write, WebSearch, WebFetch, TodoWrite`.
- Body: invoke the `dependency-auditor` subagent via the Task tool, parsing
  `--project-folder`, `--output-folder` (default `docs/dependency-auditor`),
  `--ignore-folders`. Follow Linux option conventions (short + long where sensible).
  No time/effort estimates in output.

### 8.3 Subagent

`plugins/dependency-auditor/agents/dependency-auditor.md` (frontmatter
`name: dependency-auditor`, `description`, `model: sonnet`, `color`). The agent is
**read-only — never modifies project files**. Report sections: Summary, Critical
Issues, Dependencies table, Risk Analysis, Unverified Dependencies, Critical File
Analysis, Integration Notes, then save the report.

**Thresholds MUST match the operator's global Dependency Management policy (not the
generic upstream ones):**
- Flag **immediately**: any open security advisory of severity ≥ moderate, and any
  available patch-level update (`X.Y.Z+1`).
- Flag minor/major updates released **> 30 days ago** and not yet applied.
- Flag libraries unmaintained **> 1 year**; check license compatibility.
- Catalog **direct dependencies only**. Use Context7/web to verify latest versions;
  list anything unverifiable under "Unverified Dependencies".
- No emojis. No time/effort estimates.

### 8.4 USAGE.md

`plugins/dependency-auditor/USAGE.md` with invocation examples and the policy-alignment
note.

---

## 9. Phase C — README rewrite and credits

Rewrite root `README.md` (use `Edit`/`Write`) to describe the kit, not a single repo:

1. **What it is:** the `mcardia-claude-kit` marketplace with two plugins; keep the
   generators table and the "one authority per fact" explanation.
2. **Install (marketplace):**
   ```
   /plugin marketplace add mcardia/mcardia-claude-kit
   /plugin install sdd-generators@mcardia-claude-kit
   /plugin install dependency-auditor@mcardia-claude-kit
   ```
   Note: installing once is global for the user across all projects.
3. **Commands:** list the 8 `/sdd-*` commands and `/dependency-audit`.
4. **Team / per-project auto-prompt** — a consuming project can declare this in its
   own `.claude/settings.json` so teammates are prompted on workspace trust:
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
5. **Scopes note (brief):** project `.claude/` (repo-only), user `~/.claude/`
   (all your projects, one machine), plugin/marketplace (this kit — versioned,
   namespaced, shareable). State that paste-the-prompt still works by opening the
   files under `plugins/sdd-generators/generators/`.
6. **Credits** (operator explicitly requested):
   ```markdown
   ## Credits

   The plugin/marketplace packaging and the dependency-auditor were inspired by the
   [Full Cycle Claude Marketplace](https://github.com/devfullcycle/claude-mkt-place)
   by Wesley Willians / Full Cycle. The structure and the dependency-audit workflow
   are adapted from that project; the SDD generators themselves are original to this
   repository.
   ```
   (If the licensing gate found a license, append "Used under the &lt;LICENSE&gt; license.")

---

## 10. Phase D — `.gitignore`

Add `tmp-cloud-mkt-place/` to `.gitignore` so the reference clone is never committed.

---

## 11. Phase E — GitHub repository rename (operator action)

The marketplace install slug must resolve. Rename the GitHub repo
`mcardia/sdd-generators` → `mcardia/mcardia-claude-kit` (GitHub auto-redirects the old
slug, but update `git remote set-url origin` locally). Optionally rename the local
directory. This is an operator/`gh` action — confirm before performing.

---

## 12. Validation (before opening the PR)

1. **JSON validity:** every `*.json` manifest parses (e.g. `python3 -m json.tool`).
2. **No duplication:** each `commands/sdd-*.md` references `${CLAUDE_PLUGIN_ROOT}` and
   contains no generator prose (it should be short).
3. **Single source:** the 8 generators exist only under
   `plugins/sdd-generators/generators/`; none remain at repo root; `bootstrap.sh` gone.
4. **Install smoke test:** in a scratch Claude Code session, add the local marketplace
   path, install both plugins, confirm `/sdd-constitution` loads its generator and
   starts the interview, and `/dependency-audit` launches the subagent.
5. **English-only + no effort estimates** across all new/changed files.

---

## 13. Review and merge

- This deliverable is prompt markdown + JSON manifests (documentation/config), with
  **no executable production code** (no scripts). Per the operator's methodology,
  cascade is **not** triggered — review is operator + AI, pendency by pendency.
  (If any shell/other script is introduced during implementation, run the 3-stage
  cascade on that script before merge.)
- Open the PR from `feat/mcardia-claude-kit-marketplace` into `main`. In the PR body,
  state the licensing-gate branch taken (adapted vs. reimplemented).

---

## 14. Out of scope (do not do here)

- Hardening `03-adr.md` with strict MADR guardrails (Tier 1/2, `[NEEDS INPUT]`, size
  limits) — separate plan.
- Porting `project-analyzer` (architectural report, component deep-dive) or the ADR
  map→identify→generate→link brownfield workflow.
- Porting `development-guidelines` (overlaps the operator's `~/.claude/*_GUIDELINES.md`).
- Any `install.sh` / `~/.claude` copy mechanism (rejected in favor of the marketplace).
- Any change to `tmp-cloud-mkt-place/` or committing it.

---

## 15. Acceptance criteria

- [ ] `.claude-plugin/marketplace.json` names `mcardia-claude-kit`, lists both
      plugins, and parses.
- [ ] `sdd-generators` plugin: 8 `/sdd-*` thin-launcher commands; generators live only
      under `plugins/sdd-generators/generators/`; no prose duplication.
- [ ] `dependency-auditor` plugin: `/dependency-audit` + read-only subagent with
      thresholds matching the global Dependency Management policy.
- [ ] README documents marketplace install, the per-project `settings.json` snippet,
      the three scopes, retained paste-prompt usage, and credits the upstream.
- [ ] `bootstrap.sh` removed; no `install.sh` introduced.
- [ ] `tmp-cloud-mkt-place/` is git-ignored and uncommitted.
- [ ] GitHub repo reachable at `mcardia/mcardia-claude-kit` (Phase E).
- [ ] PR documents the licensing-gate decision.
</content>
