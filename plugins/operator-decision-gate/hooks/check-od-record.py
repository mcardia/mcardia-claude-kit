#!/usr/bin/env python3
"""PreToolUse gate: a decision reaching the tracker arrives as a whole record.

The operator-decision rule says a decision is written as a fixed set of fields
"whether it asks or reports". Prose cannot enforce that, and the recorded
failure is not forgetting — it is the rule LOSING to a competing one in the
same context window. So the check lives at the boundary where the artifact is
actually written: an issue-tracker write that files a defect, claims the
operator owns something, or already carries a grade.

Three things are required of such a write:

1. **A grade**, spelled as a grade, in the project's own grade words — read
   out of its constitution by `od_common.grade_vocabulary`, never from here.
2. **At least two `file:line` anchors** — the rule requires the cause AND the
   remedy to have been verified at source, which is two places, not one.
3. **The adversarial panel named**, unless the grade is explicitly `n/a`
   (a record of a decision taken elsewhere: there is nothing to adjudicate).

Exit 2 with the reason on stderr blocks the call and hands the reason back.

Refuses nothing unless the project declares the rule — see
`od_common.find_constitution`. To ask whether a directory is gated, and by
which file:

    python3 check-od-record.py --explain [dir]

## What this check cannot see, and does not pretend to

It reads a command string. It does not run a shell, so a body the shell would
build is invisible to it:

- **A wrapper in the head slot.** `timeout 60 gh …`, `xargs gh …`,
  `bash -c "gh …"` hide the write behind a command whose arguments only a shell
  knows how to interpret. An absolute path (`/usr/bin/gh`) and a leading
  assignment (`GH_TOKEN=x gh …`) ARE handled, because both are lexical; the
  rest are not.
- **A body the shell expands.** `--body "$(cat record.md)"` and `--body "$VAR"`
  arrive here as the literal text `$(cat record.md)`, which matches nothing.

Closing either needs an interpreter, and a gate that claimed to be
unbypassable while these stand would be worse than one that says so. The claim
this check actually supports: it makes the correct path the cheap one and makes
skipping it visible.
"""
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from od_common import (  # noqa: E402
    GRADE_NA,
    MIN_ANCHORS,
    OWNERSHIP_CLAIM,
    PANEL,
    anchors,
    explain,
    find_constitution,
    grade_stated,
    read_vocabulary,
    remote_slugs,
)

# The writes that land a record where it can be read back later. `gh api` is
# included bare: a read carries no body, and a write with no body is nothing
# this check has an opinion about, so the body extraction below is the filter.
GH_WRITE = re.compile(
    r"\bgh\s+(?:issue|pr)\s+(?:create|comment|edit|close|reopen|review)\b"
    r"|\bgh\s+api\b",
    re.IGNORECASE,
)

# A defect filed on the tracker. A defect is the commonest thing a session
# wrongly hands over, so filing one is a way into the check on its own.
FILES_A_DEFECT = re.compile(
    r"--label[= ]\s*['\"]?bug\b|(?<!\w)-l\s+['\"]?bug\b|--type[= ]\s*['\"]?bug\b",
    re.IGNORECASE)

# `punctuation_chars=True` makes these their own tokens. `{` and `}` are not in
# that set, so a brace group needs them named here; `\n` is NOT here, because
# shlex keeps a newline as whitespace and never emits one — newlines are turned
# into `;` before lexing, by `_break_lines`.
SEPARATORS = {"|", "||", "&&", ";", ";;", "&", "|&", "(", ")", "{", "}"}

# A command word the shell looks straight through, as a shell does.
TRANSPARENT_HEADS = ("sudo", "env", "command", "nohup", "exec")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# `--body-file -` reads the body from stdin, which in practice is a heredoc.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

TEXT_FLAGS = {"--body", "-b", "--comment"}
TEXT_PREFIXES = ("--body=", "-b=", "--comment=")
FIELD_FLAGS = {"-f", "--field", "--raw-field", "-F"}
PATH_FLAGS = {"--body-file", "-F"}
PATH_PREFIXES = ("--body-file=",)
# `gh pr review --comment --body …` uses `--comment` as a boolean, so the
# token after it is the next flag and not the text. A value that looks like a
# flag is not a value.
FLAGLIKE = re.compile(r"^--?[A-Za-z][\w-]*$")

MESSAGE = (
    "OPERATOR DECISION: this tracker write hands over or files a decision and "
    "is missing {reason}. The rule is in {constitution} — read its "
    "operator-decision section and write the record that section specifies, "
    "in full, in whichever direction this is: asking or reporting. Run "
    "/operator-decision-gate:od to produce the record and run the panel in "
    "one call. "
    "If the section leaves a change of this grade with the session rather than "
    "with the operator, execute it and make the record the receipt."
)


def strip_heredocs(command):
    """`(command without heredoc bodies, the bodies)`.

    Text inside a heredoc is data, not commands: `cat <<EOF > f` followed by a
    line beginning `gh issue comment` writes a file, it does not file a
    comment. Separating the two is what lets newlines be command separators
    everywhere else.
    """
    kept, bodies, terminator = [], [], None
    for line in command.split("\n"):
        if terminator is not None:
            if line.strip() == terminator:
                terminator = None
            else:
                bodies.append(line)
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match:
            terminator = match.group(2)
    return "\n".join(kept), "\n".join(bodies)


def _break_lines(text):
    """Newlines outside quotes become `;`, so each line starts a new segment.

    The gap this closes: `SEPARATORS` used to contain `"\\n"`, but shlex treats
    a newline as whitespace and never emits one as a token, so
    `echo hi` ⏎ `gh issue comment …` read as ONE segment headed by `echo` and
    passed. It is the commonest multi-command shape a session emits.
    """
    out, index, quote = [], 0, None
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\" and quote == '"' and index + 1 < len(text):
                out.append(char)
                out.append(text[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            out.append(char)
            index += 1
            continue
        if char == "\\" and index + 1 < len(text):
            if text[index + 1] == "\n":
                index += 2  # line continuation: still one command
                continue
            out.append(char)
            out.append(text[index + 1])
            index += 2
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            index += 1
            continue
        out.append(";" if char == "\n" else char)
        index += 1
    return "".join(out)


def segment_heads(command):
    """The command word of each segment, so text inside a heredoc is not one.

    `punctuation_chars` is what makes `;` and `&&` their own tokens. Without it
    a plain split leaves `hi;` glued together, no separator is ever recognised,
    and `echo hi; gh issue comment …` reads as a single segment headed by
    `echo` — which is the evasion this whole check exists to close.
    """
    text, _bodies = strip_heredocs(command)
    lexer = shlex.shlex(_break_lines(text), posix=True, punctuation_chars=True)
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
        if expect_head:
            if token in TRANSPARENT_HEADS or ASSIGNMENT.match(token):
                continue
            heads.append(token)
            expect_head = False
    return heads


def writes_with_gh(command):
    """True when some segment of the command runs `gh` itself.

    Compared by basename, so `/usr/bin/gh` is `gh`.
    """
    return any(os.path.basename(head) == "gh" for head in segment_heads(command))


def _read_file(path, cwd):
    """A `--body-file` path, resolved against the PAYLOAD's cwd.

    Resolving against this process's cwd instead is how a relative path read
    nothing and the check failed open; the hook does not run where the session
    runs.
    """
    if not os.path.isabs(path) and cwd:
        path = os.path.join(cwd, path)
    try:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            return handle.read()
    except OSError:
        return ""


def body_of(command, cwd=None):
    """The text this write would post: every body-carrying flag, resolved."""
    text, heredoc = strip_heredocs(command)
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        return command  # unparseable: fall back to the raw text
    chunks, index = [], 0
    while index < len(tokens):
        token = tokens[index]
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if following is not None and FLAGLIKE.match(following):
            following = None
        if token in TEXT_FLAGS and following is not None:
            chunks.append(following)
            index += 2
            continue
        prefix = next((p for p in TEXT_PREFIXES if token.startswith(p)), None)
        if prefix:
            chunks.append(token[len(prefix):])
            index += 1
            continue
        # `gh api … -f body=…` posts the same comment the porcelain does.
        if (token in FIELD_FLAGS and following is not None
                and following[:5].lower() == "body="):
            chunks.append(following[5:])
            index += 2
            continue
        prefix = next((p for p in PATH_PREFIXES if token.startswith(p)), None)
        if prefix:
            chunks.append(_read_file(token[len(prefix):], cwd))
            index += 1
            continue
        if token in PATH_FLAGS and following is not None:
            if following == "-":
                chunks.append(heredoc)
            elif "=" not in following:
                chunks.append(_read_file(following, cwd))
            index += 2
            continue
        index += 1
    return "\n".join(chunk for chunk in chunks if chunk)


REPO_FLAG = re.compile(r"(?:--repo|(?<![\w-])-R)[= ]\s*['\"]?([^\s'\"]+)")


def in_scope(command, project_root):
    """False when an explicit repository flag names a repository outside this
    project.

    A command naming another organisation's repository is out of the rule even
    when it runs from inside the project tree. Both spellings count: `-R` is
    the one a session reaches for, and reading only `--repo` left every `-R`
    write gated as if it were local. When the remotes cannot be read the answer
    is yes: a gate that fails open on an unreadable config would be switched
    off by a shallow clone.
    """
    match = REPO_FLAG.search(command)
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
    if not writes_with_gh(command):
        return None
    found = find_constitution(cwd)
    if not found:
        return None
    project_root, constitution = found
    if not in_scope(command, project_root):
        return None
    body = body_of(command, cwd)
    if not body:
        return None
    stated = grade_stated(read_vocabulary(constitution))
    # Three ways in: filing a defect, claiming the operator owns something, or
    # already writing a record — a half-written one still has to be whole.
    if not (FILES_A_DEFECT.search(command)
            or OWNERSHIP_CLAIM.search(body)
            or stated.search(body)):
        return None
    if not stated.search(body):
        return "a grade", constitution
    if len(anchors(body)) < MIN_ANCHORS:
        return "two file:line anchors (the cause and the remedy)", constitution
    if not GRADE_NA.search(body) and not PANEL.search(body):
        return "the adversarial panel it went through", constitution
    return None


def main(argv):
    # `--explain` is the only way to ask whether a project is gated and by
    # which file, and the only way to see what the vocabulary parser read.
    # A bare run in a terminal means the same question.
    if argv and argv[0] in ("-e", "--explain"):
        print(explain(argv[1] if len(argv) > 1 else os.getcwd()))
        return 0
    if sys.stdin.isatty():
        print(explain(os.getcwd()))
        return 0
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
    sys.exit(main(sys.argv[1:]))
