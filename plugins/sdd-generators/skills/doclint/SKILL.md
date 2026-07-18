---
description: "Generates a project-tailored docs lint (scripts/check-docs.sh): dead cross-references, stale markers, canonical-name drift, policy violations, traceability coverage, diagram integrity. The mechanized regression guard for the SDD corpus."
disable-model-invocation: true
---

# Generator: SDD docs lint (`scripts/check-docs.sh`)

# Objective

Author a **project-tailored bash lint** for the SDD documentation corpus and wire it into the project's gates. The lint mechanizes the finding classes that documentation audits repeatedly surface, so agents and humans stop paying for them:

1. **Dead path references** — repo paths cited in docs that do not exist (with an allowlist for artifacts that tasks author later).
2. **Stale markers** — phrases that betray an unsynced document ("to be authored", "once authored", "future dedicated spec", project-specific ones).
3. **Canonical-name drift** — module/crate/package names outside the project's canonical map (the single worst drift class in autonomous batch authoring).
4. **Policy violations** — terms the project's decisions forbid outside exclusion phrasing (e.g., a banned platform, a superseded technology).
5. **Decision-range citations** — references to ADR numbers beyond the authored set.
6. **Traceability coverage** — every requirement ID from the PRD and every spec directory appears in the traceability matrix (if the project has one — see `/sdd-generators:traceability`).
7. **Diagram integrity** — balanced Mermaid fences; exactly one `@startuml`/`@enduml` pair per PlantUML file; deep syntax check when a free/OSS `plantuml` binary is available (skip with a note otherwise).

The output is one executable file, `scripts/check-docs.sh`, plus the wiring edits (CI/standards doc, constitution amendment rule) the project's structure calls for.

## Competence boundary

The lint checks **mechanical** consistency only. Semantic contradictions, unowned mandates, and wrong attributions belong to the readiness audit (`/sdd-generators:readiness-audit`); do not try to encode them as greps. The lint is the always-on subset; the audit is the periodic deep pass.

## Phase 0 — Derive the project facts (do this first, from the corpus)

Scan the repository and derive every parameter from what actually exists — never invent:

- **Constitution / methodology** (`AGENTS.md`, `methodology.md`, `standards/`): the canonical-name authority (module/crate map, naming registry), the editing rules, any platform/technology policies (e.g., "Wayland-only", "no ORM") whose violation the lint should catch, and the CI/standards doc to wire the gate into.
- **Corpus layout**: where docs live (`docs/`, `specs/`, `plans/`), which files are historical records to exclude (audit fix plans, scratch dirs), diagram directories (Mermaid, PlantUML).
- **Planned artifacts**: reference docs and scripts that specs/tasks cite but that implementation tasks author later — these seed the allowlist, each with a comment naming the authoring task. If a whole directory is planned (e.g., `docs/reference/`), the blanket exemption must **expire automatically once the directory exists** — from then on only explicit allowlist entries pass.
- **Requirement IDs**: the PRD's ID scheme (e.g., `FR-\d{3}`) — derive the coverage list from the PRD at runtime, never hardcode it.
- **Traceability matrix path** (if present).

Present the derived configuration as a short summary and confirm it with the user before writing the script.

## Script requirements (hard rules)

- Plain bash, `set -u`, no dependencies beyond git/grep/sed and optional `plantuml`. All tooling free and OSS.
- `cd` to the repo root via `git rev-parse --show-toplevel`; bail out with a clear message (exit 1) when no tracked doc files are found.
- Scope from `git ls-files` (stderr-guarded), with the historical/scratch exclusions derived in Phase 0.
- Exit 0 clean / exit 1 with findings printed as `<file>:<line>: <message>`. Never let a `cmd | while read` subshell swallow the failure flag — use `while ... done < <(...)`.
- Guard every glob loop (`[ -e "$f" ] || continue`, `[ -d "$d" ] || continue`); never report "syntax errors" when the real condition is "no input files".
- Case-insensitive matching for exclusion-phrase allowlists (sentence-initial capitals are legitimate).
- Comment each check block with what it guards and why; comment each allowlist entry with the task that will retire it.

## Verification (mandatory before finishing)

1. **Dogfood**: the script must exit 0 on the current corpus. Every finding it raises is either a real defect (fix it with the user or record it) or a false positive (refine the check — never weaken it into uselessness).
2. **Negative probes**: for each check class, inject a temporary defective file, assert exit 1 and the expected message, then remove it. A check without a failing probe is not proven to work.
3. `bash -n` syntax check.

## Wiring

- Register the script as a gate in the project's CI/standards doc and in its pre-push mirror if one exists.
- If the constitution has an amendment/change protocol, add the lint to it ("run before committing any documentation change"). If the project uses `/sdd-generators:traceability`, point check 6 at the matrix.
- Register `scripts/` in the constitution's artifact taxonomy if it is not there.

## Reference template

Use this structure as the starting point, replacing the `<derived: …>` slots with Phase 0 facts and deleting checks the project has no substrate for (e.g., no PlantUML → drop check 7b):

```bash
#!/usr/bin/env bash
# Docs lint for the <derived: project> SDD corpus. Gate registered in <derived: CI doc>.
# Exit 0 = clean; exit 1 = findings printed as <file>:<line>: <message>.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
FAIL=0
fail() { printf '%s\n' "$1"; FAIL=1; }

mapfile -t DOC_FILES < <(git ls-files '*.md' <derived: diagram globs> 2>/dev/null \
  | grep -v <derived: historical/scratch exclusions>)
[ "${#DOC_FILES[@]}" -eq 0 ] && { printf 'check-docs: no tracked doc files found (not a repo?)\n'; exit 1; }

# 1. Dead path references (allowlist: planned artifacts, each comment names its authoring task)
PLANNED_PATHS=( <derived: planned files> )
is_planned() {
  local p="$1"
  for a in "${PLANNED_PATHS[@]}"; do [ "$p" = "$a" ] && return 0; done
  [ ! -d <derived: planned dir> ] && case "$p" in <derived: planned dir>/*) return 0 ;; esac
  return 1
}
while IFS=: read -r file line path; do
  path="${path%.}"
  [ -z "$path" ] && continue
  case "$path" in *'<'*|*'*'*|*-|*/) continue ;; esac   # placeholders, globs, truncated tokens
  [ -e "$path" ] && continue
  is_planned "$path" && continue
  fail "$file:$line: dead path reference: $path"
done < <(grep -nEo '(<derived: top-level dirs>)/[A-Za-z0-9._/<>-]+' "${DOC_FILES[@]}" /dev/null)

# 2. Stale / banned markers
BANNED='once authored|to be authored|future dedicated spec|<derived: project-specific>'
while IFS= read -r hit; do fail "$hit: banned stale marker"; done \
  < <(grep -nEi "$BANNED" "${DOC_FILES[@]}" /dev/null)

# 3. Canonical-name drift  (known-bad names fail anywhere; path-form names must be canonical)
# <derived from the naming authority>

# 4. Policy violations  (banned term outside case-insensitive exclusion phrasing)
# <derived from the project's decision records>

# 5. Decision-range citations
MAX_ADR=$(ls <derived: adr dir>/adr-*.md 2>/dev/null | sed -E 's/.*adr-0*([0-9]+)-.*/\1/' | sort -n | tail -1)
# fail any ADR-NNN citation with NNN > MAX_ADR

# 6. Traceability coverage  (IDs derived from the PRD at runtime; every spec dir mapped)
# 7. Diagram integrity  (fence balance; @startuml/@enduml pairing; optional plantuml -checkonly
#    guarded so "no input files" is never reported as a syntax error)

[ "$FAIL" -eq 0 ] && printf 'check-docs: clean (%d files)\n' "${#DOC_FILES[@]}"
exit "$FAIL"
```

## Style

- English only. The script and its messages are terse and evidence-first.
- Never estimate effort anywhere in the output.
