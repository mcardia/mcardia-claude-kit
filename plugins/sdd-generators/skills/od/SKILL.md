---
description: "Apply the project's operator-decision rule: verify cause and remedy at source, run the adversarial panel, grade the change, then either execute it or hand it over — as one fixed record either way. Use this whenever a finding, defect, design question or blocker looks like something the operator must decide, BEFORE writing that anywhere; also when asked to 'show this as an operator decision', or when a turn is about to end by handing something over."
---

# Orchestrator: the operator-decision gate

# Objective

Settle **who decides**, on evidence, and produce the record that says so — in the same act. A project running Spec-Driven Development generates a stream of findings, and each one poses the same question before anything else can happen: is this the coordinating session's to execute, or the operator's to rule on?

The rule that answers it lives in the project's own constitution. This skill does not restate it and is not an authority over it. What this skill adds is the procedure that makes the rule bind: a verification pass the session cannot perform on itself, an adversarial panel, and a record whose shape is checked.

## Why this exists as a mechanism and not as advice

The recorded failure is **not forgetting**. The rule was present, in the constitution and in memory, and it still lost — to a competing instruction in the same context window that was more specific about the immediate act. A session reads "show me this as an operator decision", obeys the literal verb, and presents something the rule said to execute. The operator's words for it: *"memory and AGENTS.md are not working."*

So the correction is not emphasis. It is that the correct path costs one call, and that two hooks refuse the violation at the boundary where it becomes an artifact. Anything that leaves those two paths open is advice again.

## When it fires

Reach for this **before** writing a decision anywhere — not after, and not only when asked. The trigger is the shape of the thing, not the shape of the request:

- A finding, defect, audit result or review comment that looks like the operator's to rule on.
- A blocker, a deferral, or anything about to be described as parked, registered, awaiting a word, or not-work-yet. Those are dispositions; a disposition needs a grade behind it.
- An explicit ask — "show this as an operator decision", "present it as an OD". **The ask names the form, never the routing.** If the gate grades it at `moderate` or below with no operator-only category, the answer to that ask is the executed change plus the record as its receipt.
- A turn about to end by handing something over.

It does **not** fire for a routine call the session owns — ceremony tier, ordering, placement, naming. Those are decided in one line and the work continues.

## The cycle (follow in order)

### 0. The rule must exist in this project

Find the constitution — `AGENTS.md`, `docs/AGENTS.md`, or the methodology document — and read its operator-decision section **in full, now, before reasoning about the case**. Re-deriving it from memory each turn is how a session ends up flipping its own answer between turns.

If the project has no such section, this skill has nothing to apply. Author it first — `/sdd-generators:constitution` owns that document — and say plainly that it did not exist. The hooks are inert until it does, by design.

What the section must fix, for the rest of this cycle to mean anything: what counts as an operator decision; the gate; the grade words and the line above which the operator decides; the categories that are the operator's at every grade; the record's fields; and where a record lands.

### 1. Verify the cause AND the remedy at source

Both. By **something other than the pass that produced them** — a session cannot discharge this against its own reasoning, which is the entire point of the clause. A separate agent, a fresh read, a probe, a measurement.

An unverified recommendation is not presented. It is verified first, and if it cannot be, that is the finding.

### 2. Run the panel

    Workflow({ name: "sdd-generators:od-gate", args: [ … ] })

Three lenses per finding — cause, remedy, ownership — each briefed to refute, then a synthesiser, then one critic across the whole set. `4N + 1` agents, so pass few items and batch related ones into one run rather than several.

Each item is either an issue number or `{ key, title, brief }` with the finding stated in full. When the corpus or the code lives outside the working directory, pass `{ items, corpus, code }` instead of a bare array.

The panel exists because a single verifier checks whether a finding is real and does **not** check whether the reason given for handing it over is real. Both recorded escapes were of the second kind: a cited document that did not say what it was cited for, and an operator ruling quoted as binding that turned out conditional with its condition already discharged.

Its output is evidence, not a verdict. Where the critic and a record disagree, settle it at the source yourself.

### 3. Grade, then route

Grade the change **whole** — what it costs to make and how far it reaches — with the constitution's one word.

- **At `moderate` or below, with none of the operator-only categories touched: execute it.** Then write the record as the receipt. Presenting it instead is the failure this skill exists to prevent; it costs the operator time he did not owe.
- **Above that line, or any operator-only category touched: it is the operator's.** Present the record and stop.

Assign a category only when you can **quote the corpus sentence** that makes it one, and argue the opposite case before landing. Claiming a category that does not hold blocks work on the operator for nothing; claiming `none` where one holds authorises a session to act where it must not.

There is no third state. "Registered, awaiting his word" is not a disposition — it is an ungrounded grade claim wearing a hedge.

For the security category specifically, the test is **what becomes reachable**, not what some closure clause reaches. A change that adds no reachability is not a security decision merely because it touches security-adjacent code.

### 4. Write the record where the work it governs lands

The record's shape is the same whether it asks or reports — the constitution fixes the fields; do not invent a shorter form for the reporting direction, which is the direction that gets cut.

Where it lands is the constitution's routing sentence, not a preference: a decision that changes something rides the pull request or commit carrying the change; a decision that changes nothing — a KEEP, a deferral, a finding left unscheduled — goes on the tracker thread of the issue it concerns; a decision that changes a spec's phase set goes in that spec's revision log. **The grade decides WHO decides, never WHETHER it is written down.**

## What the hooks refuse

This plugin ships two hooks. Both are inert in a project whose constitution has no operator-decision section, so they cost nothing where the rule was never adopted.

- **On a tracker write** (`gh issue|pr create|comment`) that files a defect, claims the operator owns something, or already carries a grade: the write is blocked unless it carries a grade, at least two `file:line` anchors — the cause and the remedy are two places — and names the panel it went through. A grade of `n/a` records a decision taken elsewhere and owes the anchors but not the panel.
- **At the end of a turn** that hands the operator a decision, or states a grade above the line: the turn does not end without the record. A grade inside a sentence is not the record.

A hook firing is information, not an obstacle: it means the gate was skipped. Satisfy it by running the cycle, never by rewording the text until the pattern stops matching.

## Rules

- The record is written inline, as the block. Never a popup, never a question widget, never prose that describes a decision without carrying its fields.
- **A finding is not work.** Reporting a defect never authorises fixing it, and this cycle does not widen into execution: verification verifies. The one exception is step 3's own routing, which is the rule's instruction, not a session's initiative.
- Incidental defects noticed on the way get one line each under "Incidental, not scheduled". They do not join the change set.
- Batch related findings into one panel run. Interactions between remedies are a question only the critic can answer, and it can only answer it for records it sees together.
- Artifacts are English, whatever language the conversation uses.
