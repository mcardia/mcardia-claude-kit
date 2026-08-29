# AGENTS.md — mcardia-claude-kit

This repository is a **Claude Code marketplace** (`mcardia-claude-kit`) shipping two
plugins: `sdd-generators` and `dependency-auditor`. Everything an end user runs is
delivered **through the plugin**. There is exactly one supported way to install and
update it, described below.

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
/plugin install dependency-auditor@mcardia-claude-kit
```

Equivalent CLI form:

```sh
claude plugin marketplace add mcardia/mcardia-claude-kit
claude plugin install sdd-generators@mcardia-claude-kit
claude plugin install dependency-auditor@mcardia-claude-kit
```

Installing once makes the commands (`/sdd-generators:*`, `/dependency-auditor:*`)
available across **all** your projects. The plugin bundles both the skills and its
registered agent (`docs-auditor`); no separate agent install is needed.

## Update (end user)

```sh
claude plugin marketplace update mcardia-claude-kit      # refresh the marketplace clone from GitHub
claude plugin update sdd-generators@mcardia-claude-kit   # update the installed plugin to the new version
```

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

1. Make the change in the repo. The **agent files in `plugins/sdd-generators/agents/`
   are the single source of truth** for subagent behavior; each `SKILL.md` references
   its agent by name and must not duplicate the agent prompt (no drift).
2. Branch → commit → push → PR → merge to `main`. Production code goes through the
   cascade review; documentation does not.
3. Bump the version in **both** files, which must agree:
   - `plugins/sdd-generators/.claude-plugin/plugin.json` → `version`
   - `.claude-plugin/marketplace.json` → the plugin's `version` entry
   Use SemVer: patch for fixes, minor for new skills/agents, major for breaking changes.
4. Validate before merging:
   ```sh
   claude plugin validate plugins/sdd-generators
   ```
5. After merge, each machine picks up the release via the **Update (end user)** steps
   above. A plugin update only triggers when the version was bumped.

## Why this matters

The kit's core discipline is **one authority per fact, zero drift**. The same principle
applies to its own delivery: the repo is the single authority, the plugin is the only
distribution channel, and the version number is how a change propagates. Manual copies
break all three.
