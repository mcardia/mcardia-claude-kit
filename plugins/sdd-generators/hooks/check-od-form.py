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
a grade above `moderate` — that IS the handover, because the rule puts
everything above that line with the operator whether or not a sentence says so.

Loop-safe: a turn already continuing from this hook is allowed through, so a
second failure surfaces to the operator rather than spinning.

Inert unless the project declares the rule — see `od_common.find_constitution`.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from od_common import (  # noqa: E402
    ABOVE_MODERATE,
    PANEL,
    find_constitution,
)

# Handing a DECISION over. Deliberately not a bare possessive — "that file is
# yours" is possession, not a decision, and a gate that fires on it teaches
# nothing and gets resented.
HANDOVER = re.compile(
    r"^\s*(?:[-*>]\s*|\*\*)?seus?\s*[,:—–-]"
    r"|aguarda(?:m|ndo)?\s+(?:a\s+)?sua\s+palavra"
    r"|(?:é|e)\s+sua\s+decis|decis(?:ão|ao)\s+(?:é|e)\s+sua"
    r"|fica\s+(?:com|para)\s+você|passo\s+para\s+você|deixo\s+com\s+você"
    r"|n(?:ã|a)o\s+(?:é|e)\s+trabalho"
    r"|the\s+operator'?s\b(?!\s+own\s+words)|is\s+yours\b|yours\s+to\s+(?:decide|call)"
    r"|awaiting\s+(?:his|your|the\s+operator'?s)\s+word|not\s+work\s+until"
    r"|blocked-by-operator",
    re.IGNORECASE | re.MULTILINE,
)

# The record's fields, in the project's chat language or in English.
FIELD_LABELS = [
    r"o\s+qu(?:ê|e)\b|decision\b",
    r"como\s+est(?:á|a)\b|how\s+things\s+stand\b",
    r"por\s+qu(?:ê|e)\s+est(?:á|a)\s+assim|why\s+they\s+stand\b|why\s+things\s+stand\b",
    r"recomenda(?:ção|cao)\b|recommendation\b",
    r"\bgrau\b|\bgrade\b",
    r"onde\s+foi\s+verificado|where\s+(?:the\s+cause|cause\s+and)|where\s+verified\b",
]
GRADE_WORD = re.compile(
    r"(?:\bgrau\b|\bgrade\b)[^\n]{0,60}?\b(low|minor|moderate|major|critical)\b",
    re.IGNORECASE,
)
MIN_FIELDS = 4

MESSAGE = (
    "DECISION FORM: this turn hands the operator a decision and does not carry "
    "the record. The rule fixes the form for BOTH directions — \"whether it "
    "asks or reports\" — and a grade inside a sentence is not it. Write the "
    "block: the decision / how things stand / why they stand that way / the "
    "recommendation (KEEP or CHANGE, with exactly what changes) / the grade / "
    "where the cause and the remedy were verified. Run /sdd-generators:od to "
    "produce it with the panel. If the grade is `moderate` or below and none "
    "of the operator-only categories is touched, it is not the operator's at "
    "all: execute it and make the block the receipt. Rule read from "
    "{constitution}."
)


def last_assistant_text(path):
    """The text of the turn's final assistant message, or None."""
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
        text = "\n".join(chunk for chunk in chunks if chunk)
        if text.strip():
            return text
    return None


def compliant(text):
    if not (HANDOVER.search(text) or ABOVE_MODERATE.search(text)):
        return True
    if not GRADE_WORD.search(text):
        return False
    if not PANEL.search(text):
        return False
    present = sum(1 for pattern in FIELD_LABELS
                  if re.search(pattern, text, re.IGNORECASE))
    return present >= MIN_FIELDS


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
    text = last_assistant_text(payload.get("transcript_path") or "")
    if text is None or compliant(text):
        return 0
    sys.stderr.write(MESSAGE.format(constitution=constitution) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
