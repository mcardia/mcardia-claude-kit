---
description: Run a read-only dependency audit and write a report on outdated, vulnerable, deprecated, or stale direct dependencies, aligned with the project dependency-currency policy.
argument-hint: [--project-folder=PATH] [--output-folder=PATH] [--ignore-folders=a,b,c]
disable-model-invocation: true
allowed-tools: Task Read Write WebSearch WebFetch TodoWrite
---

Run a dependency audit by delegating to the `dependency-auditor` subagent. The audit is
strictly read-only: never modify project files, never run upgrade commands.

Parse these optional arguments from `$ARGUMENTS` (support short and long forms):

- `--project-folder` / `-p` — folder to audit (default: the repository root).
- `--output-folder` / `-o` — where to write the report (default: `docs/dependency-auditor`).
- `--ignore-folders` / `-i` — comma-separated folders to exclude (e.g. `node_modules,dist,.venv`).

Then invoke the subagent with the Task tool:

- `subagent_type`: `dependency-auditor`
- `prompt`: "Run a dependency audit. project-folder: <value or repository root>. output-folder: <value or docs/dependency-auditor>. ignore-folders: <value or none>. Follow your full workflow and report sections, then save the report and return its path."

Raw arguments: $ARGUMENTS
