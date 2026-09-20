# autonomy-grant-gate

A turn ends when the assistant stops calling tools. So when the operator has said
"continue autonomously" and gone away, **naming the next step and stopping IS stopping**
— and he finds out only by coming back. This plugin ships one `Stop` hook that refuses a
turn which ends without declaring its own state, and only while such a grant is active.

It has no command, no agent and no skill. One hook, one calibration script, one suite.

## The finding this plugin exists to carry

**The mechanism is a form check, not a predicate.** Three mechanical predicates were
measured against 45 transcripts and 2,358 turn-ends before the form was chosen:

| predicate | fired on the five real stops |
|---|---|
| the message declares a unit of work complete | 1 of 5 |
| nothing is running that will re-invoke the session | 0 of 5 |
| the turn made no tool call at all | 0 of 5 |

Every one of those five turns had done substantial work first — the last made 117 tool
calls — and then stopped where more was available. **There is no mechanical signature for
"more was available."** So the hook does what this kit's operator-decision gate already
does for a decision it also cannot judge: it cannot check the truth, so it checks the
FORM, and the form makes the omission visible. Writing `STOPPED: queue empty` three lines
above a to-do list naming the next task is a lie that has to be typed on purpose, which
is a far higher bar than drifting into a closing report.

The next person to touch the hook will reach for a predicate. Those numbers are what
should stop them, and they are in the file's own docstring for that reason.

## What it refuses

Exit 2, message on stderr, when **both** hold:

1. **A continuous grant is active** in this session — read out of the transcript, never
   out of the assistant's own prose.
2. **The turn's final assistant message carries no state line.**

**The grant is standing.** It binds from the message that gives it until the session
ends. Re-evaluating it against the operator's later sentences was measured and missed
four of the five stops: he gives the grant once, then answers questions, and an expiring
reading disarms the gate at the first answer.

Only what the human typed counts. Tool results, `isMeta` harness records, compaction
summaries and sidechain records are skipped whole; the harness envelopes a real message
can carry — `<system-reminder>`, `<task-notification>`, `<bash-input>`, a slash command's
`<command-message>` — are stripped before the phrases are matched, rather than
disqualifying the record that carries them, because the session's first real message
usually has a reminder appended to it. The `isMeta` skip is load-bearing: this hook's own
refusal is fed back into the transcript as an `isMeta` user record, so without it a gate
whose wording quoted a grant phrase would arm itself.

## The state line

One line, anywhere in the final message:

```
IN FLIGHT: <what is running that will re-invoke this session>
EM VOO:    <o que está rodando e vai me chamar de volta>

STOPPED: <queue empty | red gate | operator decision | question>
PARADO:  <fila vazia | gate vermelho | decisão sua | pergunta>
```

An in-flight rest is free text — it names the thing, and no closed set can. **A stopped
rest must name one of the configured reasons**, because an open reason field is an
exemption the writer issues to itself.

**`queue empty` is not an assertible exit, and the refusal says so.** It is discharged by
an ACTION in the same turn — reading whatever the project uses to decide what comes next
— and never by the claim. An exemption satisfied by a sentence the assistant writes for
the gate is a self-issued exemption.

The vocabulary is bilingual because the operator this was built for writes chat in
pt-BR. It is a vocabulary, not prose; everything else this repository ships is English.

## Configuration, and a deliberate departure from the sibling

`operator-decision-gate` ships **no rule**: it parses every word it enforces out of the
consuming project's own constitution, and refuses nothing in a project that has no
operator-decision section. **This plugin cannot do that, and does not pretend to.** A
grant is a conversational act — the operator types a sentence and walks away. No corpus
section declares it, so there is nothing to parse and no opt-in to detect. Two
consequences follow, and both are departures worth naming:

- **It ships defaults.** Words this plugin chose, not a project's.
- **It has no project scope.** It applies wherever it is installed. It is self-limiting
  in practice rather than by predicate: in a project where nobody grants autonomy, it
  never fires. The cost of being installed there is not zero, and is stated below.

An optional override replaces those words. Put it at `.claude/autonomy-grant.json` in the
project root — the hook looks for it in the working directory and its ancestors, stopping
below `$HOME` so that one file in a home directory cannot silently re-word the gate in
every project on the machine:

```json
{
  "grant_phrases": ["continue autonom", "luz verde"],
  "in_flight_prefixes": ["IN FLIGHT", "EM VOO"],
  "stopped_prefixes": ["STOPPED", "PARADO"],
  "stop_reasons": ["queue empty", "red gate", "operator decision", "question"]
}
```

Entries are **literal substrings, matched case-insensitively** — not regular
expressions. A project writes this file by hand; a bad pattern would take the hook down
or hang it, and none of the phrases that were actually measured need alternation. List
accented and unaccented spellings separately.

**Each key REPLACES the default list rather than merging with it**, and a key you leave
out keeps its default. Replacement is what lets a project drop a default phrase that
misfires for it; a merge it cannot turn off is a default it cannot escape. A malformed
file, or a key of the wrong shape, falls back to the defaults **and says so on stderr**
rather than failing open in silence.

### Why the defaults lean toward arming

Every default grant phrase either contains `autonom` — which is what makes a sentence a
grant rather than an instruction — or was measured as a whole message the operator sent.
Nothing else is guessed. Two of them are known to over-match, and both are kept
deliberately, because the asymmetry is the whole point: **a false arm costs one line of
text; a missed grant costs the wait the gate exists to prevent.**

- `continuar autonom` fires on a question — *"consegue continuar autonomamente?"*,
  measured four times. A turn that answers that question by declaring its state is
  answering it correctly.
- `pode seguir` is the loosest default: measured five times, four of them real grants and
  one a narrow instruction (*"pode seguir e apagar"*). It is the first entry a project
  should drop through the override if it reads Portuguese and finds it noisy.

## Arming it: the calibration script

Never trust the gate in a project before running this against that project's transcripts:

```sh
python3 <plugin>/hooks/calibrate.py -p /path/to/project ~/.claude/projects/<slug>/
```

It prints the vocabulary in force and five numbers:

```
transcripts scanned
turn-ends
turn-ends under an active grant
  ... of those, lacking a state line    <- what the gate would have refused
fires with no grant active              <- MUST BE 0
```

**The last number is the control.** It is counted against an independent reading: the
walk decides the grant incrementally, turn-end by turn-end, the way the standing rule
works; the control re-decides it per file with the hook's own whole-file predicate, the
one production runs. A fire landing in a file that predicate calls ungranted means the
two disagree — **the grant parser is wrong and the gate is not armed**, whatever the
other four numbers say. The script exits non-zero and says so.

**It self-checks before it prints anything, and prints nothing but the failure if a
control is off.** The measurement this gate was designed from was confidently wrong
twice: once because it looked for a task-notification id inside the `message` object when
the id lives outside it, once because it treated the grant as expiring. Both runs
produced confident numbers and neither looked wrong. So the script asserts nine synthetic
controls whose answers are known, plus an ungranted control population of twenty
turn-ends — through the real hook as a subprocess, as well as in process — before it
reads a single real transcript. A harness that cannot assert its own control is worth
nothing.

It re-implements none of the gate: every predicate it uses is imported from
`check-grant-stop.py`, so its numbers cannot drift from what the hook does. The
subprocess controls are what prove the import and the executable agree.

## What this plugin does NOT claim

- **It has almost no evidence of prevention.** The rule has been live in one project for
  hours. What stands behind it is the design plus 2,358 turn-ends of *negative*
  measurement — the three predicates that do not work — and a positive control after the
  fact: replayed over the same transcripts, the gate would have fired on 5 of the 6 turns
  the operator actually complained about, the sixth being a turn before he had granted
  anything in that session. That is not measured prevention. Nothing here should be read
  as a rate.
- **It is a one-shot nudge, not enforcement.** `stop_hook_active` passes the retry
  unconditionally, so the gate costs a determined stopper exactly one extra sentence. It
  cannot make a session keep working; it can make the decision to stop explicit.
- **It cannot see a grant that is not in the transcript.** A session resumed into a fresh
  transcript, or one whose grant survives only inside a compaction summary, reads as
  ungranted — the summary is the model's prose, and this gate never reads the assistant's
  prose for the grant. The gate stays inert there until the operator says it again.
- **It costs a `python3` process on every turn end, in every project where it is
  installed, grant or no grant.** Measured on this machine (Python 3.14, median of 15
  subprocess runs, against an interpreter-startup floor of 8.1 ms):

  | case | cost |
  |---|---|
  | the turn carries a state line and the host supplied `last_assistant_message` | **14.9 ms** — the transcript is never opened |
  | small transcript, full scan | 14.9 ms |
  | median 2.71 MB transcript, full scan | 27.2 ms |
  | largest 36.5 MB transcript, full scan | 152.8 ms |

  Proving a grant ABSENT means reading every record, so the scan is unavoidable in a
  project that never adopts the vocabulary. What removes it where the plugin IS adopted
  is checking the state line first: a compliant turn never opens the file. **The obvious
  further optimisation is measured and refused** — a cheap regex prefilter over each raw
  line before paying for `json.loads` is **14x slower** (1,998 ms against 141 ms in
  process, interleaved in one run), because `json.loads` runs at C speed over the whole
  line while the regex pays for case-folding and alternation over 36 MB of text the
  parser would have discarded.

## Tests

```sh
python3 plugins/autonomy-grant-gate/hooks/test_hooks.py
```

Each case runs the real hook as a subprocess with a real JSON payload on stdin against a
real temporary transcript, and asserts the exit code. Nothing is mocked.

**A case that expects 0 says why in its name** — `(compliant)` for a turn that carries
the line, `(no grant)` for a turn the gate correctly ignores, `(one-shot)` for a retry
the gate has already spoken about. A suite that spelled all three the same way would read
as closed when it is not.

`claude plugin validate` reads manifests; it does not run anything. This hook is
executable code that REFUSES turn-ends, so a regression here does not raise an error —
the gate quietly stops guarding, in every project that installed it.

## Why this is a plugin of its own

The cheaper answers, named and refused in writing, because this kit's discipline is to
put the enumeration in the deliverable rather than to have weighed it privately.

1. **Accept it.** Let the rule live as prose — in a memory file, in a constitution, in
   the session's instructions. Refused by evidence, not by preference: it *was* prose, in
   exactly those places, through five stops in two days, three of them explicit
   complaints and the last a 35-minute wait.
2. **Make the case unreachable.** There is no surface. The failure is a session deciding
   that a report is a turn's proper end: no button to remove, no default to flip.
3. **One line in something that already exists.** The nearest existing thing is
   `operator-decision-gate`'s Stop hook, and folding this in would weld two unrelated
   rules to one boundary and put a rule with *no* project scope inside a plugin whose
   entire design is that it has one. The prototype this generalises from did exactly that
   — two rules in one file, hard-scoped to one project's path — and its hard-coded root
   is why it could not be installed anywhere else.
4. **A new mechanism.** One hook, one calibration script, one suite, this page. **This is
   the tier shipped, and it is tier 4.**

What the separation buys: a project can take the operator-decision gate without paying
for a transcript scan on every turn end, or take this one without adopting an
operator-decision section it does not have; and each release states its own blast radius
instead of one version number covering two rules that fire at the same boundary.
