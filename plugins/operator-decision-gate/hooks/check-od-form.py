#!/usr/bin/env python3
"""Stop gate: a decision handed over in chat leaves as the whole record.

`check-od-record.py` catches an ungraded ownership claim on its way to the
tracker. It cannot see one that never leaves the chat — and that gap closed
itself the moment it was first written: the same message describing it ended
with a grade inside a sentence, which the rule does not admit.

The rule fixes the form for both directions, "whether it asks or reports". So
this hook reads the turn's final assistant message: if it hands the operator a
decision and does not carry the record, the turn does not end.

Two ways a turn hands over. The obvious one is saying so. The other is stating
a grade the constitution puts above its own line — that IS the handover,
because the rule puts everything above that line with the operator whether or
not a sentence says so. Which words those are is read from the constitution,
and when it cannot be read the second test is skipped rather than guessed.

Loop-safe: a turn already continuing from this hook is allowed through, so a
second failure surfaces to the operator rather than spinning.

Refuses nothing unless the project declares the rule — see
`od_common.find_constitution`.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from od_common import (  # noqa: E402
    GRADE_NA,
    PANEL,
    above_threshold,
    find_constitution,
    grade_stated,
    read_vocabulary,
)

# Handing a DECISION over. Deliberately not a bare possessive — "that file is
# yours" is possession, not a decision, and a gate that fires on it teaches
# nothing and gets resented. `the operator's` on its own used to be here and
# was the same defect the record hook carried: it fires on "the operator's
# machine" and on any turn that quotes the rule. What is left names a decision
# and says whose it is.
HANDOVER = re.compile(
    r"^\s*(?:[-*>]\s*|\*\*)?seus?\s*[,:—–-]"
    r"|aguarda(?:m|ndo)?\s+(?:a\s+)?sua\s+palavra"
    r"|(?:é|e)\s+sua\s+decis|decis(?:ão|ao)\s+(?:é|e)\s+sua"
    r"|fica\s+(?:com|para)\s+você|passo\s+para\s+você|deixo\s+com\s+você"
    r"|the\s+operator'?s\s+to\s+(?:decide|call|rule|settle|schedule|take|say)"
    # `is yours` on its own is the bare possessive this comment disclaims —
    # "that file is yours" is possession. It needs the thing being assigned.
    r"|\b(?:choice|call|decision|verdict|ruling)\s+is\s+yours\b"
    r"|yours\s+to\s+(?:decide|call|rule|settle)"
    r"|awaiting\s+(?:his|your|the\s+operator'?s)\s+word"
    r"|blocked-by-operator",
    re.IGNORECASE | re.MULTILINE,
)

MESSAGE = (
    "DECISION FORM: this turn hands the operator a decision and does not carry "
    "the record. The rule is in {constitution} — read its operator-decision "
    "section and write the record that section specifies, as a block, in "
    "whichever direction this is: asking or reporting. A grade inside a "
    "sentence is not it. Run /operator-decision-gate:od to produce the block "
    "with the panel. "
    "If the section leaves a change of this grade with the session "
    "rather than with the operator, execute it and make the block the receipt."
)


def last_assistant_text(path):
    """The text of the turn's FINAL assistant message.

    Used only when the host did not hand us `last_assistant_message`. It stops
    at the last assistant record rather than searching backwards for one that
    happens to carry text: walking further back blocks this turn for a
    previous turn's words, which is a refusal nobody can act on.
    """
    try:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
    except OSError:
        return None
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if record.get("type") != "assistant":
            continue
        content = (record.get("message") or {}).get("content") or []
        if isinstance(content, str):
            return content
        chunks = [c.get("text", "") for c in content
                  if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(chunk for chunk in chunks if chunk)
    return None


def compliant(text, vocabulary=None):
    """Whether a handover carries the record.

    Two requirements, and only two. A grade, in the project's own words; and
    the panel named, unless the grade is `n/a`, which records a decision taken
    elsewhere and has nothing to adjudicate — the same exemption the tracker
    hook applies, so that one record does not block in chat and pass on the
    tracker.

    **The record's six field labels are NOT checked.** They are the
    constitution's, like the grade words, and unlike the grade words they
    cannot be read out of prose reliably: a fields sentence lists clauses, and
    the first content word of each ("how", "why", "where") matches any text at
    all. A hard-coded list of six English labels here would be this plugin
    stating a rule it claims only to apply, which is the defect this file was
    rewritten to remove. What survives is what the plugin can check without
    inventing anything: a grade, and the panel.
    """
    if not (HANDOVER.search(text) or above_threshold(text, vocabulary)):
        return True
    if not grade_stated(vocabulary).search(text):
        return False
    return bool(GRADE_NA.search(text) or PANEL.search(text))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if payload.get("stop_hook_active"):
        return 0  # already retrying: let it surface rather than spin
    found = find_constitution(payload.get("cwd") or "")
    if not found:
        return 0
    _, constitution = found
    # The host documents `last_assistant_message` as exactly this text, and
    # says using it "avoids the need to read and parse the transcript file" —
    # a file measured at 35.4 MB, re-read on every turn.
    text = payload.get("last_assistant_message")
    if text is None:
        text = last_assistant_text(payload.get("transcript_path") or "")
    if text is None or compliant(text, read_vocabulary(constitution)):
        return 0
    sys.stderr.write(MESSAGE.format(constitution=constitution) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
