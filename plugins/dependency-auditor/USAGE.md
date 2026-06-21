# dependency-auditor

A read-only audit of a project's **direct** dependencies. It finds outdated,
vulnerable, deprecated, unmaintained, or license-risky libraries and writes a
structured report. It never modifies the codebase, runs upgrades, or prescribes
migrations.

## Command

```
/dependency-auditor:dependency-audit [--project-folder=PATH] [--output-folder=PATH] [--ignore-folders=a,b,c]
```

| Option | Short | Default | Meaning |
|---|---|---|---|
| `--project-folder` | `-p` | repository root | Folder to audit |
| `--output-folder` | `-o` | `docs/dependency-auditor` | Where the report is written |
| `--ignore-folders` | `-i` | none | Comma-separated folders to skip |

### Examples

```
/dependency-auditor:dependency-audit
/dependency-auditor:dependency-audit --project-folder=services/api
/dependency-auditor:dependency-audit --ignore-folders=node_modules,dist,.venv
/dependency-auditor:dependency-audit -p src -o reports -i node_modules
```

The report is saved as `dependency-audit-{YYYY-MM-DD}.md` in the output folder.

## Policy alignment

Severity thresholds mirror the project dependency-currency policy:

- Security advisory severity ≥ moderate, or any available patch update → flag immediately.
- Minor/major update released more than 30 days ago and not applied → flag as due.
- No release/repository activity for more than one year → flag as stale.
- Incompatible, more restrictive, or missing license → flag as legal risk.

Versions and advisories are verified against authoritative sources; anything that
cannot be verified is listed under "Unverified Dependencies" rather than guessed.
