#!/usr/bin/env python3
"""Stop gate: under a continuous autonomy grant, a turn declares its own state.

A turn ends when the assistant stops calling tools. So when the operator has
said "continue autonomously" and gone away, naming the next step and stopping
IS stopping — and he finds out only by coming back. The rule was born from
five such stops in one project across two days, three of them explicit
complaints, the last a 35-minute wait.

THE MECHANISM IS A FORM CHECK, NOT A PREDICATE, AND THAT IS THE FINDING THIS
FILE CARRIES. Three mechanical predicates were measured against 45 transcripts
and 2,358 turn-ends before the form was chosen:

    predicate                                        fired on the five
                                                     real stops
    ---------------------------------------------    -----------------
    the message declares a unit of work complete     1 of 5
    nothing is running that will re-invoke the       0 of 5
      session
    the turn made no tool call at all                0 of 5

Every one of those five turns had done substantial work first — the last made
117 tool calls — and then stopped where more was available. THERE IS NO
MECHANICAL SIGNATURE FOR "MORE WAS AVAILABLE". So this hook does what the
kit's operator-decision gate already does for a decision it also cannot judge:
it cannot check the truth, so it checks the FORM, and the form makes the
omission visible. Writing "queue empty" three lines above a to-do list naming
the next task is a lie that has to be typed on purpose, which is a far higher
bar than drifting into a closing report.

The next person to touch this file will reach for a predicate. The numbers
above are what should stop them.

WHAT IT REFUSES. Exit 2, message on stderr, when BOTH hold:

  1. a continuous grant is active in this session, read out of the transcript
     and never out of the assistant's own prose; and
  2. the turn's final assistant message carries no state line.

THE GRANT IS STANDING. It binds from the message that gives it until the
session ends. Re-evaluating it against the operator's later sentences was
measured and missed four of the five stops: he gives the grant once, then
answers questions, and an expiring reading disarms the gate at the first
answer.

WHAT IS AND IS NOT THE OPERATOR SPEAKING. Only records the human typed count.
Tool results, `isMeta` harness records, compaction summaries and sidechain
records are skipped whole, and the harness envelopes a real message can carry
(`<system-reminder>`, `<task-notification>`, `<bash-input>`, a slash command's
`<command-message>`, …) are STRIPPED before the phrases are matched, rather
than disqualifying the record that carries them — the session's first real
message usually has a reminder appended to it.

The `isMeta` skip is load-bearing rather than tidy: this hook's own refusal is
fed back into the transcript as an `isMeta` user record, so without it a gate
whose refusal text quoted a grant phrase would arm itself.

COST, AND A MEASUREMENT THAT CONTRADICTS THE OBVIOUS FIX. Deciding (1) means
reading the whole transcript when no grant is there to find. On this estate's
largest transcript — 36.5 MB, 54k records — that scan is ~141 ms in process,
~153 ms as the process the harness actually starts; a median 2.71 MB
transcript is ~27 ms, and the floor is ~15 ms. The obvious optimisation is a
cheap regex prefilter over each raw line before paying for `json.loads`.
MEASURED, INTERLEAVED, IT IS 14x SLOWER: 1,998 ms against 141 ms, because
`json.loads` runs at C speed over the whole line while the regex pays for
case-folding and alternation over 36 MB of text the parser would have thrown
away. What is done instead costs nothing and cannot regress: the state line is
checked FIRST when the host hands us `last_assistant_message`, so a turn that
carries the line never opens the transcript at all.

LOOP-SAFE, AND HONEST ABOUT WHAT THAT COSTS. `stop_hook_active` passes the
retry unconditionally, so the gate costs a determined stopper exactly one
extra sentence. It is a one-shot nudge, not enforcement.

NO PROJECT SCOPE. Unlike this kit's operator-decision gate, which asks a
project's constitution whether it adopted the rule, a grant is a
conversational act and no corpus section declares it. So this hook applies
wherever it is installed and is self-limiting in practice: in a project where
the operator never gives a grant, it never fires. The vocabulary — the grant
phrases, the state prefixes, the closed set of stop reasons — ships as a
default and is replaced, per key, by an optional `.claude/autonomy-grant.json`
in the project.
"""
import json
import os
import re
import sys

# ------------------------------------------------------------- vocabulary ---
# Entries are LITERAL substrings, matched case-insensitively. Not regexes: a
# project writes this file by hand, a bad pattern would take the hook down or
# hang it, and the phrases that were actually measured need no alternation.
# Accented and unaccented spellings are listed separately for the same reason.

# Every default here either contains `autonom` in one of its spellings — which
# is what makes a phrase a grant rather than an instruction — or was measured
# as a whole message the operator sent in this estate's 45 transcripts.
# Nothing else is guessed. Two are known to over-match and are kept anyway,
# because the asymmetry is the point: a false arm costs one line of text, and
# a missed grant costs the wait this gate exists to prevent.
DEFAULT_GRANT_PHRASES = (
    "continue autonom",      # continue autonomously / autonomamente / autonoma
    "continuar autonom",     # also fires on "consegue continuar autonomamente?"
    "continua autonom",
    "de forma autonom",      # continue o desenvolvimento DE FORMA AUTONOMA
    "de forma autônom",
    "siga autonom",
    "work autonom",
    "proceed autonom",
    "pode seguir",           # the loosest: measured 5x, 2 as a whole message
)

# What is running that will re-invoke the session. Free text after the colon:
# the point is to name the thing, and no closed set can.
DEFAULT_IN_FLIGHT_PREFIXES = ("IN FLIGHT", "EM VOO")

# THE HOLE THIS CLOSES WAS FOUND IN USE, ON THE SESSION THAT DESIGNED THE GATE.
# Its argument for checking the FORM rather than the fact was that a lie would
# have to be typed on purpose. Within hours it typed `EM VOO: nada` — "in
# flight: nothing" — to end two turns, and the gate passed both, because `nada`
# is a non-empty rest. A declaration that names nothing is not a declaration;
# it is the omission wearing the form. Measured on that session's transcript:
# 2 of its last 6 turn-ends.
# Matched against the FIRST WORD of the rest, not the whole of it: the form
# that got through in use was `EM VOO: nada — o que falta é meu`, a negation
# with a clause after it, which an exact match does not see.
#
# `no` and `na` are deliberately absent though they negate in English: in
# Portuguese they are the commonest prepositions, and `EM VOO: no painel` is
# a true declaration this gate must not refuse. A gate whose vocabulary
# collides across its own two languages teaches that it is noise.
DEFAULT_IN_FLIGHT_NEGATIONS = (
    "nada", "nenhum", "nenhuma", "nenhum(a)", "vazio", "zero",
    "nothing", "none", "nil", "n/a", "empty", "-", "—", "–",
)

# The turn really is over. These demand a reason from the closed set below,
# because an open reason field is an exemption the writer issues to itself.
DEFAULT_STOPPED_PREFIXES = ("STOPPED", "PARADO")

# The closed set. Four ends are legitimate; a fifth is a rationalisation.
DEFAULT_STOP_REASONS = (
    "queue empty", "fila vazia",
    "red gate", "gate vermelho",
    "operator decision", "decisão sua", "decisao sua", "decisão do operador",
    "question", "pergunta",
)

CONFIG_NAME = os.path.join(".claude", "autonomy-grant.json")
KEYS = ("grant_phrases", "in_flight_prefixes", "stopped_prefixes",
        "stop_reasons", "in_flight_negations")
DEFAULTS = dict(zip(KEYS, (DEFAULT_GRANT_PHRASES, DEFAULT_IN_FLIGHT_PREFIXES,
                           DEFAULT_STOPPED_PREFIXES, DEFAULT_STOP_REASONS,
                           DEFAULT_IN_FLIGHT_NEGATIONS)))

# The tools whose completion RE-INVOKES the session. An in-flight claim is
# about one of these and nothing else: a CI run, a provider, a colleague and
# the operator's own word all leave the session to poll, which under a grant
# is stopping. Naming them here is what lets the claim be checked instead of
# taken.
_REINVOKING_TOOLS = ("Agent", "Task", "Workflow")
# A notification names the tool_use it answers, OUTSIDE the `message` object.
# Searching only inside it matches nothing and leaves every launch live for
# ever — a bug this gate's own designer shipped twice in the measurement that
# produced the gate.
_NOTIFIED = re.compile(r"<tool-use-id>(toolu_[A-Za-z0-9]+)</tool-use-id>")

# Harness envelopes. Stripped from a user message before the grant phrases are
# matched, so that a grant quoted inside one is not the operator saying it —
# and so that a reminder appended to a real message does not disqualify the
# message. An unterminated tag swallows the rest of the text, which is the
# safe direction: drop rather than admit.
_ENVELOPE = re.compile(
    r"<(system-reminder|task-notification|local-command-caveat"
    r"|local-command-stdout|local-command-stderr|command-message|command-name"
    r"|command-args|command-contents|bash-input|bash-stdout|bash-stderr"
    r"|user-prompt-submit-hook|skill-format)\b[^>]*>.*?(?:</\1>|\Z)",
    re.IGNORECASE | re.DOTALL)

# Text the harness writes into a user record without an envelope around it.
_HARNESS_PREFIXES = (
    "This session is being continued",   # compaction / resumption preamble
    "[Request interrupted by user]",
    "Caveat: The messages below were generated by the user",
)


def load_config(cwd):
    """`(config, complaint)` — the vocabulary in force for a directory.

    An override at `.claude/autonomy-grant.json`, in the nearest enclosing
    directory that has one, REPLACES the default list of each key it states
    and leaves the others alone. Replacement rather than merge, so that a
    project can drop a default phrase that misfires for it; a merge it cannot
    turn off is a default it cannot escape.

    A malformed file falls back to the defaults and says so, rather than
    failing open in silence. `complaint` is that sentence, or None.

    The walk stops below `$HOME`: a `~/.claude/autonomy-grant.json` is a
    person's settings and would silently re-word the gate in every project on
    the machine, which is the one way this file could change what a project
    enforces without anyone in that project seeing it.
    """
    path = find_config(cwd)
    if path is None:
        return dict(DEFAULTS), None
    try:
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("the file is not a JSON object")
    except (OSError, ValueError) as error:
        return dict(DEFAULTS), f"{path}: {error} — using the defaults."
    config, bad = dict(DEFAULTS), []
    for key in KEYS:
        if key not in raw:
            continue
        value = raw[key]
        entries = tuple(item for item in value
                        if isinstance(item, str) and item.strip()) \
            if isinstance(value, list) else ()
        if not entries:
            bad.append(key)
            continue
        config[key] = entries
    if bad:
        return config, (f"{path}: {', '.join(bad)} is not a non-empty list of "
                        f"strings — using the default for it.")
    return config, None


def find_config(cwd):
    """The nearest `.claude/autonomy-grant.json` at or above `cwd`, or None."""
    if not cwd:
        return None
    try:
        current = os.path.realpath(cwd)
    except OSError:
        return None
    home = os.environ.get("HOME") or ""
    try:
        home = os.path.realpath(home) if home else None
    except OSError:
        home = None
    if home is not None and not (current == home
                                 or current.startswith(home + os.sep)):
        home = None  # outside it, `$HOME` bounds nothing
    while True:
        if current == home:
            return None
        candidate = os.path.join(current, CONFIG_NAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def human_text(record):
    """What the operator actually typed in a transcript record, or "".

    Everything the harness wrote is removed: whole records it owns, and the
    envelopes it wraps around text inside a record the human also wrote in.
    """
    if record.get("type") != "user":
        return ""
    if record.get("isMeta") or record.get("isCompactSummary") \
            or record.get("isSidechain"):
        # isMeta carries this hook's own refusal back into the transcript;
        # isCompactSummary is the model's summary of the session, not him;
        # isSidechain is a subagent's brief, which this session wrote.
        return ""
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content
                            if isinstance(part, dict)
                            and part.get("type") == "text")
    if not isinstance(content, str):
        return ""
    text = _ENVELOPE.sub(" ", content).strip()
    if not text or text.startswith(_HARNESS_PREFIXES):
        return ""
    return text


def assistant_text(record):
    """The text of an assistant record, or None when it is not one."""
    if record.get("type") != "assistant":
        return None
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return None
    return "\n".join(part.get("text", "") for part in content
                     if isinstance(part, dict) and part.get("type") == "text")


def has_phrase(text, phrases):
    """Whether any phrase occurs in the text, case-insensitively."""
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def state_line(text, config):
    """What the message declares about itself: "in-flight", "stopped" or None.

    One line: a prefix, a colon, and a rest. An in-flight rest is free text —
    it names what will re-invoke the session, and no closed set can — except
    that it may not NEGATE, because "in flight: nothing" is the omission
    wearing the form. A stopped rest must name one of the configured reasons,
    because an open reason field is an exemption the writer issues to itself.

    An in-flight claim is returned rather than accepted: main cross-checks it
    against the transcript, since the whole weakness of a form is that the
    form can be satisfied by a sentence nobody has to mean.
    """
    if not text:
        return None
    for line in text.splitlines():
        rest = _after_prefix(line, config["in_flight_prefixes"])
        if rest:
            if _negates(rest, config["in_flight_negations"]):
                return None
            return "in-flight"
        rest = _after_prefix(line, config["stopped_prefixes"])
        if rest and has_phrase(rest, config["stop_reasons"]):
            return "stopped"
    return None


def _negates(rest, negations):
    """Whether an in-flight rest names nothing, reading its FIRST WORD.

    First word rather than the whole rest, because what got through in use
    carried a clause after the negation. Decoration is stripped from both
    ends; a rest that is decoration alone negates too.
    """
    cleaned = rest.strip().strip("*_`~ ").strip()
    if not cleaned:
        return True
    head = re.split(r"[\s.,;:!?…]+", cleaned, maxsplit=1)[0].strip("*_`").lower()
    return head in tuple(n.lower() for n in negations)


def live_reinvoking_tasks(path):
    """How many launched Agent/Task/Workflow calls have not yet notified.

    This is what an in-flight claim MEANS, so it is what the claim is checked
    against. Zero of them and a turn that says it is waiting is a turn that
    has stopped: nothing will wake the session, and the operator learns it by
    coming back.
    """
    launched, notified = set(), set()
    try:
        handle = open(path, encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    with handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            if "<tool-use-id>" in raw:
                notified.update(_NOTIFIED.findall(raw))
            try:
                record = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            if record.get("type") != "assistant":
                continue
            content = (record.get("message") or {}).get("content") or []
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                args = block.get("input") or {}
                background = isinstance(args, dict) and args.get("run_in_background")
                if name in _REINVOKING_TOOLS or (name == "Bash" and background):
                    launched.add(block.get("id"))
    return len(launched - notified)


def _after_prefix(line, prefixes):
    """What follows `<prefix>:` on a line, or "" when it is not that shape.

    Tolerant of the decoration a message carries around it — a list bullet, a
    blockquote marker, bold — and of nothing else. The prefix heads the line.
    """
    stripped = line.strip()
    while stripped[:1] in ("-", "*", ">", "#"):
        stripped = stripped[1:].lstrip()
    lowered = stripped.lower()
    for prefix in prefixes:
        token = prefix.lower()
        if not lowered.startswith(token):
            continue
        rest = stripped[len(token):].lstrip()
        if rest.startswith("**"):
            rest = rest[2:].lstrip()
        if not rest.startswith(":"):
            continue
        return rest[1:].strip()
    return ""


def scan(path, config, want_text=True):
    """One pass over a transcript: `(grant_active, last_assistant_text)`.

    One pass rather than two because the expensive half is unavoidable: the
    grant is standing, so proving it ABSENT means reading every record. The
    last assistant message is collected on the way past for free.
    """
    grant = False
    text = None
    try:
        handle = open(path, encoding="utf-8", errors="ignore")
    except OSError:
        return False, None
    with handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            if want_text:
                found = assistant_text(record)
                if found is not None:
                    # The FINAL assistant record, text or not: walking further
                    # back would judge this turn by a previous turn's words.
                    text = found
            if not grant and has_phrase(human_text(record),
                                        config["grant_phrases"]):
                grant = True
    return grant, text


def refusal(config):
    """What the turn is told. Wording decides whether it obeys or argues.

    It demands a tool call rather than a justification, states the default
    next act, and does not present stopping as a menu — the four reasons are
    named because the form requires one of them, not as an invitation.
    """
    stopped = " | ".join(config["stopped_prefixes"])
    in_flight = " | ".join(config["in_flight_prefixes"])
    reasons = " | ".join(config["stop_reasons"])
    queue = f"{config['stopped_prefixes'][0]}: {config['stop_reasons'][0]}"
    return (
        f"AUTONOMY GRANT: a continuous grant is active and this turn does not "
        f"declare its own state. Do not answer this with an explanation — the "
        f"next tool call is cheaper than the paragraph defending its absence, "
        f"and is what the grant asked for. Default next act: start the next "
        f"unblocked item, now, in this same turn.\n"
        f"Then put ONE line in the message:\n"
        f"  {in_flight}: <what is running that will re-invoke this session>\n"
        f"  {stopped}: <{reasons}>\n"
        f"`{queue}` is NOT assertible. It is discharged by an ACTION in this "
        f"same turn — reading whatever this project uses to decide what comes "
        f"next — and never by the claim. If a to-do list in this message "
        f"names an unblocked item, the honest line is not `{queue}`; the "
        f"honest act is that item's first tool call."
    )


def unmet_claim(config):
    """What a turn is told when it claims to be waiting and nothing is.

    Separate wording from the missing-line refusal, because the mistake is
    different: the form was satisfied and the fact was not. Saying so is the
    point — a gate that answered this with the generic message would teach
    that the line is a password.
    """
    in_flight = config["in_flight_prefixes"][0]
    stopped = config["stopped_prefixes"][0]
    return (
        f"AUTONOMY GRANT: this turn declares `{in_flight}` and NOTHING is in "
        f"flight — no agent, workflow or background command is outstanding, so "
        f"nothing will re-invoke this session. Waiting on CI, on a provider, "
        f"or on the operator is not in flight: under a grant those are polled, "
        f"and stopping on one is stopping.\n"
        f"Either start the next unblocked item in THIS turn — that is what the "
        f"grant asked for and it is cheaper than the sentence defending the "
        f"pause — or say `{stopped}: <reason>` and mean it."
    )


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("stop_hook_active"):
        return 0  # already retrying: let it surface rather than spin
    config, complaint = load_config(payload.get("cwd") or "")
    if complaint:
        sys.stderr.write(f"autonomy-grant-gate: {complaint}\n")

    path = payload.get("transcript_path") or ""
    # The host documents `last_assistant_message` as exactly this text. A
    # STOPPED line is self-contained, so the transcript is never opened for
    # one — that is the cost control. An IN-FLIGHT line is a claim ABOUT the
    # session, so it is the one shape that must be paid for.
    text = payload.get("last_assistant_message")
    declared = state_line(text, config) if text is not None else None
    if declared == "stopped":
        return 0
    if declared == "in-flight" and live_reinvoking_tasks(path) > 0:
        return 0

    grant, scanned = scan(path, config, want_text=text is None)
    if not grant:
        return 0
    if text is None:
        text = scanned
        declared = state_line(text, config)
    # A final assistant record with no text at all declares nothing, but it is
    # also not a turn ending in prose: at a real stop the last record carries
    # the message. Refusing there would be refusing a transcript artifact.
    if not (text or "").strip():
        return 0
    if declared == "stopped":
        return 0
    if declared == "in-flight":
        if live_reinvoking_tasks(path) > 0:
            return 0
        sys.stderr.write(unmet_claim(config) + "\n")
        return 2
    sys.stderr.write(refusal(config) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
