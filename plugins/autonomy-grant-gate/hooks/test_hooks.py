#!/usr/bin/env python3
"""Behavioural tests for the Stop hook this plugin ships.

Run them:

    python3 plugins/autonomy-grant-gate/hooks/test_hooks.py

Each case runs the real hook as a subprocess with a real JSON payload on
stdin, against a real temporary transcript on disk, and asserts the exit code.
Exit 2 refuses the turn; exit 0 lets it end. Nothing is mocked, because what
this hook gets wrong is never the logic — it is what a transcript record
actually looks like on disk and which of them the operator actually typed.

**A case that expects 0 says WHY in its name.** `(compliant)` means the turn
declared its state. `(no grant)` means the gate correctly ignored a turn
nobody had granted autonomy for. `(one-shot)` means the gate had already
spoken. A suite that spelled all three the same way would read as closed when
it is not.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HOOKS, "check-grant-stop.py")
CALIBRATE = os.path.join(HOOKS, "calibrate.py")

GRANT = "continue autonomamente"
PLAIN = "Phase 1 merged, gates green, PR open. Phase 2 is next."
TEN_MORE = [f"ok, and check item {n}" for n in range(10)]


def transcript(root, human, final, name="t.jsonl", extra=()):
    """A transcript: one human message, optional more, one final assistant one.

    `human` is a list of `(kind, text)`, where kind is `user`, `meta` or
    `summary` — the two harness-owned shapes a grant can hide in.
    """
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8") as handle:
        for kind, text in human:
            record = {"type": "user", "message": {"content": text}}
            if kind == "meta":
                record["isMeta"] = True
            elif kind == "summary":
                record["isCompactSummary"] = True
            elif kind == "sidechain":
                record["isSidechain"] = True
            handle.write(json.dumps(record) + "\n")
        for text in extra:
            handle.write(json.dumps(
                {"type": "user", "message": {"content": text}}) + "\n")
        if final is not None:
            handle.write(json.dumps(
                {"type": "assistant",
                 "message": {"content": [{"type": "text",
                                          "text": final}]}}) + "\n")
    return path


def run(payload, raw=None):
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True, text=True, timeout=30)
    return proc.returncode, (proc.stderr or "").strip()


# (name, human records, final assistant message, extra human messages, exit)
CASES = [
    ("blocks a grant with no state line",
     [("user", GRANT)], PLAIN, (), 2),
    ("ALLOWED (compliant): IN FLIGHT",
     [("user", GRANT)], PLAIN + "\n\nIN FLIGHT: the phase-2 executor agent.",
     (), 0),
    ("ALLOWED (compliant): EM VOO",
     [("user", GRANT)], PLAIN + "\n\nEM VOO: o agente executor da fase 2.",
     (), 0),
    ("ALLOWED (compliant): STOPPED: queue empty",
     [("user", GRANT)], PLAIN + "\nSTOPPED: queue empty", (), 0),
    ("ALLOWED (compliant): STOPPED: red gate",
     [("user", GRANT)], PLAIN + "\nSTOPPED: red gate — the smoke suite.",
     (), 0),
    ("ALLOWED (compliant): STOPPED: operator decision",
     [("user", GRANT)], PLAIN + "\nSTOPPED: operator decision, core#230.",
     (), 0),
    ("ALLOWED (compliant): STOPPED: question",
     [("user", GRANT)], PLAIN + "\nSTOPPED: question — which of the two?",
     (), 0),
    ("ALLOWED (compliant): PARADO: fila vazia",
     [("user", GRANT)], PLAIN + "\nPARADO: fila vazia", (), 0),
    ("ALLOWED (compliant): PARADO: gate vermelho",
     [("user", GRANT)], PLAIN + "\nPARADO: gate vermelho no pre-push.", (), 0),
    ("ALLOWED (compliant): PARADO: decisao sua",
     [("user", GRANT)], PLAIN + "\nPARADO: decisao sua, core#230.", (), 0),
    ("ALLOWED (compliant): PARADO: pergunta",
     [("user", GRANT)], PLAIN + "\nPARADO: pergunta sobre o escopo.", (), 0),
    # The closed set is the whole of the second half of the rule: an open
    # reason field is an exemption the writer issues to itself.
    ("blocks a stop reason outside the closed set",
     [("user", GRANT)], PLAIN + "\nSTOPPED: work finished for today.", (), 2),
    ("blocks a state line with nothing after the colon",
     [("user", GRANT)], PLAIN + "\nEM VOO:", (), 2),
    ("ALLOWED (compliant): the line is decorated and not last",
     [("user", GRANT)],
     "- **EM VOO:** o executor da fase 2.\n\nAnd here is the rest.", (), 0),
    ("ALLOWED (compliant): the line is a list bullet",
     [("user", GRANT)], PLAIN + "\n- STOPPED: question", (), 0),

    ("ALLOWED (no grant): nobody ever granted anything",
     [("user", "fix the login redirect")], PLAIN, (), 0),
    ("ALLOWED (no grant): the grant is only inside a system-reminder",
     [("user", f"<system-reminder>\nstanding: {GRANT}\n</system-reminder>")],
     PLAIN, (), 0),
    ("ALLOWED (no grant): the grant is only inside a task-notification",
     [("user", f"<task-notification>\n<summary>{GRANT}</summary>\n"
               f"</task-notification>")], PLAIN, (), 0),
    # The hook's own refusal is fed back as an isMeta user record. Without the
    # skip, a gate whose wording quoted a phrase would arm itself.
    ("ALLOWED (no grant): the grant is only in the hook's own feedback",
     [("meta", f"Stop hook feedback: ... {GRANT} ...")], PLAIN, (), 0),
    ("ALLOWED (no grant): the grant is only inside a compaction summary",
     [("summary", f"This session is being continued ... he said {GRANT}")],
     PLAIN, (), 0),
    ("ALLOWED (no grant): the grant is only in a subagent's brief",
     [("sidechain", f"Your brief: {GRANT} until the queue is empty.")],
     PLAIN, (), 0),
    ("ALLOWED (no grant): the grant is only in a slash-command envelope",
     [("user", f"<command-message>{GRANT}</command-message>"
               f"<command-name>go</command-name>")], PLAIN, (), 0),
    # A reminder appended to a real message must not disqualify the message:
    # the session's first human message usually carries one.
    ("fires on a grant written beside a system-reminder",
     [("user", f"{GRANT}\n<system-reminder>be careful</system-reminder>")],
     PLAIN, (), 2),

    # STANDING. Re-evaluating the grant against his later sentences was
    # measured and missed four of the five real stops.
    ("the grant stands through ten later messages",
     [("user", GRANT)], PLAIN, TEN_MORE, 2),
    ("ALLOWED (compliant): standing, and the line is there",
     [("user", GRANT)], PLAIN + "\nPARADO: fila vazia", TEN_MORE, 0),

    ("ALLOWED (no grant): a transcript with no final assistant message",
     [("user", GRANT)], None, (), 0),
    ("ALLOWED (no grant): the final assistant message has no text",
     [("user", GRANT)], "", (), 0),
]


def basic_cases(suite):
    for name, human, final, extra, expected in CASES:
        root = tempfile.mkdtemp(prefix="grant-hook-test-")
        try:
            code, err = run({
                "cwd": root,
                "transcript_path": transcript(root, human, final, extra=extra),
                "stop_hook_active": False,
            })
            suite.check(name, code, expected, err)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def one_shot_case(suite):
    """`stop_hook_active` passes the retry, so the gate never spins.

    This is also the honest limit the README states: the gate costs a
    determined stopper exactly one extra sentence.
    """
    root = tempfile.mkdtemp(prefix="grant-hook-test-")
    try:
        path = transcript(root, [("user", GRANT)], PLAIN)
        code, err = run({"cwd": root, "transcript_path": path,
                         "stop_hook_active": True})
        suite.check("ALLOWED (one-shot): a retry is not refused again",
                    code, 0, err)
        code, err = run({"cwd": root, "transcript_path": path,
                         "stop_hook_active": False})
        suite.check("the same turn without the retry flag is refused",
                    code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def payload_cases(suite):
    """Payloads that give the hook nothing to judge."""
    code, _ = run(None, raw="{not json at all")
    suite.check("ALLOWED (no grant): malformed stdin", code, 0)
    code, _ = run(None, raw="")
    suite.check("ALLOWED (no grant): empty stdin", code, 0)
    code, _ = run(None, raw='["a list, not an object"]')
    suite.check("ALLOWED (no grant): stdin is not an object", code, 0)
    code, _ = run({"cwd": "/tmp", "stop_hook_active": False,
                   "transcript_path": "/nonexistent/transcript.jsonl"})
    suite.check("ALLOWED (no grant): the transcript is not there", code, 0)


def last_message_cases(suite):
    """The host hands us the final message; using it avoids a 36 MB read."""
    root = tempfile.mkdtemp(prefix="grant-hook-test-")
    try:
        path = transcript(root, [("user", GRANT)], "IN FLIGHT: the executor.")
        code, err = run({
            "cwd": root, "transcript_path": path, "stop_hook_active": False,
            "last_assistant_message": PLAIN,
        })
        suite.check("last_assistant_message wins over the transcript",
                    code, 2, err)
        path = transcript(root, [("user", GRANT)], PLAIN)
        code, err = run({
            "cwd": root, "transcript_path": path, "stop_hook_active": False,
            "last_assistant_message": PLAIN + "\nPARADO: fila vazia",
        })
        suite.check("ALLOWED (compliant): the line is in "
                    "last_assistant_message", code, 0, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def wording_case(suite):
    """The refusal decides whether starting is cheaper than explaining.

    Three things it must carry, pinned so a later edit cannot quietly drop
    them: a demand for the next tool call rather than a justification, the
    default next act, and the fact that `queue empty` is not assertible.
    """
    root = tempfile.mkdtemp(prefix="grant-hook-test-")
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(root, [("user", GRANT)], PLAIN),
            "stop_hook_active": False,
        })
        lowered = err.lower()
        suite.check("the refusal demands a tool call, not a justification",
                    "next tool call" in lowered
                    and "do not answer this with an explanation" in lowered,
                    True, err[:120])
        suite.check("the refusal states the default next act",
                    "default next act" in lowered, True, err[:120])
        suite.check("the refusal says `queue empty` is not assertible",
                    "not assertible" in lowered and "queue empty" in lowered,
                    True, err[:120])
        suite.check("the refusal exits 2", code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def config_cases(suite):
    """`.claude/autonomy-grant.json`: absent, malformed, and in force."""
    def project(override, raw=None):
        root = tempfile.mkdtemp(prefix="grant-hook-test-")
        os.makedirs(os.path.join(root, ".claude"))
        with open(os.path.join(root, ".claude", "autonomy-grant.json"), "w",
                  encoding="utf-8") as handle:
            handle.write(raw if raw is not None else json.dumps(override))
        return root

    # Malformed: the defaults still apply, and the hook says so rather than
    # failing open in silence.
    root = project(None, raw="{ this is not json")
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(root, [("user", GRANT)], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("a malformed override still applies the defaults",
                    code, 2, err)
        suite.check("a malformed override complains on stderr",
                    "autonomy-grant.json" in err and "defaults" in err.lower(),
                    True, err[:120])
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # A key whose value is the wrong shape falls back for that key alone.
    root = project({"grant_phrases": "not a list"})
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(root, [("user", GRANT)], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("a key of the wrong shape falls back to its default",
                    code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # An override that adds a phrase: the new one now triggers.
    added = list(_defaults("grant_phrases")) + ["luz verde"]
    root = project({"grant_phrases": added})
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(
                root, [("user", "luz verde, toca o barco")], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("an added phrase triggers the gate", code, 2, err)
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(root, [("user", GRANT)], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("adding a phrase keeps the ones it listed", code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Per key, an override REPLACES rather than merges — which is what lets a
    # project drop a default that misfires for it.
    root = project({"grant_phrases": ["luz verde"]})
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(root, [("user", GRANT)], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("ALLOWED (no grant): a replaced list drops the defaults",
                    code, 0, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Its own vocabulary, end to end.
    root = project({"in_flight_prefixes": ["RUNNING"],
                    "stopped_prefixes": ["HALTED"],
                    "stop_reasons": ["nothing left"]})
    try:
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(
                root, [("user", GRANT)], PLAIN + "\nHALTED: nothing left"),
            "stop_hook_active": False,
        })
        suite.check("ALLOWED (compliant): a project's own state vocabulary",
                    code, 0, err)
        code, err = run({
            "cwd": root,
            "transcript_path": transcript(
                root, [("user", GRANT)], PLAIN + "\nEM VOO: o executor."),
            "stop_hook_active": False,
        })
        suite.check("a replaced prefix list drops the default prefixes",
                    code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Found from a subdirectory, the way a session running deep in a tree
    # would find it.
    root = project({"grant_phrases": ["luz verde"]})
    try:
        deep = os.path.join(root, "internal", "app", "auth")
        os.makedirs(deep)
        code, err = run({
            "cwd": deep,
            "transcript_path": transcript(
                root, [("user", "luz verde")], PLAIN),
            "stop_hook_active": False,
        })
        suite.check("the override is found from a subdirectory", code, 2, err)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _defaults(key):
    """The hook's own default list for a key, read from the hook."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_grant_stop", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEFAULTS[key]


def calibration_case(suite):
    """The calibration script must refuse to print numbers it cannot back.

    Its self-check is the part that matters: the measurement this gate was
    designed from was confidently wrong twice, so the script asserts its own
    controls through this same hook before it prints anything at all.
    """
    root = tempfile.mkdtemp(prefix="grant-calib-test-")
    try:
        transcript(root, [("user", GRANT)], PLAIN, name="a.jsonl")
        transcript(root, [("user", "fix the redirect")], PLAIN, name="b.jsonl")
        proc = subprocess.run(
            [sys.executable, CALIBRATE, "-p", root, root],
            capture_output=True, text=True, timeout=120)
        out = proc.stdout
        suite.check("the calibration self-check passes", proc.returncode, 0,
                    out[-300:] + proc.stderr[-200:])
        suite.check("it reports both transcripts",
                    "transcripts scanned                 : 2" in out, True,
                    out[:400])
        suite.check("it reports the one granted turn-end lacking a line",
                    "... of those, lacking a state line: 1" in out, True,
                    out[:400])
        suite.check("it reports the control as zero",
                    "fires with no grant active          : 0" in out, True,
                    out[:400])

        # A directory with no transcripts is an error, not a green run.
        empty = os.path.join(root, "empty")
        os.makedirs(empty)
        proc = subprocess.run(
            [sys.executable, CALIBRATE, "-p", root, empty],
            capture_output=True, text=True, timeout=120)
        suite.check("an empty transcript directory fails rather than passing",
                    proc.returncode, 1, proc.stdout[:200])
    finally:
        shutil.rmtree(root, ignore_errors=True)


class Suite:
    def __init__(self):
        self.passed = 0
        self.failures = []

    def check(self, label, got, expected, detail=""):
        if got == expected:
            self.passed += 1
        else:
            self.failures.append(
                f"{label}: expected {expected}, got {got} ({detail[:110]})")


def main():
    suite = Suite()
    basic_cases(suite)
    one_shot_case(suite)
    payload_cases(suite)
    last_message_cases(suite)
    wording_case(suite)
    config_cases(suite)
    calibration_case(suite)

    total = suite.passed + len(suite.failures)
    print(f"{suite.passed}/{total} passed")
    for line in suite.failures:
        print(f"  FAIL  {line}")
    return 1 if suite.failures else 0


if __name__ == "__main__":
    sys.exit(main())
