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
- An explicit ask — "show this as an operator decision", "present it as an OD". **The ask names the form, never the routing.** Where the constitution's own line leaves the change with the session, the answer to that ask is the executed change plus the record as its receipt.
- A turn about to end by handing something over.

It does **not** fire for a routine call the session owns — ceremony tier, ordering, placement, naming. Those are decided in one line and the work continues.

## The cycle (follow in order)

### 0. The rule must exist in this project

Find the constitution — `AGENTS.md`, `docs/AGENTS.md`, `CLAUDE.md`, or the methodology document — and read its operator-decision section **in full, now, before reasoning about the case**. Re-deriving it from memory each turn is how a session ends up flipping its own answer between turns.

What the section must fix, for the rest of this cycle to mean anything: what counts as an operator decision; the gate; the grade words; the line above which the operator decides; the categories that are the operator's at every grade; the record's fields; and where a record lands.

#### What the hooks' parser needs on top of that

The seven items above are what the *rule* must settle. Two of them are also read by machine, so their spelling is this plugin's contract and is stated here because the parser is here:

- **The sentence that introduces the grade scale** carries every grade word in backticks, in order, cheapest first, and carries no other backticked word.
- **The sentence that draws the line** names one of those same words, spelled the same way.

Where that parse fails the hooks do not guess: a grade label with any value satisfies them and the above-the-line test is skipped entirely — the project reads as gated and is barely gated. So confirm the parse rather than assuming it, with the command at the end of this step.

#### Install the rule (first run only)

If the project has no such section, this skill has nothing to apply. Say so plainly, improvise no rule, and do not hand the case over as though it were covered — there is no rule yet under which it could be. Two ways to get one:

- **An interview authors it** — `/sdd-generators:constitution`, in the `sdd-generators` plugin of this same marketplace, has an **operator-decisions stage** that asks for every item above and an `AGENTS.md` template that renders them in the shape the parser reads. It is a **separate install** (`/plugin install sdd-generators@mcardia-claude-kit`); this plugin never authors the section, because two authors for one fact is the drift the kit exists to prevent. With no constitution yet, run that command whole — the stage sits after the review process. With a constitution that predates the stage, run the stage alone and add what it produces to the existing document in that document's own heading style and numbering.
- **Or it is written by hand** — the seven items above are what it must settle, and the two bullets above are how the two machine-read sentences must be spelled. Heading it `## Operator decisions` (numbered or not) is what the hooks look for.

Author neither the interview's questions nor the section itself here. Both belong to the `constitution` skill, in the other plugin; a second copy in this file would diverge from the first the day either one changes.

Declining is an answer. A project that does not want the discipline writes no section, and nothing below ever fires — not a gap, and not something to argue anyone out of. To see which it is:

    python3 "$CLAUDE_PLUGIN_ROOT/hooks/check-od-record.py" --explain .

names the constitution the walk resolved and the vocabulary parsed out of it, or reports the project ungated and lists the filenames it looked for.

### 1. Verify the cause AND the remedy at source

Both. By **something other than the pass that produced them** — a session cannot discharge this against its own reasoning, which is the entire point of the clause. A separate agent, a fresh read, a probe, a measurement.

An unverified recommendation is not presented. It is verified first, and if it cannot be, that is the finding.

### 2. Run the panel

    Workflow({ name: "operator-decision-gate:od-gate", args: [ … ] })

Three lenses per finding — cause, remedy, ownership — each briefed to refute, then a synthesiser, then one critic across the whole set. `4N + 1` agents, so pass few items and batch related ones into one run rather than several.

Each item is either an issue number or `{ key, title, brief }` with the finding stated in full. When the corpus or the code lives outside the working directory, pass `{ items, corpus, code }` instead of a bare array.

The panel exists because a single verifier checks whether a finding is real and does **not** check whether the reason given for handing it over is real. Both recorded escapes were of the second kind: a cited document that did not say what it was cited for, and an operator ruling quoted as binding that turned out conditional with its condition already discharged.

Its output is evidence, not a verdict. Where the critic and a record disagree, settle it at the source yourself.

### 3. Grade, then route

Grade the change in the constitution's own word, weighing it the way that section says to weigh it. Then route by what the section says — it draws a line, and it names the categories that are the operator's whatever the grade. Read both there, in the text, this turn. Two outcomes, and only two:

- **The section leaves it with the session** — execute it, then write the record as the receipt. Presenting it instead is the failure this skill exists to prevent; it costs the operator time he did not owe.
- **The section leaves it with the operator** — present the record and stop.

Which of the two holds is the `od-lens` **ownership** lens's question, and that lens is defined in the agent file. Take its answer as evidence and settle it at the constitution yourself.

### 4. Write the record where the work it governs lands

The record's shape is the same whether it asks or reports — the constitution fixes the fields; do not invent a shorter form for the reporting direction, which is the direction that gets cut.

Where it lands is the constitution's routing sentence, read there and applied literally rather than by preference. **The grade decides WHO decides, never WHETHER it is written down.**

## The form the record takes

The cycle above settles what the record contains. This is how the finished block reaches a person, and it is not polish: a block that cannot be answered from the top is answered late or not at all, and a receipt shaped like a question costs the operator a reply he did not owe.

**How each field is WRITTEN belongs to the `od-lens` agent.** Its synthesis role defines the reachable-scenario rule for the standing field, the executable-recommendation rule, and the quote-the-corpus rule behind a reserved category. Read them there; none of them is restated here. What follows is only the shape of the block.

**Order it for a decision, not for a review.** The reader opens the block to answer something, not to audit a chain of reasoning. So: what is being decided, then what the reader would observe, then why it stands that way, then the recommendation. Reasoning supports the recommendation; it never precedes the question.

**Options go inline, in the block.** Never a question widget, never a popup, never a separate round trip that costs a turn. Where there are two or three ways to go, each gets its real shape — the screen the reader would see, the command they would run, the files that move — never an abstract label. "Option A: refactor" is not an option, it is a category.

**One block, in the constitution's own field labels and in the conversation's language.** This plugin does not name the fields; the constitution does. Render what it declares, in the order it declares.

**The two directions differ in emphasis, not in shape.** Step 4 fixes the fields; what moves is where the block puts its weight. Asking: the recommendation is a proposal, the choice is live, and the block ends with that choice. Reporting: those same fields are a receipt for something already done, and the block ends with what was done and where it landed. A receipt dressed as a question is the commonest way this breaks in the reporting direction — "shall I proceed?" written under a change already made re-opens a decision the constitution's own line had settled.

**Never a bare grade in a sentence in place of the block.** "This one is minor, so I went ahead" carries a grade and is not a record. The block is what lands, in both directions.

### Two worked examples

Both write the field labels as `<…>` placeholders, because the plugin does not name the fields. Substitute whatever the constitution declares.

**Asking — a CHANGE handed over.**

> **\<label: what is being decided\>** — whether the CSV export keeps returning every column to a viewer-role user.
>
> **\<label: how things stand\>** — a viewer opens Reports → Export on the shared account and downloads a file whose last four columns are the salary fields that same account cannot see anywhere in the UI.
>
> **\<label: why it stands that way\>** — the exporter serialises the row struct rather than the view model: `internal/export/csv.go:88` takes `*model.Employee`, and `internal/http/reports.go:212` hands it the unfiltered record.
>
> **\<label: the recommendation\>** — CHANGE. Two ways, and they are different products:
>
> - **Filter at the serialiser.** `csv.go:88` takes the view model. A viewer's file loses four columns; every other role's file is byte-identical to today's. One file, no API change.
> - **Refuse the export to viewers.** `reports.go:212` returns 403 for that role and the Export button goes with it, so a viewer sees no button rather than a shorter file. Two files, plus a string for the empty state.
>
> **\<label: the grade\>** — \<the constitution's word for a change of this reach\>, which its line puts on the operator's side.
>
> **\<label: where verified\>** — `internal/export/csv.go:88`, `internal/http/reports.go:212`; od-gate panel, three lenses and a critic.
>
> Yours: the serialiser, the 403, or neither.

**Reporting — a KEEP, as a receipt.**

> **\<label: what is being decided\>** — whether the webhook sender's retry budget moves off 3.
>
> **\<label: how things stand\>** — a customer whose endpoint is down for four minutes sees one failed delivery and no retry row; the next attempt is the next event, hours later.
>
> **\<label: why it stands that way\>** — the budget is per request, not per endpoint: `internal/webhook/sender.go:54` resets it on every call.
>
> **\<label: the recommendation\>** — KEEP. A bigger number moves the failure later without removing it; what removes it is the per-endpoint backoff `docs/adr-019.md:22` already schedules.
>
> **\<label: the grade\>** — \<the constitution's word for a change of this reach\>, which its line leaves with the session. Executed as KEEP: nothing changed, and the finding is closed against ADR-019.
>
> **\<label: where verified\>** — `internal/webhook/sender.go:54`, `docs/adr-019.md:22`; od-gate panel.

## What the hooks refuse

This plugin ships two hooks. Both refuse nothing in a project whose constitution has no operator-decision section — though each is still a `python3` process, about 17 ms on every Bash call and every turn end, adopted or not.

- **On a tracker write** (`gh issue|pr create|comment|edit|close|review`, and `gh api` with a body) that files a defect, claims the operator owns something, or already carries a grade: the write is blocked unless it carries a grade in the constitution's own words, at least two `file:line` anchors — the cause and the remedy are two places — and names the panel it went through. A grade of `n/a` records a decision taken elsewhere and owes the anchors but not the panel.
- **At the end of a turn** that hands the operator a decision, or states a grade above the line the constitution draws: the turn does not end without the record. A grade inside a sentence is not the record.

A hook firing is information, not an obstacle: it means the gate was skipped. Satisfy it by running the cycle, never by rewording the text until the pattern stops matching.

## Rules

- Batch related findings into one panel run. Interactions between remedies are a question only the critic can answer, and it can only answer it for records it sees together.
- Artifacts are English, whatever language the conversation uses.
