# AGENTS.md — mcardia-claude-kit

This repository is a **Claude Code marketplace** (`mcardia-claude-kit`) shipping four
plugins: `sdd-generators`, `operator-decision-gate`, `autonomy-grant-gate` and
`dependency-auditor`. Everything an end user runs is delivered **through the plugin**.
There is exactly one supported way to install and update it, described below.

## Golden rule: the plugin is the only delivery mechanism

**Never hand-copy skills or agents into `~/.claude/`.** Do not place files under
`~/.claude/skills/` or `~/.claude/agents/` to "install" or "update" these generators.
Those manual copies are unversioned, invisible to `claude plugin update`, and drift
away from the repo — the exact contradiction this kit exists to prevent. The plugin
already provides every skill and agent; that is the canonical, version-managed source.

If you find manual copies on a machine (e.g. `~/.claude/skills/sdd-*`), remove them and
rely on the installed plugin instead.

## Install (end user)

In an interactive Claude Code session:

```sh
/plugin marketplace add mcardia/mcardia-claude-kit
/plugin install sdd-generators@mcardia-claude-kit
/plugin install operator-decision-gate@mcardia-claude-kit
/plugin install autonomy-grant-gate@mcardia-claude-kit
/plugin install dependency-auditor@mcardia-claude-kit
```

Equivalent CLI form:

```sh
claude plugin marketplace add mcardia/mcardia-claude-kit
claude plugin install sdd-generators@mcardia-claude-kit
claude plugin install operator-decision-gate@mcardia-claude-kit
claude plugin install autonomy-grant-gate@mcardia-claude-kit
claude plugin install dependency-auditor@mcardia-claude-kit
```

Each plugin installs on its own; take the ones you want. Installing one makes its
commands (`/sdd-generators:*`, `/operator-decision-gate:*`, `/dependency-auditor:*`)
available across **all** your projects, and each bundles everything it needs:
`sdd-generators` its eight interview skills and the `docs-auditor` agent;
`operator-decision-gate` its skill, the `od-lens` agent, the `od-gate` workflow and two
hooks; `autonomy-grant-gate` one `Stop` hook, a calibration script and their suite, and
registers no command at all; `dependency-auditor` its command and the agent that runs
the audit.

The first two are independent installs with one deliberate seam. `operator-decision-gate`
reads an operator-decision section out of the consuming project's constitution and never
authors it; the interview that authors it is `/sdd-generators:constitution`. Install the
gate alone and it stays inert until that section exists — written by hand, or by
installing `sdd-generators` for the one interview stage that produces it.

`autonomy-grant-gate` takes the opposite stance on purpose, and it is the only plugin
here that does. A continuous autonomy grant is a conversational act, not a corpus
section, so there is nothing to parse and no opt-in to detect: it **ships a default
vocabulary**, applies wherever it is installed, and is self-limiting only in practice —
in a project where nobody grants autonomy it never fires, but its `python3` process runs
on every turn end there all the same. An optional `.claude/autonomy-grant.json` in the
project replaces the words. The departure and its price are stated in that plugin's
USAGE.

## Update (end user)

```sh
claude plugin marketplace update mcardia-claude-kit              # refresh the marketplace clone from GitHub
claude plugin list                                               # which of the four this machine already has
claude plugin update <plugin>@mcardia-claude-kit                 # each one it has, by name
claude plugin install <plugin>@mcardia-claude-kit                # each one you want that it does not have
```

Refreshing the marketplace updates nothing by itself, and `update` cannot install a
plugin that was never installed — it fails with `Plugin "<name>" is not installed` and
changes nothing. So the sequence asks the machine what it has instead of naming the
four: what is there is updated by name, and only when its own version was bumped; what
is missing is added with `install`. **An update that skips that second command leaves a
plugin absent while reporting success on the others.**

**The gate is the case where that silently removes enforcement.** Its skill, agent,
workflow and both hooks shipped inside `sdd-generators` before `operator-decision-gate`
became a plugin of its own. A machine that installed the generators then, and now only
updates them, keeps the generators and has no gate — nothing refused, nothing said.
`claude plugin install operator-decision-gate@mcardia-claude-kit` is what puts it back,
once; it updates by name after that.

`claude plugin update` prints **"Restart to apply changes."** **Restarting Claude Code
is the reliable, version-independent way to apply the update** — a running session keeps
the version it started with, so an update on disk only takes effect on restart.

Recent CLI versions also expose in-session reload commands, but they may be absent on
older builds (and a running session predating the update will not have them) — treat
them as an optional shortcut, not a guarantee:

- `/reload-plugins` — reloads plugins, skills, agents, hooks and plugin MCP servers
  (add `--force` if it warns about invalidating the MCP tool cache).
- `/reload-skills` — reloads standalone skills/commands only (does not pick up new agents).

Verify with `/plugin` and `/agents`.

## Release (maintainer)

Code and docs live only in this repo; changes reach users by publishing a new version.

1. Make the change in the repo. Where a skill **ships an agent**, the agent file in
   that plugin's own `agents/` directory is the **single source of truth** for that
   subagent's behavior: the `SKILL.md` references it by name and must not duplicate
   the agent prompt (no drift). A skill with no agent carries its own prompt in full —
   one authority either way, never two.
2. Branch → commit → push → PR → merge to `main`. Production code goes through the
   independent review before merge defined in the operator's global rules; documentation
   does not.
3. Bump the version in **both** files, which must agree:
   - `plugins/<plugin>/.claude-plugin/plugin.json` → `version`
   - `.claude-plugin/marketplace.json` → that plugin's `version` entry
   Bump only the plugins the change touches; a plugin whose files did not move keeps its
   number, and the marketplace's own top-level `version` does not track plugin releases.
   Use SemVer: patch for fixes, minor for new skills/agents, major for breaking changes
   — and **removing a component from a released plugin is breaking**, whoever is believed
   to have installed it.
4. Validate before merging, once per plugin the change touches:
   ```sh
   claude plugin validate plugins/sdd-generators
   claude plugin validate plugins/operator-decision-gate
   claude plugin validate plugins/autonomy-grant-gate
   claude plugin validate plugins/dependency-auditor
   ```
5. **Run the behavioural suite** of each gate the change touched:
   ```sh
   python3 plugins/operator-decision-gate/hooks/test_hooks.py
   python3 plugins/autonomy-grant-gate/hooks/test_hooks.py
   ```
   `claude plugin validate` reads manifests; it does not run anything. Those hooks are
   the only executable code this marketplace ships and they REFUSE tool calls and
   turn-ends, so a regression there does not raise an error — the gate quietly stops
   guarding, in every project that installed it. Six of the operator-decision cases hold
   that plugin's parser and the `constitution` generator's template to one contract
   across a plugin boundary; they SKIP, saying so and naming the paths they tried, when
   the sibling is not present. **A skip is not a pass** — from a checkout of this
   repository both plugins are there and the full count must run.
6. After merge, each machine picks up the release via the **Update (end user)** steps
   above. A plugin update only triggers when the version was bumped.

## Why this matters

The kit's core discipline is **one authority per fact, zero drift**. The same principle
applies to its own delivery: the repo is the single authority, the plugin is the only
distribution channel, and the version number is how a change propagates. Manual copies
break all three.
