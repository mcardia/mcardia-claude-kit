# operator-decision-gate

Applies and enforces a project's **own** rule about which decisions belong to one person
— the operator, the owner, the tech lead — and which the working session settles itself.

The rule is never this plugin's. It lives in the consuming project's constitution, and
every component here reads it there on every run. What this plugin adds is the procedure
that makes the rule bind: a verification pass a session cannot perform on itself, an
adversarial panel, a record whose shape is checked, and two hooks that refuse a handover
arriving without one.

**A project adopts the discipline by having the section in its constitution, and by
nothing else** — no flag, no settings entry, no second file to drift. Install this plugin
in a project whose constitution has no operator-decision section and it refuses nothing.

## Command

| Command | Produces | Role |
|---|---|---|
| `/operator-decision-gate:od` | an operator-decision record | verify cause and remedy at source → adversarial panel → grade → execute it or hand it over, as one fixed record either way |

It is the one skill in this marketplace that may fire on its own, because the failure it
prevents is a session that never thought to invoke it.

## Where the section comes from

This plugin **reads** the operator-decision section and never writes it. The interview
that writes it is `/sdd-generators:constitution`, in the `sdd-generators` plugin of this
same marketplace — a **separate install**:

```sh
/plugin install sdd-generators@mcardia-claude-kit
```

Its operator-decisions stage collects the whole rule and renders it through an `AGENTS.md`
template. Two authors for one fact is the drift this kit exists to prevent, so the
template lives there and this plugin carries no copy of it.

You do not need that plugin. A section written by hand works identically, and the
`/operator-decision-gate:od` skill states what it must settle and how its two
machine-read sentences must be spelled — the grade scale in backticks, cheapest first,
and a line sentence naming one of those same words. What you lose by hand-writing it is
the interview, not the enforcement.

## Registered agent

- **`od-lens`** — the adversarial examiner behind the command: the cause, remedy and
  ownership lenses, the synthesis role that writes the record, and the critic role that
  reads a whole set of records at once. It is the authority on what its own lenses mean;
  the skill and the workflow name a lens and never restate it, so there is one definition
  to keep true. It pins its effort in its definition and does not pin a model, because
  what a fleet of agents costs is the operator's call, not the plugin's.

## Registered workflow

**`od-gate`** runs the operator-decision panel: three lenses per finding, a synthesiser,
then one critic across the set — `4N + 1` agents. It is saved as a workflow rather than
re-authored per use because the cheapest path has to be the correct one, or it loses to
the shortcut. `/operator-decision-gate:od` invokes it as
`Workflow({ name: "operator-decision-gate:od-gate", args: [ … ] })`; you can also run it
directly on a list of issue numbers.

## Registered hooks

Two, and they are why the operator-decision rule binds instead of advising:

- **On a tracker write** that files a defect, claims the operator owns something, or
  already carries a grade — the write is refused unless it carries a grade, two
  `file:line` anchors (cause and remedy are two places), and the panel it went through.
- **At the end of a turn** that hands the operator a decision, or states a grade the
  constitution puts above its own line — the turn does not end without the record.

**Both read the rule out of the project's own constitution, and refuse nothing in a
project whose constitution has no operator-decision section.** They walk up from the
working directory looking for one — stopping below `$HOME`, because a `CLAUDE.md` in the
home directory is a person's standing instructions and not a project's constitution — and
finding none, they do nothing. That predicate is deliberate: a plugin's hooks load in
*every* project, and a gate that refused ordinary work in repositories which never
adopted the rule would be a gate people switch off.

Inert is not free. Each hook is a `python3` process: **about 17 ms on every Bash call and
every turn end, in every project, adopted or not.** The Stop hook uses the
`last_assistant_message` the host supplies rather than re-reading the transcript, which on
a 35.4 MB transcript is 17 ms instead of 66 ms.

### Is this project gated, and by what?

```sh
python3 <this plugin's root>/hooks/check-od-record.py --explain [DIR]
```

Prints the constitution the walk resolved, the grade vocabulary parsed out of it and the
threshold word, or says `INERT` and lists the filenames it looked for. It is the only way
to see what the vocabulary parser actually read — and worth running once per project,
because a section whose scale sentence the parser could not read still reports the
project ACTIVE while accepting any grade value and skipping the above-the-line test.

`hooks/test_hooks.py` ships inside the installed payload too. It never runs on its own; it
is there so that running it proves the *installed* copy behaves, not only the one in this
repository. One group of its cases reads the `constitution` generator's template out of
the sibling plugin, and looks for it on both layouts — beside this plugin in the
repository, and under the marketplace's cache directory, through the version segment,
once installed. Where the sibling is on neither path — this plugin installs alone — that
group prints the paths it tried and the rest still reports.

### What the hooks cannot see

They read a command string; they do not run a shell. Two classes of write are therefore
invisible to them, and no amount of pattern work closes either:

- **A wrapper that takes its own arguments** — `timeout 60 gh …`, `xargs gh …`,
  `bash -c "gh …"`. (`/usr/bin/gh` and `GH_TOKEN=x gh …` *are* handled: both are lexical.)
- **A body the shell expands** — `--body "$(cat record.md)"`, `--body "$VAR"`. The hook
  sees the literal `$(cat record.md)`.

The honest claim is not that the gate cannot be bypassed. It is that it makes the correct
path the cheap one and makes skipping it visible.

## Why this is a plugin and not project policy

**What the plugin reads, and what it states.** The rule is the constitution's: what counts
as a decision, the grade words, the line those words are measured against, which
categories are the operator's at every grade, the record's fields, and where a record
lands. `/operator-decision-gate:od` reads them there every run, and the hooks *parse* the
grade words and the threshold out of that same section rather than carrying a copy —
which is why a project grading `trivial|small|large|sweeping` is gated in its own
vocabulary and never asked for another's. Where that parse fails, the hooks fall back to
"a grade label carries some value" and skip the threshold test entirely, rather than
guessing.

Four things ARE the plugin's, and are named here so they are not mistaken for yours: the
adversarial panel; **two distinct `file:line` anchors** as the operational test that a
cause and a remedy were both verified; `grade: n/a` as the spelling for a record of a
decision taken elsewhere; and the **four-rung sizing ladder** the `od-lens` remedy lens
prices a fix against — used only where your constitution states no sizing policy of its
own, and reported as the plugin's whenever it is used. None of the four is in anybody's
constitution. They are how a text gate checks a sentence that is.

## Why this is a plugin of its own

The cheaper options, named and refused, because this kit's discipline is to write them
down rather than to have weighed them privately. It is the same four-rung ladder the
`od-lens` remedy lens prices a fix against, turned on this component.

1. **Accept it** — leave the rule as prose in each project's constitution and trust a
   session to follow it. Refused by evidence rather than by preference: it *was* prose,
   in the constitution and in a memory file, and it still lost to a more specific
   competing instruction in the same context window. The operator's words for that
   state: *"memory and AGENTS.md are not working."*

2. **Make the case unreachable** — change the surface so the mistake cannot be made.
   There is no surface. The failure is in how a session routes a decision it has already
   understood: no button to remove, no default to flip, no screen anyone touches.

3. **One thing in something that already exists** — the cheapest shape that could work
   is a skill, and a skill is advice. The recorded failure is a session reading the rule
   and routing past it anyway, so more text at the same authority level changes nothing.
   What closes it is a refusal at the boundary where a decision becomes an artifact; a
   refusal needs a hook; a hook that must not fire in projects which never adopted the
   rule needs a parser for each project's own grade vocabulary; and a parser that decides
   whether work is blocked needs tests. Tier 3 does not reach the case.

4. **A new mechanism** — a skill, an agent, a workflow, two hooks and their test suite:
   over two thousand lines across eight files, the large majority of them executable, and
   this repository's first executable code of any kind. **This is the tier shipped, and
   it is tier 4.**

**A fifth answer, refused on the record: tier 4 filed inside tier 3's home.** All of the
above first shipped inside `sdd-generators`, on the argument that a second install, a
second version to track and a second USAGE would buy nothing for a rule belonging to a
discipline that plugin already served. That label was wrong, and it is corrected here
rather than quietly dropped, because a ladder whose conclusion can be reached by filing
is not a ladder. Filing a new mechanism beside an existing one does not make it an
increment to it — and the enumeration refuted its own placement in the same breath it
argued for it, in the sentence *sharing a version number does not make a new mechanism a
small one.*

What the separation buys, which the refused answer said was nothing:

- **Install the generators without the gate.** Two `python3` processes stop running on
  every Bash call and every turn end in projects that wanted eight interview skills and
  no enforcement boundary. Inert was never free, and under one plugin it was not optional
  either.
- **Install the gate without the generators.** A project that already has a constitution
  takes the enforcement without eight interview skills in its context.
- **A version number that says what changed.** One number for two products means a
  generator fix also ships new hook code into the path of every Bash call, and a gate fix
  re-releases the generators. Split, each release states its own blast radius.
