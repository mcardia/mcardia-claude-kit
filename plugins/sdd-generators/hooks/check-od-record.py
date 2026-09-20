#!/usr/bin/env python3
"""PreToolUse gate: a decision reaching the tracker arrives as a whole record.

The operator-decision rule says a decision is written as a fixed set of fields
"whether it asks or reports". Prose cannot enforce that, and the recorded
failure is not forgetting — it is the rule LOSING to a competing one in the
same context window. So the check lives at the boundary where the artifact is
actually written: an issue-tracker write that files a defect, claims the
operator owns something, or already carries a grade.

Three things are required of such a write:

1. **A grade**, spelled as a grade. The grade is what answers *who decides*;
   an ownership claim without one is an assertion with nothing behind it.
2. **At least two `file:line` anchors** — the rule requires the cause AND the
   remedy to have been verified at source, which is two places, not one.
3. **The adversarial panel named**, unless the grade is explicitly `n/a`
   (a record of a decision taken elsewhere: there is nothing to adjudicate).

Exit 2 with the reason on stderr blocks the call and hands the reason back.

Inert unless the project declares the rule — see `od_common.find_constitution`.
"""
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from od_common import (  # noqa: E402
    ANCHOR,
    GRADE_NA,
    GRADE_STATED,
    MIN_ANCHORS,
    OWNERSHIP_CLAIM,
    PANEL,
    find_constitution,
    remote_slugs,
)

# The writes that land a record where it can be read back later.
GH_WRITE = re.compile(r"\bgh\s+(issue|pr)\s+(create|comment)\b")

# A defect filed on the tracker. A defect is the commonest thing a session
# wrongly hands over, so filing one is a way into the check on its own.
FILES_A_DEFECT = re.compile(
    r"--label[= ]\s*['\"]?bug\b|(?<!\w)-l\s+['\"]?bug\b|--type[= ]\s*['\"]?Bug\b")

SEPARATORS = {"|", "||", "&&", ";", ";;", "&", "|&", "(", ")", "\n"}

MESSAGE = (
    "OPERATOR DECISION: this tracker write hands over or files a decision and "
    "is missing {reason}. The rule fixes the form for BOTH directions — "
    "whether it asks or reports: the decision; how things stand; why they "
    "stand that way; the recommendation (KEEP or CHANGE, with exactly what "
    "changes); the grade; and where the cause AND the remedy were verified. "
    "Run /sdd-generators:od — it produces the record and the panel in one "
    "call. If the grade is `moderate` or below and none of the operator-only "
    "categories is touched, it is not the operator's at all: execute it and "
    "make the record the receipt. Rule read from {constitution}."
)


def segment_heads(command):
    """The command word of each segment, so text inside a heredoc is not one.

    `punctuation_chars` is what makes `;` and `&&` their own tokens. Without it
    a plain split leaves `hi;` glued together, no separator is ever recognised,
    and `echo hi; gh issue comment …` reads as a single segment headed by
    `echo` — which is the evasion this whole check exists to close.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    heads, expect_head = [], True
    for token in tokens:
        if token in SEPARATORS:
            expect_head = True
            continue
        if expect_head and token not in ("sudo", "env", "command", "nohup"):
            heads.append(token)
            expect_head = False
    return heads


def body_of(command):
    """The --body / -b text of the write, with --body-file/-F resolved."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return command  # unparseable: fall back to the raw text
    chunks, index = [], 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--body", "-b") and index + 1 < len(tokens):
            chunks.append(tokens[index + 1])
            index += 2
            continue
        if token.startswith("--body="):
            chunks.append(token[len("--body="):])
            index += 1
            continue
        if token in ("--body-file", "-F") and index + 1 < len(tokens):
            path = tokens[index + 1]
            if path != "-":
                try:
                    with open(path, encoding="utf-8", errors="ignore") as handle:
                        chunks.append(handle.read())
                except OSError:
                    chunks.append("")
            index += 2
            continue
        index += 1
    return "\n".join(chunks)


def in_scope(command, project_root):
    """False when an explicit --repo names a repository outside this project.

    A command naming another organisation's repository is out of the rule even
    when it runs from inside the project tree. When the remotes cannot be read
    the answer is yes: a gate that fails open on an unreadable config would be
    switched off by a shallow clone.
    """
    match = re.search(r"--repo[= ]\s*['\"]?([^\s'\"]+)", command)
    if not match:
        return True
    slugs = remote_slugs(project_root)
    if not slugs:
        return True
    named = match.group(1).lower()
    return any(named == slug or named.endswith("/" + slug.split("/")[-1])
               for slug in slugs)


def failing_reason(command, cwd):
    """The reason to block, or None when compliant or out of scope."""
    if not GH_WRITE.search(command):
        return None
    if "gh" not in segment_heads(command):
        return None
    found = find_constitution(cwd)
    if not found:
        return None
    project_root, constitution = found
    if not in_scope(command, project_root):
        return None
    body = body_of(command)
    if not body:
        return None
    # Three ways in: filing a defect, claiming the operator owns something, or
    # already writing a record — a half-written one still has to be whole.
    if not (FILES_A_DEFECT.search(command)
            or OWNERSHIP_CLAIM.search(body)
            or GRADE_STATED.search(body)):
        return None
    if not GRADE_STATED.search(body):
        return "a grade", constitution
    if len(set(ANCHOR.findall(body))) < MIN_ANCHORS:
        return "two file:line anchors (cause and remedy)", constitution
    if not GRADE_NA.search(body) and not PANEL.search(body):
        return "the adversarial panel it went through", constitution
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0
    verdict = failing_reason(command, payload.get("cwd") or "")
    if not verdict:
        return 0
    reason, constitution = verdict
    sys.stderr.write(
        MESSAGE.format(reason=reason, constitution=constitution) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
