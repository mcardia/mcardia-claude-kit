---
description: "Generates docs/traceability.md: the authoritative matrix mapping every PRD requirement, acceptance criterion, and non-functional target to its owning spec and task, plus the cross-feature criteria registry."
disable-model-invocation: true
---

# Generator: SDD traceability matrix (`docs/traceability.md`)

# Objective

Author the **traceability matrix** — one document mapping product intent to its owners, making "mandated but owned by nothing" structurally impossible to miss:

- **Requirement → owning spec**: every requirement ID in the PRD (FR-xxx or the project's scheme) mapped to the `specs/<slug>/` that owns it, with notes for split ownership.
- **Infrastructure specs**: specs without their own requirement (undo services, persistence layers) mapped to the ADR that backs them instead.
- **Acceptance criteria → owner**: every product-level acceptance criterion in the PRD mapped to the owning spec (criteria numbers or section) — and any *deliberately* unowned criterion named as such, with where its future owner is queued.
- **Cross-feature criteria registry**: every criterion marked "built by feature A, verified when feature B lands", centralized in one table (location, built-by, verified-when).
- **Non-functional targets → owner**: every measurable PRD target (latency, startup, memory) mapped to the spec/task that tests it.

## Competence boundary

The matrix **maps**; it never restates or redefines. Requirement text stays in the PRD; behavior stays in specs. Each cell is a pointer plus at most one line of splitting/ownership rationale. If the mapping exposes an unowned requirement, that is a **finding to raise to the user** (author or queue a spec), never something to silently absorb into the matrix.

## Phase 0 — Derive from the corpus (do this first)

1. Read the PRD: extract the requirement ID scheme, the full ID list, the acceptance-criteria list, and the measurable non-functional targets.
2. List `specs/*/` (excluding `.template`); read each `spec.md` summary/scope and `tasks.md` to place ownership at the right granularity (task numbers only where a single task owns the fact, e.g., a fixture generator).
3. Grep the specs for cross-feature markers ("Cross-feature", "verified once", "verified when") to build the registry.
4. Read the constitution for the artifact taxonomy so the matrix registers itself correctly.

Present the derived mapping as a draft table set and confirm gaps with the user (especially unowned criteria) before writing the file.

## Output shape

`docs/traceability.md`, opening with a two-line statement of what the document is and how it is kept current, then the tables above in that order. Atemporal body: no dates, no change history.

## Wiring

- Register the matrix in the constitution's artifact taxonomy (one authority per fact: the matrix owns the *mapping*, nothing else).
- If the project has the docs lint (`/sdd-generators:doclint`), point its coverage check at the matrix: every PRD requirement ID present, every spec directory mapped. If it does not, recommend running that generator.
- If the constitution has an amendment protocol, add: "update the matrix in the same stage whenever a requirement/criterion/task mapping moves".

## Style

- English only; terse cells; pointers over prose. Never estimate effort.
