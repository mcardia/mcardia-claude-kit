---
description: "Runs the SDD readiness-audit cycle: independent multi-lens audit agents over the corpus, cross-verification at source, an executable fix plan, and a fresh-eyes re-verification that alone declares READY. Installs docs/standards/VERIFICATION.md on first run."
disable-model-invocation: true
---

# Orchestrator: SDD readiness audit

# Objective

Decide, with evidence, whether a documentation corpus is **READY** for implementation — and, when it is not, drive it there. This skill orchestrates the cycle; the auditing itself is done by independent `docs-auditor` subagents (registered by this plugin).

READY means: internally consistent (no document contradicts another), complete (nothing mandated is owned by nothing), and current (no stale claims) — verified by an agent that did not make the fixes.

## When to run

- Before declaring a corpus (or a multi-spec authoring wave) READY for implementation.
- After autonomous batch authoring — batch authoring is the known drift generator.
- On user order.

Single-document changes need the docs lint and the amendment protocol, not an audit.

## The cycle (follow in order)

### 1. Install the standard (first run only)

If `docs/standards/VERIFICATION.md` (or the project's equivalent) does not exist, author it from the principles below, adapted to the project's paths, and register it in the constitution's taxonomy:

- Verify at source, never trust the report — findings need `file:line` evidence.
- Independent agents, no shared session context.
- Different lenses beat more of the same lens.
- Findings become an executable fix plan, not ad-hoc edits.
- Fresh eyes re-verify; only the re-verification verdict declares READY.
- Recurring finding classes graduate into the docs lint (`/sdd-generators:doclint`).

### 2. Audit

Spawn **N ≥ 2 independent `docs-auditor` agents in parallel**, one per lens:

- **consistency** — cross-document contradictions: names vs the canonical authority, execution order, ownership, cross-references, decision attributions.
- **completeness** — unowned mandates: every PRD requirement traced, every ADR-delegated detail landing in a spec, every cited artifact created by some task, every criterion verifiable or explicitly re-scoped.
- Additional lenses when the surface warrants (security, terminology, test-coverage).

Each brief names the lens, the scope, and the corpus root — nothing of the session's own beliefs.

### 3. Cross-verify

For every finding, check the evidence at source yourself (read/grep). Classify: **accepted** (blocker / major / minor) or **rejected** (with recorded reason). Never relay a finding you did not confirm.

### 4. Plan

Consolidate accepted findings into `plans/plan-readiness-fixes.md` (or the project's plan location): validated findings with evidence first, then ordered execution steps, one commit per step, documentation-only where possible. Present to the user; execution follows the project's approval rules.

### 5. Execute

Per step, one commit each. Steps that change specs trigger the project's amendment protocol duties (diagram regeneration, traceability sync, docs lint) in the same stage.

### 6. Re-verify and declare

Spawn a fresh `docs-auditor` (re-verification lens) with only the fix list: verify each fix at source and scan for regressions the fixes introduced. Defects loop back to step 4. Its READY verdict — never the fixing session's own judgment — closes the cycle.

## Rules

- The orchestrating session never audits its own authored fixes as the final word.
- Historical records (fix plans, audit reports) are excluded from staleness checks — they legitimately quote old defects.
- English only; never estimate effort.
