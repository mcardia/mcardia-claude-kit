#!/usr/bin/env python3
"""Behavioural tests for the two operator-decision hooks this plugin ships.

Run them:

    python3 plugins/operator-decision-gate/hooks/test_hooks.py

Each case runs the real hook as a subprocess with a real JSON payload on stdin,
against a real temporary project tree, and asserts the exit code. Exit 2 blocks
the call; exit 0 lets it through. Nothing is mocked, because what these hooks
get wrong is never the logic — it is what a shell string actually tokenises to
and what a directory actually looks like on disk.

**A case that expects 0 says WHY in its name.** `(compliant)` means the write
satisfies the rule. `(hole)` means the gate cannot see the write at all — a
documented limit of checking text without a shell, not a pass. A suite that
spelled both the same way would read as if the gate were closed.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.dirname(os.path.abspath(__file__))
RECORD_HOOK = os.path.join(HOOKS, "check-od-record.py")
FORM_HOOK = os.path.join(HOOKS, "check-od-form.py")
PLUGIN = os.path.dirname(HOOKS)
# The template case reads the `constitution` generator's Output Template B out
# of the SIBLING plugin. This plugin carries no copy of it: the generator owns
# the section and this one only ever parses it, and two authors for one fact is
# the drift the kit exists to prevent.
#
# Where that sibling sits depends on which copy is running, and the two layouts
# are NOT the same shape:
#
#   repository   <repo>/plugins/<plugin>/                  siblings side by side
#   installed    <cache>/<marketplace>/<plugin>/<version>/ a version segment
#                                                          under every plugin
#
# So one hop up and across finds it in the repository only; from an installed
# copy it is two hops up and back down through a version directory whose name
# this plugin cannot know. Both are tried, repository first. Where several
# versions of the sibling are cached the NEWEST is read, because an update
# leaves older directories behind and never newer ones. Where the sibling is
# on neither path it is genuinely absent — this plugin installs alone — which
# the case reports, with the paths it tried, rather than crashes on.
_SKILL_TAIL = ("skills", "constitution", "SKILL.md")
CONSTITUTION_PATTERNS = (
    os.path.join(os.path.dirname(PLUGIN), "sdd-generators", *_SKILL_TAIL),
    os.path.join(os.path.dirname(os.path.dirname(PLUGIN)), "sdd-generators",
                 "*", *_SKILL_TAIL),
)


def _version_key(path):
    """Sort a cached sibling by its version directory, numerically.

    Sorting these as strings picks `3.0.0` over `10.0.0`, so the first
    double-digit major would silently read a stale template and the contract
    test would go green against the wrong side of it. The segments are
    compared as integers where they are integers, and the raw name breaks
    ties so a non-numeric directory still orders deterministically.
    """
    name = os.path.basename(os.path.dirname(os.path.dirname(
        os.path.dirname(path))))
    parts = tuple(int(p) if p.isdigit() else -1
                  for p in re.split(r"[.+-]", name))
    return (parts, name)


def find_constitution_skill():
    """The sibling's template, resolved across both layouts, or None."""
    for pattern in CONSTITUTION_PATTERNS:
        matches = glob.glob(pattern)
        if matches:
            return max(matches, key=_version_key)
    return None


CONSTITUTION_SKILL = find_constitution_skill()

sys.path.insert(0, HOOKS)

import od_common  # noqa: E402

CONSTITUTION = """# AGENTS.md

## 12. Where execution state lives

Nothing to see here.

## 13. Operator decisions

A question the coordinating session cannot settle is an operator decision.
Then grade the change with one word: `low`, `minor`, `moderate`, `major`,
`critical`. At `moderate` or below, execute the recommendation and report it
as done. Above `moderate`, it is the operator's.

## 14. Amendments
"""

NO_OD_CONSTITUTION = """# AGENTS.md

## 1. Source-of-truth hierarchy

This project has no operator-decision section.
"""

# A project that adopted the discipline with its OWN grade vocabulary and its
# own threshold. Nothing about this rule is this estate's, which is the point:
# the plugin applies whatever the constitution says and states none of it.
OTHER_VOCABULARY = """# AGENTS.md

## 9. Operator decisions

A question the session cannot settle is an operator decision. Grade the change
with one word: `trivial`, `small`, `large`, `sweeping`. At `small` or below the
session executes and reports it as done. Above `small`, it is the operator's.
"""

# A constitution that declares the rule but states no vocabulary, so the parse
# must fail and the hooks must degrade to the weaker-but-true check rather than
# to some other project's words.
NO_VOCABULARY = """# AGENTS.md

## 13. Operator decisions

A question the coordinating session cannot settle is an operator decision.
"""

# Sample answers for every placeholder in the operator-decision block of the
# Output Template B that the `constitution` generator in the `sdd-generators`
# plugin emits — the one authority on that section. The vocabulary is
# deliberately nobody's default — least of all this estate's — because a
# template and a parser that only agree on five familiar words agree on nothing.
TEMPLATE_ANSWERS = {
    "what makes a decision the operator's rather than the session's":
        "A decision is the operator's when it changes what the product "
        "promises a customer, rather than how the code keeps that promise.",
    "what the gate verifies": "the cause and the remedy, both at source",
    "who or what verifies it":
        "a fresh agent carrying none of the session's context",
    "grade word 1": "cosmetic",
    "grade word 2": "contained",
    "grade word 3": "structural",
    "grade word 4": "sweeping",
    "how a change is weighed": "how far its blast radius reaches",
    "threshold grade word": "contained",
    "what the session does at or below the line":
        "the session executes the recommendation and reports it as done",
    "reserved category 1": "anything that costs money",
    "reserved category 2": "anything a customer can see",
    "field label 1": "Under decision",
    "what field 1 states": "what is being decided, in one sentence",
    "field label 2": "As it stands",
    "what field 2 states": "what a named person does and what they see",
    "field label 3": "Where verified",
    "what field 3 states": "the anchors, for the cause and for the remedy",
    "where a handed-over record lands": "the pull request thread",
    "where a receipt lands": "the issue the work closes",
}
TEMPLATE_WORDS = "cosmetic, contained, structural, sweeping"
TEMPLATE_THRESHOLD = "contained (above it: structural, sweeping)"

# A record written in the vocabulary that template emits. No apostrophes: it
# travels inside a single-quoted shell string.
TEMPLATE_RECORD = (
    "Under decision: whether the export keeps every column for a viewer. "
    "Grade: contained. Where verified: internal/export/csv.go:88 and "
    "internal/http/reports.go:212 - od-gate panel."
)

PLACEHOLDER = re.compile(r"\[([^\[\]]+)\]")

FULL_RECORD = """Decision: whether the carrier write keeps its own statement.
How things stand: a returning user hits the OAuth callback and sees a 500.
Why they stand that way: the index admits one pending row, see
internal/repo/hub/email_verifications.go:41 and queries/create.sql:12.
Recommendation: KEEP.
Grade: minor.
Where verified: internal/repo/hub/email_verifications.go:41,
internal/repo/hub/queries/email_verifications_create.sql:12 — od-gate panel.
"""

CLAIM = "This is the operator decision, awaiting his word."
WHOLE = ("Grade: moderate. The operator decision. Verified at "
         "internal/app/auth/login.go:844 and internal/workers/lockids.go:70, "
         "adjudicated by the od-gate panel.")

CASES_RECORD = [
    # (name, constitution_body_or_None, command, expected_exit)
    ("ALLOWED (inert): no constitution at all", None,
     f"gh issue comment 12 --repo acme/core --body '{CLAIM} grade: major'", 0),
    ("ALLOWED (inert): the constitution has no OD section", NO_OD_CONSTITUTION,
     f"gh issue comment 12 --body '{CLAIM}'", 0),
    ("blocks an ownership claim with no grade", CONSTITUTION,
     f"gh issue comment 12 --body '{CLAIM}'", 2),
    ("blocks a graded record with too few anchors", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: moderate. The operator decision. "
     "Verified at internal/app/auth/login.go:844.'", 2),
    ("blocks a graded, anchored record that names no panel", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: moderate. The operator decision. Verified at "
     "internal/app/auth/login.go:844 and internal/workers/lockids.go:70.'", 2),
    ("ALLOWED (compliant): a whole record", CONSTITUTION,
     f"gh issue comment 12 --body '{WHOLE}'", 0),
    ("ALLOWED (compliant): grade n/a without a panel, anchors still required",
     CONSTITUTION,
     "gh issue comment 12 --body 'Grade: n/a — recorded in ADR-076. The operator decision "
     "was taken at docs/architecture/decisions/adr-076.md:31 and docs/plan.md:12.'", 0),
    ("blocks grade n/a with too few anchors", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: n/a. This is the operator decision, "
     "see docs/plan.md:12.'", 2),
    ("blocks filing a defect with no grade", CONSTITUTION,
     "gh issue create --label bug --title 'x' --body 'The reap dies on every tick.'", 2),
    ("ALLOWED (not a write): a read", CONSTITUTION,
     "gh issue view 12 --repo acme/core", 0),
    ("ALLOWED (out of scope): --repo names a foreign repository", CONSTITUTION,
     f"gh issue comment 12 --repo other-org/other-repo --body '{CLAIM}'", 0),
    # `-R` is the spelling a session actually types. Reading only `--repo` left
    # every `-R` write gated as if it named this project.
    ("ALLOWED (out of scope): -R names a foreign repository", CONSTITUTION,
     f"gh issue comment 12 -R other-org/other-repo --body '{CLAIM}'", 0),
    # This passes because `cat`, not `gh`, heads the only command: the second
    # line is heredoc DATA, stripped before the lexer sees it. It used to pass
    # for the wrong reason — newlines were not separators at all, so the same
    # two lines without a heredoc also passed, which is the case below.
    ("ALLOWED (not a command): gh appears only inside a heredoc", CONSTITUTION,
     f"cat <<'EOF' > /tmp/x\ngh issue comment 12 --body '{CLAIM}'\nEOF", 0),
    ("still fires when gh is not the first segment", CONSTITUTION,
     f"echo hi; gh issue comment 12 --body '{CLAIM}'", 2),
    ("still fires when a NEWLINE separates the two commands", CONSTITUTION,
     f"echo hi\ngh issue comment 12 --body '{CLAIM}'", 2),
    ("still fires after a bare `cd` on its own line", CONSTITUTION,
     f"cd /tmp\ngh issue comment 12 --body '{CLAIM}'", 2),
    ("still fires inside a brace group", CONSTITUTION,
     f"{{ gh issue comment 12 --body '{CLAIM}'; }}", 2),
    ("still fires when gh is named by absolute path", CONSTITUTION,
     f"/usr/bin/gh issue comment 12 --body '{CLAIM}'", 2),
    ("still fires behind a leading environment assignment", CONSTITUTION,
     f"GH_TOKEN=x gh issue comment 12 --body '{CLAIM}'", 2),

    # Body-carrying spellings the first suite never exercised.
    ("reads --body= (equals form)", CONSTITUTION,
     f"gh issue comment 12 --body='{CLAIM}'", 2),
    ("reads -b (short form)", CONSTITUTION,
     f"gh issue comment 12 -b '{CLAIM}'", 2),
    ("reads --body-file= (equals form)", CONSTITUTION, None, 2),  # built below
    ("gates gh pr comment", CONSTITUTION,
     f"gh pr comment 12 --body '{CLAIM}'", 2),
    ("gates gh pr create", CONSTITUTION,
     f"gh pr create --title x --body '{CLAIM}'", 2),
    ("gates gh issue edit", CONSTITUTION,
     f"gh issue edit 12 --body '{CLAIM}'", 2),
    ("gates gh pr edit", CONSTITUTION,
     f"gh pr edit 12 --body '{CLAIM}'", 2),
    ("gates gh issue close --comment", CONSTITUTION,
     f"gh issue close 12 --comment '{CLAIM}'", 2),
    ("gates gh pr review --comment --body", CONSTITUTION,
     f"gh pr review 12 --comment --body '{CLAIM}'", 2),
    ("gates gh api with -f body=", CONSTITUTION,
     f"gh api repos/acme/core/issues/12/comments -f body='{CLAIM}'", 2),
    ("reads the body from a heredoc behind --body-file -", CONSTITUTION,
     f"gh issue comment 12 --body-file - <<'EOF'\n{CLAIM}\nEOF", 2),

    # Filing a defect: the label spellings.
    ("gates -l bug", CONSTITUTION,
     "gh issue create -l bug --title x --body 'The reap dies on every tick.'", 2),
    ("gates --label Bug, whatever its case", CONSTITUTION,
     "gh issue create --label Bug --title x --body 'The reap dies on every tick.'", 2),

    # Anchors. A host and a port have a file-and-line's shape.
    ("two host:port strings are not two anchors", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: major. The operator decision. Seen at "
     "example.com:8080 and staging.io:9090 — od-gate panel.'", 2),
    ("ALLOWED (compliant): two bare file:line anchors, no directory", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: minor. The operator decision. Verified at "
     "reap.go:70 and lockids.go:12 — od-gate panel.'", 0),

    # Holes. Each needs a shell to close, and the gate has none.
    ("ALLOWED (hole): a body built by command substitution", CONSTITUTION,
     'gh issue comment 12 --body "$(cat /tmp/record.md)"', 0),
    ("ALLOWED (hole): a body held in a variable", CONSTITUTION,
     'gh issue comment 12 --body "$BODY"', 0),
    ("ALLOWED (hole): a wrapper taking its own arguments", CONSTITUTION,
     f"timeout 60 gh issue comment 12 --body '{CLAIM}'", 0),
    ("ALLOWED (hole): xargs in the head slot", CONSTITUTION,
     f"echo '' | xargs gh issue comment 12 --body '{CLAIM}'", 0),
    ("ALLOWED (hole): bash -c around the whole write", CONSTITUTION,
     f'bash -c "gh issue comment 12 --body \'{CLAIM}\'"', 0),
    ("ALLOWED (hole): a command shlex cannot parse", CONSTITUTION,
     f"gh issue comment 12 --body 'unterminated {CLAIM}", 0),

    # BLOCKER 1's acceptance case. The record below is WHOLE by the adopting
    # project's own constitution: its vocabulary, its threshold, its words. A
    # gate that refuses it is a gate stating a rule of its own.
    ("ALLOWED (compliant): a whole record in a project with its own vocabulary",
     OTHER_VOCABULARY,
     "gh issue comment 12 --body 'Decision: drop the retry. Grade: small. "
     "Verified at internal/workers/reap.go:70 and internal/workers/lockids.go:12, "
     "adjudicated by the od-gate panel. This operator decision is recorded here.'", 0),
    ("blocks an ungraded handover in that same project", OTHER_VOCABULARY,
     f"gh issue comment 12 --body '{CLAIM}'", 2),
    ("reads the foreign vocabulary, not this estate's", OTHER_VOCABULARY,
     f"gh issue comment 12 --body '{WHOLE}'", 2),

    # Degrading honestly: no vocabulary in the section, so any labelled value
    # satisfies the grade check and nothing is guessed.
    ("blocks an ungraded handover when no vocabulary can be read", NO_VOCABULARY,
     f"gh issue comment 12 --body '{CLAIM}'", 2),
    ("ALLOWED (compliant): any labelled grade when no vocabulary can be read",
     NO_VOCABULARY,
     "gh issue comment 12 --body 'Grade: whatever-this-project-calls-it. The "
     "operator decision. Verified at reap.go:70 and lockids.go:12 — od-gate panel.'", 0),

    # A turn or a comment that QUOTES the rule is not a record. The threshold
    # words appear in it, and must not pull it into the gate.
    ("ALLOWED (compliant): a comment quoting the grade vocabulary", CONSTITUTION,
     "gh issue comment 12 --body 'The section says to grade the change with one "
     "word: `low`, `minor`, `moderate`, `major`, `critical`. Nothing is decided here.'", 0),
    ("ALLOWED (compliant): a grade word used as prose", CONSTITUTION,
     "gh issue comment 12 --body 'We upgraded CI. The grade of the regression "
     "is minor at worst.'", 0),
    ("ALLOWED (compliant): the operator's machine is not a decision", CONSTITUTION,
     "gh issue comment 12 --body \"Repro only on the operator's laptop, not in CI.\"", 0),
    ("ALLOWED (compliant): plain english 'does not work until'", CONSTITUTION,
     "gh issue comment 12 --body 'Blocked: the smoke suite does not work until "
     "#231 lands.'", 0),
]

CASES_FORM = [
    # (name, constitution, assistant_text, stop_hook_active, expected_exit)
    ("ALLOWED (inert): no OD section", NO_OD_CONSTITUTION,
     "Seu: core#230 é sua decisão.", False, 0),
    ("ALLOWED (compliant): ordinary prose", CONSTITUTION,
     "Fase 1 fechada, gates verdes, PR aberto.", False, 0),
    ("blocks a bare handover", CONSTITUTION,
     "Seu, um só: core#230, o handler do SPA shell.", False, 2),
    ("blocks an English handover", CONSTITUTION,
     "That one is yours to decide — I have left it registered.", False, 2),
    ("blocks a grade above the line with no record", CONSTITUTION,
     "Corrigi o resto. O último fica: grade major, o handler do SPA shell.", False, 2),
    ("blocks a record missing the panel", CONSTITUTION,
     FULL_RECORD.replace(" — od-gate panel.", ".").replace("Grade: minor", "Grade: major"),
     False, 2),
    ("ALLOWED (compliant): a whole record", CONSTITUTION,
     FULL_RECORD.replace("Grade: minor", "Grade: major"), False, 0),
    ("ALLOWED (compliant): a retry, rather than spinning", CONSTITUTION,
     "Seu, um só: core#230, o handler do SPA shell.", True, 0),
    # The self-reference case. A turn that explains, amends or quotes the rule
    # names the threshold words, and used to be unable to end.
    ("ALLOWED (compliant): a turn explaining what the hook blocks", CONSTITUTION,
     "O hook novo bloqueia qualquer turno que diga grade major sem o record.",
     False, 0),
    ("ALLOWED (compliant): a turn quoting the grade vocabulary", CONSTITUTION,
     "A regra: grade the change with one word — `low`, `minor`, `moderate`, "
     "`major`, `critical`. Acima de `moderate` é dele.", False, 0),
    ("ALLOWED (compliant): a grade word in prose near the label", CONSTITUTION,
     "Fase 3 fechada. Grade: minor, e o critical path não muda.", False, 0),
    ("ALLOWED (compliant): a major version bump is not a grade", CONSTITUTION,
     "Bumpei o driver: grade minor, mas é um major version bump.", False, 0),
    ("ALLOWED (compliant): the operator's own rules, quoted", CONSTITUTION,
     "Segui the operator's global rules e abri o PR.", False, 0),
    # Nothing above the line can be read out of a section that states none.
    ("ALLOWED (compliant): no vocabulary, so no threshold to be above",
     NO_VOCABULARY,
     "Corrigi o resto. O último fica: grade major, o handler do SPA shell.", False, 0),
    ("blocks an explicit handover even with no vocabulary", NO_VOCABULARY,
     "Seu, um só: core#230, o handler do SPA shell.", False, 2),
    # The two hooks must agree about `grade: n/a`, or one record blocks in chat
    # and passes on the tracker.
    ("ALLOWED (compliant): grade n/a handover, no panel — as on the tracker",
     CONSTITUTION,
     "Seu: core#230. Grade: n/a — já decidido na ADR-076. Verificado em "
     "docs/adr-076.md:31 e docs/plan.md:12.", False, 0),
]


GIT_CONFIG = """[core]
\trepositoryformatversion = 0
[remote "origin"]
\turl = git@github.com:{slug}.git
\tfetch = +refs/heads/*:refs/remotes/origin/*
"""


def make_project(body, worktree=False, parent=None, remote="acme/core",
                 name=None):
    """A temp project: a constitution plus a real git config with a remote.

    `worktree` builds the linked-worktree shape, where `.git` is a FILE and the
    config lives in the common directory rather than beside it. `remote` is the
    slug that config points at, which is what scope is decided against.
    """
    config = GIT_CONFIG.format(slug=remote)
    if name is not None:
        root = os.path.join(parent, name)
        os.makedirs(root)
    else:
        root = (tempfile.mkdtemp(prefix="od-hook-test-") if parent is None
                else tempfile.mkdtemp(prefix="p-", dir=parent))
    if body is not None:
        with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
            fh.write(body)
    if worktree:
        common = os.path.join(root, "real.git")
        gitdir = os.path.join(common, "worktrees", "wt")
        os.makedirs(gitdir)
        with open(os.path.join(common, "config"), "w", encoding="utf-8") as fh:
            fh.write(config)
        with open(os.path.join(gitdir, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with open(os.path.join(root, ".git"), "w", encoding="utf-8") as fh:
            fh.write(f"gitdir: {gitdir}\n")
    else:
        os.makedirs(os.path.join(root, ".git"))
        with open(os.path.join(root, ".git", "config"), "w", encoding="utf-8") as fh:
            fh.write(config)
    return root


def run(hook, payload, env=None, raw=None):
    proc = subprocess.run(
        [sys.executable, hook],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True, text=True, timeout=20,
        env=None if env is None else {**os.environ, **env})
    return proc.returncode, (proc.stderr or "").strip()


def transcript_of(root, text, name="t.jsonl"):
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user", "message": {"content": "go"}}) + "\n")
        fh.write(json.dumps({
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": text}]},
        }) + "\n")
    return path


class Suite:
    def __init__(self):
        self.passed = 0
        self.failures = []

    def check(self, label, got, expected, detail=""):
        if got == expected:
            self.passed += 1
        else:
            self.failures.append(f"{label}: expected {expected}, got {got} ({detail[:90]})")


def record_cases(suite):
    for name, body, command, expected in CASES_RECORD:
        root = make_project(body)
        try:
            if command is None:  # the --body-file= case
                path = os.path.join(root, "body.md")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(CLAIM + " No grade anywhere.")
                command = f"gh issue comment 12 --body-file={path}"
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": root,
            })
            suite.check(f"record/{name}", code, expected, err)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def body_file_cases(suite):
    """`--body-file` resolves against the PAYLOAD's cwd, not the hook's."""
    root = make_project(CONSTITUTION)
    try:
        with open(os.path.join(root, "body.md"), "w", encoding="utf-8") as fh:
            fh.write(CLAIM + " No grade anywhere.")
        for label, command in [
            ("absolute", f"gh issue comment 12 --body-file {root}/body.md"),
            # The hook does not run where the session runs. Resolving this
            # against the hook's own cwd read nothing and failed open.
            ("relative", "gh issue comment 12 --body-file body.md"),
        ]:
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": root,
            })
            suite.check(f"record/resolves a {label} --body-file", code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def payload_cases(suite):
    """Payloads that are not a gh write at all."""
    code, _ = run(RECORD_HOOK, {"tool_name": "Edit", "tool_input": {"file_path": "/x"},
                                "cwd": "/home/mario"})
    suite.check("record/ALLOWED (not a write): a non-Bash tool", code, 0)

    code, _ = run(RECORD_HOOK, None, raw="{not json at all")
    suite.check("record/ALLOWED (inert): malformed stdin", code, 0)

    # Inert because nothing ABOVE this path carries a constitution — not
    # because the path is missing. A missing cwd whose ancestors do carry one
    # still gates; `deleted_cwd_case` is that half.
    code, _ = run(RECORD_HOOK, {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh issue comment 12 --body '{CLAIM}'"},
        "cwd": "/nonexistent/path/that/is/not/there",
    })
    suite.check("record/ALLOWED (inert): a cwd under no constitution at all",
                code, 0)

    code, _ = run(FORM_HOOK, None, raw="")
    suite.check("form/ALLOWED (inert): empty stdin", code, 0)


def worktree_cases(suite):
    """Scope must survive a linked worktree, where `.git` is a file."""
    for label, command, expected in [
        ("ALLOWED (out of scope): foreign repo from a worktree",
         f"gh issue comment 12 --repo other-org/other --body '{CLAIM}'", 0),
        ("own repo still gated from a worktree",
         f"gh issue comment 12 --repo acme/core --body '{CLAIM}'", 2),
    ]:
        root = make_project(CONSTITUTION, worktree=True)
        try:
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": root,
            })
            suite.check(f"record/{label}", code, expected, err)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def submodule_scope_cases(suite):
    """A sibling repository of the same owner is inside the rule.

    The shape is the one that produced the hole: a tree of submodules where
    the inner one carries its own constitution, so the walk stops there and
    the only remote in view is the inner repository's. Every write naming a
    sibling — the commonest tracker write there is — then read as another
    organisation's business and went through ungated.
    """
    outer = make_project(CONSTITUTION, remote="acme/core")
    try:
        inner = make_project(CONSTITUTION, parent=outer, name="docs",
                             remote="acme/docs")
        for label, command, expected in [
            ("gates a sibling of the same owner (--repo)",
             f"gh issue comment 12 --repo acme/core --body '{CLAIM}'", 2),
            ("gates a sibling of the same owner (-R)",
             f"gh issue comment 12 -R acme/core --body '{CLAIM}'", 2),
            ("ALLOWED (out of scope): another owner, from the same cwd",
             f"gh issue comment 12 --repo other-org/core --body '{CLAIM}'", 0),
        ]:
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": inner,
            })
            suite.check(f"record/{label}", code, expected, err)
    finally:
        shutil.rmtree(outer, ignore_errors=True)


def deleted_cwd_case(suite):
    """A working directory that has been deleted must not switch the gate off.

    The session goes on running in it — a branch checkout removing a directory
    is enough — and an early return on "not a directory" made every hook call
    for the rest of that session inert, in silence.
    """
    root = make_project(CONSTITUTION)
    try:
        gone = os.path.join(root, "removed-while-running")
        os.makedirs(gone)
        os.rmdir(gone)
        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash",
            "tool_input": {"command": f"gh issue comment 12 --body '{CLAIM}'"},
            "cwd": gone,
        })
        suite.check("record/a deleted cwd still gates from its ancestors",
                    code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def subdirectory_case(suite):
    root = make_project(CONSTITUTION)
    try:
        deep = os.path.join(root, "internal", "repo", "hub")
        os.makedirs(deep)
        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash",
            "tool_input": {"command": "gh issue comment 12 "
                                      "--body 'This is the operator decision.'"},
            "cwd": deep,
        })
        suite.check("record/found from a subdirectory", code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def home_boundary_cases(suite):
    """A constitution in `$HOME` must not gate every project on the machine.

    One `~/CLAUDE.md` with an operator-decision heading would otherwise switch
    the gate on everywhere, including repositories that never adopted the rule.
    """
    home = tempfile.mkdtemp(prefix="od-home-")
    try:
        with open(os.path.join(home, "CLAUDE.md"), "w", encoding="utf-8") as fh:
            fh.write(CONSTITUTION)
        project = make_project(None, parent=home)
        command = f"gh issue comment 12 --body '{CLAIM}'"
        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash", "tool_input": {"command": command}, "cwd": project,
        }, env={"HOME": home})
        suite.check("record/ALLOWED (inert): a constitution in $HOME does not gate",
                    code, 0, err)

        with open(os.path.join(project, "AGENTS.md"), "w", encoding="utf-8") as fh:
            fh.write(CONSTITUTION)
        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash", "tool_input": {"command": command}, "cwd": project,
        }, env={"HOME": home})
        suite.check("record/the project's own constitution still gates", code, 2, err)

        # Outside `$HOME` the bound means nothing and the walk runs to `/`.
        outside = make_project(CONSTITUTION)
        try:
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash", "tool_input": {"command": command}, "cwd": outside,
            }, env={"HOME": home})
            suite.check("record/a project outside $HOME still gates", code, 2, err)
        finally:
            shutil.rmtree(outside, ignore_errors=True)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def explain_case(suite):
    """`--explain` is the only way to ask whether a project is gated."""
    root = make_project(CONSTITUTION)
    try:
        proc = subprocess.run(
            [sys.executable, RECORD_HOOK, "--explain", root],
            input="", capture_output=True, text=True, timeout=20)
        out = proc.stdout
        ok = (proc.returncode == 0 and "ACTIVE" in out
              and "low, minor, moderate, major, critical" in out
              and "threshold:     moderate" in out)
        suite.check("record/--explain names the constitution and its vocabulary",
                    ok, True, out[:120])
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = make_project(NO_OD_CONSTITUTION)
    try:
        proc = subprocess.run(
            [sys.executable, RECORD_HOOK, "-e", root],
            input="", capture_output=True, text=True, timeout=20)
        suite.check("record/--explain says INERT where the rule is not adopted",
                    proc.returncode == 0 and "INERT" in proc.stdout, True,
                    proc.stdout[:120])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def form_cases(suite):
    for name, body, text, active, expected in CASES_FORM:
        root = make_project(body)
        try:
            code, err = run(FORM_HOOK, {
                "cwd": root,
                "transcript_path": transcript_of(root, text),
                "stop_hook_active": active,
            })
            suite.check(f"form/{name}", code, expected, err)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def form_source_cases(suite):
    """Where the turn's text comes from."""
    root = make_project(CONSTITUTION)
    try:
        # The host hands us the answer. Preferring it avoids re-reading a
        # transcript measured at 35.4 MB on every turn.
        code, err = run(FORM_HOOK, {
            "cwd": root,
            "transcript_path": transcript_of(root, "Fase 1 fechada."),
            "stop_hook_active": False,
            "last_assistant_message": "Seu, um só: core#230, o handler.",
        })
        suite.check("form/last_assistant_message wins over the transcript",
                    code, 2, err)

        # A final assistant message with no text block handed over nothing.
        # Walking back to an older turn blocks this one for another's words.
        path = os.path.join(root, "stale.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Seu, um só: core#230."}]}}) + "\n")
            fh.write(json.dumps({"type": "user",
                                 "message": {"content": "ok, execute"}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "x", "name": "Bash", "input": {}}]}}) + "\n")
        code, err = run(FORM_HOOK, {
            "cwd": root, "transcript_path": path, "stop_hook_active": False,
        })
        suite.check("form/ALLOWED (compliant): a text-less final message is not "
                    "an older turn's handover", code, 0, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def fill_template(template):
    """`(template with sample answers substituted, placeholders with none)`."""
    unanswered = []

    def answer(match):
        key = " ".join(match.group(1).split())
        if key not in TEMPLATE_ANSWERS:
            unanswered.append(key)
            return match.group(0)
        return TEMPLATE_ANSWERS[key]

    return PLACEHOLDER.sub(answer, template), unanswered


def template_cases(suite):
    """The sibling generator must write a constitution these hooks can read.

    A `/sdd-generators:constitution` run that emitted a section the gate
    cannot parse would leave a project believing it is gated when it is not,
    and the failure would be silent in both directions — nothing refused,
    nothing said. So this fills the real template out of the real `SKILL.md`
    and puts the result through `--explain` and through the record hook as
    subprocesses, exactly as a project would.

    It is the one case that reaches outside this plugin, and the only one that
    cannot run when the sibling is not found on either of the two layouts it
    can sit on. It says so, prints every path it tried, and returns; the count
    drops by these cases and the rest of the suite still reports.

    `od_common` is imported here only to LOCATE the block — deliberately with
    the same predicate the hooks use to find a section, so a heading the gate
    would miss cannot be extracted and quietly tested anyway.
    """
    if CONSTITUTION_SKILL is None:
        print("SKIP  template/*: the `sdd-generators` plugin was not found "
              "beside or near this one, so the template these hooks must "
              "parse is not there to read. Tried:")
        for pattern in CONSTITUTION_PATTERNS:
            print(f"        {pattern}")
        return

    with open(CONSTITUTION_SKILL, encoding="utf-8") as fh:
        skill = fh.read()

    heading = od_common.OD_SECTION.search(skill)
    suite.check("template/the hooks recognise the heading the template emits",
                bool(heading), True,
                "no heading in Output Template B that OD_SECTION matches: the "
                "generated gate would ship silently off")
    if not heading:
        return

    filled, unanswered = fill_template(od_common.section_text(skill))
    suite.check("template/every placeholder in the block has a sample answer",
                unanswered, [], f"unanswered: {unanswered}")
    suite.check("template/the filled block leaves no placeholder behind",
                "[" in filled, False, filled[:120])

    root = make_project(f"# AGENTS.md\n\n{heading.group(0)}\n{filled}\n")
    try:
        proc = subprocess.run(
            [sys.executable, RECORD_HOOK, "--explain", root],
            input="", capture_output=True, text=True, timeout=20)
        out = proc.stdout
        suite.check("template/the parser reads the template's own vocabulary",
                    f"vocabulary:    {TEMPLATE_WORDS}" in out, True, out[:200])
        suite.check("template/the parser reads the template's own threshold",
                    f"threshold:     {TEMPLATE_THRESHOLD}" in out, True,
                    out[:200])

        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"gh issue comment 12 --body '{TEMPLATE_RECORD}'"},
            "cwd": root,
        })
        suite.check("template/ALLOWED (compliant): a record in the words that "
                    "template emits", code, 0, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def asymmetry_case(suite):
    """One record, two hooks, one verdict."""
    root = make_project(CONSTITUTION)
    try:
        body = ("Seu: core#230. Grade: n/a — já decidido na ADR-076. "
                "Verificado em docs/adr-076.md:31 e docs/plan.md:12.")
        code, err = run(RECORD_HOOK, {
            "tool_name": "Bash",
            "tool_input": {"command": f"gh issue comment 12 --body '{body}'"},
            "cwd": root,
        })
        suite.check("record/grade n/a needs no panel", code, 0, err)
        code, err = run(FORM_HOOK, {
            "cwd": root,
            "transcript_path": transcript_of(root, body),
            "stop_hook_active": False,
        })
        suite.check("form/grade n/a needs no panel either", code, 0, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    suite = Suite()
    record_cases(suite)
    body_file_cases(suite)
    payload_cases(suite)
    worktree_cases(suite)
    submodule_scope_cases(suite)
    deleted_cwd_case(suite)
    subdirectory_case(suite)
    home_boundary_cases(suite)
    explain_case(suite)
    form_cases(suite)
    form_source_cases(suite)
    asymmetry_case(suite)
    template_cases(suite)

    total = suite.passed + len(suite.failures)
    print(f"{suite.passed}/{total} passed")
    for line in suite.failures:
        print(f"  FAIL  {line}")
    return 1 if suite.failures else 0


if __name__ == "__main__":
    sys.exit(main())
