#!/usr/bin/env python3
"""Behavioural tests for the two operator-decision hooks shipped by the plugin.

Run them:

    python3 plugins/sdd-generators/hooks/test_hooks.py

Each case runs the real hook as a subprocess with a real JSON payload on stdin,
against a real temporary project tree, and asserts the exit code. Exit 2 blocks
the call; exit 0 lets it through. Nothing is mocked, because what these hooks
get wrong is never the logic — it is what a shell string actually tokenises to
and what a directory actually looks like on disk.

Two defects were found this way and would not have been found by reading:
a plain `shlex.split` leaves `hi;` glued together, so `echo hi; gh issue
comment …` read as a single segment and evaded the gate outright; and in a
linked worktree `.git` is a FILE, so every remote read as unknown and scope
detection failed. Both are cases below. Stdlib only, no framework, no runner —
a hook that silently stops refusing is the failure mode this guards, and that
needs one file, not a harness.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.dirname(os.path.abspath(__file__))
RECORD_HOOK = os.path.join(HOOKS, "check-od-record.py")
FORM_HOOK = os.path.join(HOOKS, "check-od-form.py")

CONSTITUTION = """# AGENTS.md

## 12. Where execution state lives

Nothing to see here.

## 13. Operator decisions

A question the coordinating session cannot settle is an operator decision.

## 14. Amendments
"""

NO_OD_CONSTITUTION = """# AGENTS.md

## 1. Source-of-truth hierarchy

This project has no operator-decision section.
"""

FULL_RECORD = """Decision: whether the carrier write keeps its own statement.
How things stand: a returning user hits the OAuth callback and sees a 500.
Why they stand that way: the index admits one pending row, see
internal/repo/hub/email_verifications.go:41 and queries/create.sql:12.
Recommendation: KEEP.
Grade: minor.
Where verified: internal/repo/hub/email_verifications.go:41,
internal/repo/hub/queries/email_verifications_create.sql:12 — od-gate panel.
"""

CASES_RECORD = [
    # (name, constitution_body_or_None, command, expected_exit)
    ("inert with no constitution at all", None,
     "gh issue comment 12 --repo acme/core --body 'This is the operator decision, grade: major'", 0),
    ("inert when the constitution has no OD section", NO_OD_CONSTITUTION,
     "gh issue comment 12 --body 'This is the operator decision to take'", 0),
    ("blocks an ownership claim with no grade", CONSTITUTION,
     "gh issue comment 12 --body 'This is the operator decision, awaiting his word.'", 2),
    ("blocks a graded record with too few anchors", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: moderate. The operator decision. "
     "Verified at internal/app/auth/login.go:844.'", 2),
    ("blocks a graded, anchored record that names no panel", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: moderate. The operator decision. Verified at "
     "internal/app/auth/login.go:844 and internal/workers/lockids.go:70.'", 2),
    ("passes a whole record", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: moderate. The operator decision. Verified at "
     "internal/app/auth/login.go:844 and internal/workers/lockids.go:70, "
     "adjudicated by the od-gate panel.'", 0),
    ("passes grade n/a without a panel, anchors still required", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: n/a — recorded in ADR-076. The operator decision "
     "was taken at docs/architecture/decisions/adr-076.md:31 and docs/plan.md:12.'", 0),
    ("blocks grade n/a with too few anchors", CONSTITUTION,
     "gh issue comment 12 --body 'Grade: n/a. This is the operator decision, "
     "see docs/plan.md:12.'", 2),
    ("blocks filing a defect with no grade", CONSTITUTION,
     "gh issue create --label bug --title 'x' --body 'The reap dies on every tick.'", 2),
    ("ignores a read", CONSTITUTION,
     "gh issue view 12 --repo acme/core", 0),
    ("ignores a gh write to a foreign repo", CONSTITUTION,
     "gh issue comment 12 --repo other-org/other-repo "
     "--body 'This is the operator decision, awaiting his word.'", 0),
    ("ignores gh appearing only inside a heredoc", CONSTITUTION,
     "cat <<'EOF' > /tmp/x\ngh issue comment 12 --body 'the operator decision'\nEOF", 0),
    ("still fires when gh is not the first segment", CONSTITUTION,
     "echo hi; gh issue comment 12 --body 'This is the operator decision, awaiting his word.'", 2),
    ("resolves --body-file", CONSTITUTION, None, 2),  # command built in the runner
]

CASES_FORM = [
    # (name, constitution, assistant_text, stop_hook_active, expected_exit)
    ("inert with no OD section", NO_OD_CONSTITUTION,
     "Seu: core#230 é sua decisão.", False, 0),
    ("passes ordinary prose", CONSTITUTION,
     "Fase 1 fechada, gates verdes, PR aberto.", False, 0),
    ("blocks a bare handover", CONSTITUTION,
     "Seu, um só: core#230, o handler do SPA shell.", False, 2),
    ("blocks an English handover", CONSTITUTION,
     "That one is the operator's — I have left it registered.", False, 2),
    ("blocks a grade above the line with no record", CONSTITUTION,
     "Corrigi o resto. O último fica: grade major, o handler do SPA shell.", False, 2),
    ("blocks a record missing the panel", CONSTITUTION,
     FULL_RECORD.replace(" — od-gate panel.", ".").replace("Grade: minor", "Grade: major"),
     False, 2),
    ("passes a whole record", CONSTITUTION,
     FULL_RECORD.replace("Grade: minor", "Grade: major"), False, 0),
    ("lets a retry through rather than spinning", CONSTITUTION,
     "Seu, um só: core#230, o handler do SPA shell.", True, 0),
]


GIT_CONFIG = """[core]
\trepositoryformatversion = 0
[remote "origin"]
\turl = git@github.com:acme/core.git
\tfetch = +refs/heads/*:refs/remotes/origin/*
"""


def make_project(body, worktree=False):
    """A temp project: a constitution plus a real git config with a remote.

    `worktree` builds the linked-worktree shape, where `.git` is a FILE and the
    config lives in the common directory rather than beside it.
    """
    root = tempfile.mkdtemp(prefix="od-hook-test-")
    if body is not None:
        with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
            fh.write(body)
    if worktree:
        common = os.path.join(root, "real.git")
        gitdir = os.path.join(common, "worktrees", "wt")
        os.makedirs(gitdir)
        with open(os.path.join(common, "config"), "w", encoding="utf-8") as fh:
            fh.write(GIT_CONFIG)
        with open(os.path.join(gitdir, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with open(os.path.join(root, ".git"), "w", encoding="utf-8") as fh:
            fh.write(f"gitdir: {gitdir}\n")
    else:
        os.makedirs(os.path.join(root, ".git"))
        with open(os.path.join(root, ".git", "config"), "w", encoding="utf-8") as fh:
            fh.write(GIT_CONFIG)
    return root


def run(hook, payload):
    proc = subprocess.run(
        [sys.executable, hook], input=json.dumps(payload),
        capture_output=True, text=True, timeout=20)
    return proc.returncode, (proc.stderr or "").strip()


def main():
    failures = []
    passed = 0

    for name, body, command, expected in CASES_RECORD:
        root = make_project(body)
        try:
            if command is None:  # the --body-file case
                path = os.path.join(root, "body.md")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("This is the operator decision, awaiting his word. "
                             "No grade anywhere.")
                command = f"gh issue comment 12 --body-file {path}"
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": root,
            })
            if code == expected:
                passed += 1
            else:
                failures.append(f"record/{name}: expected {expected}, got {code} ({err[:90]})")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # A non-Bash tool must never be examined.
    code, _ = run(RECORD_HOOK, {"tool_name": "Edit", "tool_input": {"file_path": "/x"},
                                "cwd": "/home/mario"})
    if code == 0:
        passed += 1
    else:
        failures.append(f"record/ignores a non-Bash tool: expected 0, got {code}")

    # Scope must survive a linked worktree, where `.git` is a file.
    for label, command, expected in [
        ("worktree: foreign repo still skipped",
         "gh issue comment 12 --repo other-org/other "
         "--body 'This is the operator decision, awaiting his word.'", 0),
        ("worktree: own repo still gated",
         "gh issue comment 12 --repo acme/core "
         "--body 'This is the operator decision, awaiting his word.'", 2),
    ]:
        root = make_project(CONSTITUTION, worktree=True)
        try:
            code, err = run(RECORD_HOOK, {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": root,
            })
            if code == expected:
                passed += 1
            else:
                failures.append(f"record/{label}: expected {expected}, got {code} ({err[:90]})")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # The gate must be found from a SUBDIRECTORY, not only the project root.
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
        if code == 2:
            passed += 1
        else:
            failures.append(f"record/found from a subdirectory: expected 2, got {code} ({err[:90]})")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    for name, body, text, active, expected in CASES_FORM:
        root = make_project(body)
        try:
            transcript = os.path.join(root, "t.jsonl")
            with open(transcript, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"type": "user", "message": {"content": "go"}}) + "\n")
                fh.write(json.dumps({
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": text}]},
                }) + "\n")
            code, err = run(FORM_HOOK, {
                "cwd": root,
                "transcript_path": transcript,
                "stop_hook_active": active,
            })
            if code == expected:
                passed += 1
            else:
                failures.append(f"form/{name}: expected {expected}, got {code} ({err[:90]})")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    total = passed + len(failures)
    print(f"{passed}/{total} passed")
    for line in failures:
        print(f"  FAIL  {line}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
