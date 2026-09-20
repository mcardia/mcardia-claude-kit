#!/usr/bin/env python3
"""Arm the autonomy-grant gate with a project's own numbers before trusting it.

    python3 calibrate.py [-p PROJECT] <transcript-dir>

`<transcript-dir>` is where the host keeps this project's session transcripts
(`~/.claude/projects/<slug>/`). `-p/--project` is the directory the vocabulary
is resolved from — the project root, so that an override at
`.claude/autonomy-grant.json` is the one being calibrated. It defaults to the
working directory.

WHAT IT PRINTS, AND WHICH NUMBER IS THE CONTROL

    transcripts scanned
    turn-ends
    turn-ends under an active grant
      ... of those, lacking a state line      <- what the gate would refuse
    fires with no grant active                <- MUST BE 0

The last number is the control. It is counted against an INDEPENDENT reading:
the walk decides the grant incrementally, turn-end by turn-end, the way the
standing rule works; the control re-decides it per file with `scan()`, the
same function the installed hook runs in production. A fire landing in a file
that function calls ungranted means the two disagree, and the gate is not
armed — whatever the other four numbers say. The same cross-reading catches
the walk forgetting to reset the standing flag between files, which would
make every file after the first granted one look granted.

WHY IT SELF-CHECKS FIRST, AND REFUSES TO PRINT IF IT CANNOT

The measurement this gate is designed from was wrong twice before it was
right. Once because it looked for a task-notification id inside the `message`
object when the id lives outside it; once because it treated the grant as
expiring at the operator's next sentence. Both produced confident numbers, and
nothing in either run looked wrong. So this script asserts its own controls —
against synthetic transcripts whose answers are known, through the real hook
as a subprocess as well as in process — and prints NOTHING but the failure if
any of them is off. A harness that cannot assert its own control is worth
nothing.

It re-implements none of the gate: every predicate below is imported from
`check-grant-stop.py`, so the numbers cannot drift from what the hook does.
The subprocess controls are what prove the import and the executable agree.
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HOOKS, "check-grant-stop.py")

_spec = importlib.util.spec_from_file_location("check_grant_stop", HOOK)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

GRANT = "continue autonomamente"
NO_LINE = "Phase 1 merged, gates green, PR open. Next up is phase 2."
# A STOPPED line is self-contained, so it is what the controls declare. An
# IN-FLIGHT line is a CLAIM the gate cross-checks against the transcript, so a
# synthetic record carrying one with no launched agent behind it is refused —
# correctly, and it is the shape `in-flight, nothing running` below exists to
# pin.
WITH_LINE = NO_LINE + "\n\nSTOPPED: operator decision"
# The hole found in use: "in flight: nothing" satisfied the old form check.
IN_FLIGHT_NEGATED = NO_LINE + "\n\nIN FLIGHT: nothing"
# A named claim with nothing behind it — the form satisfied, the fact not.
IN_FLIGHT_UNMET = NO_LINE + "\n\nIN FLIGHT: the phase-2 executor agent."
INTERRUPT = "[Request interrupted by user]"


# ------------------------------------------------------------- transcripts --
def write_transcript(path, records):
    """A JSONL transcript from a compact description of its records.

    Each record is `("user", text)`, `("assistant", text)`, or a user record
    with harness flags: `("meta", text)`, `("summary", text)`.
    """
    with open(path, "w", encoding="utf-8") as handle:
        for kind, text in records:
            if kind == "assistant":
                record = {"type": "assistant",
                          "message": {"content": [{"type": "text",
                                                   "text": text}]}}
            else:
                record = {"type": "user", "message": {"content": text}}
                if kind == "meta":
                    record["isMeta"] = True
                elif kind == "summary":
                    record["isCompactSummary"] = True
            handle.write(json.dumps(record) + "\n")
    return path


# ------------------------------------------------------------- the controls --
# name -> (records, expected hook exit code, expected fires counted by the walk)
CONTROLS = {
    "no grant anywhere": (
        [("user", "fix the login redirect"), ("assistant", NO_LINE)], 0, 0),
    "a grant, and no state line": (
        [("user", GRANT), ("assistant", NO_LINE)], 2, 1),
    "a grant, and a state line": (
        [("user", GRANT), ("assistant", WITH_LINE)], 0, 0),
    # Both halves of the hole the gate's own designer fell into, within hours
    # of arguing that the form was enough because a lie must be typed on
    # purpose. It was typed, twice, and neither was noticed.
    "a grant, and an in-flight line that negates itself": (
        [("user", GRANT), ("assistant", IN_FLIGHT_NEGATED)], 2, 1),
    "a grant, and an in-flight claim with nothing running": (
        [("user", GRANT), ("assistant", IN_FLIGHT_UNMET)], 2, 1),
    # The failure that missed four of the five real stops: he gives the grant
    # once, then answers questions, and an expiring reading disarms the gate.
    "a grant then ten more messages (standing)": (
        [("user", GRANT)]
        + [item for n in range(10)
           for item in (("assistant", WITH_LINE), ("user", f"ok, {n}"))]
        + [("assistant", NO_LINE)], 2, 1),
    # The nesting failure: reading a field at the wrong level of the record.
    # A grant the harness quoted is not the operator saying it.
    "a grant only inside a system-reminder": (
        [("user", f"<system-reminder>\nremember: {GRANT}\n</system-reminder>"),
         ("assistant", NO_LINE)], 0, 0),
    "a grant only inside a task-notification": (
        [("user", f"<task-notification>\n<summary>{GRANT}</summary>\n"
                  f"</task-notification>"), ("assistant", NO_LINE)], 0, 0),
    # The gate's own refusal is fed back as an isMeta user record. A gate that
    # read it would arm itself.
    "a grant only in the hook's own feedback": (
        [("meta", f"Stop hook feedback: ... {GRANT} ..."),
         ("assistant", NO_LINE)], 0, 0),
    "a grant only inside a compaction summary": (
        [("summary", f"This session is being continued ... he said {GRANT}"),
         ("assistant", NO_LINE)], 0, 0),
    # A reminder appended to a real message must not disqualify the message.
    "a grant beside a system-reminder in the same message": (
        [("user", f"{GRANT}\n<system-reminder>be careful</system-reminder>"),
         ("assistant", NO_LINE)], 2, 1),
}


def self_check(config):
    """Every control, in process and through the real hook. `[]` when clean."""
    failures = []
    root = tempfile.mkdtemp(prefix="grant-calibrate-")
    try:
        for name, (records, expected_code, expected_fires) in CONTROLS.items():
            path = write_transcript(os.path.join(root, "t.jsonl"), records)
            proc = subprocess.run(
                [sys.executable, HOOK],
                input=json.dumps({"cwd": root, "transcript_path": path,
                                  "stop_hook_active": False}),
                capture_output=True, text=True, timeout=30)
            if proc.returncode != expected_code:
                failures.append(
                    f"{name}: the hook exited {proc.returncode}, expected "
                    f"{expected_code}")
            _, _, counted = count_file(path, config)
            if counted != expected_fires:
                failures.append(
                    f"{name}: the walk counted {counted} fires, expected "
                    f"{expected_fires}")
        # The control that must be 0 by construction, asserted on a control
        # population rather than trusted: no grant, many turn-ends, no lines.
        path = write_transcript(
            os.path.join(root, "ungranted.jsonl"),
            [item for n in range(20)
             for item in (("user", f"do task {n}"), ("assistant", NO_LINE))])
        ends, granted, fires = count_file(path, config)
        if (ends, granted, fires) != (20, 0, 0):
            failures.append(
                f"the ungranted control walked to {ends} turn-ends, {granted} "
                f"granted, {fires} fires; expected 20, 0, 0")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return failures


# -------------------------------------------------------------- the walk ----
def count_file(path, config):
    """`(turn_ends, under_grant, fires)` for one transcript.

    A turn end is where the Stop hook runs: the last assistant record before
    the operator speaks again, or before the file ends. A turn the operator
    INTERRUPTED is not one — the hook never ran there — so the pending message
    is dropped when the interrupt marker arrives.

    The grant is decided incrementally and is STANDING: a turn end is granted
    when a grant phrase appeared in something the operator typed BEFORE it.
    """
    ends = granted = fires = 0
    pending = None
    grant = False
    # Mirrors the hook's cross-check. An in-flight claim is only satisfied
    # while something is outstanding that will re-invoke the session, so the
    # walk has to know the same fact at the same point — tracked incrementally
    # because the answer differs turn by turn.
    launched, notified = set(), set()
    try:
        handle = open(path, encoding="utf-8", errors="ignore")
    except OSError:
        return 0, 0, 0

    def _fires(message):
        declared = gate.state_line(message, config)
        if declared == "stopped":
            return False
        if declared == "in-flight":
            return not (launched - notified)
        return True

    with handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            if "<tool-use-id>" in raw:
                notified.update(gate._NOTIFIED.findall(raw))
            try:
                record = json.loads(raw)
            except ValueError:
                continue
            text = gate.assistant_text(record)
            if text is not None:
                pending = text
            content = (record.get("message") or {}).get("content")
            if record.get("type") == "assistant" and isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    args = block.get("input") or {}
                    background = isinstance(args, dict) and args.get("run_in_background")
                    if block.get("name") in gate._REINVOKING_TOOLS \
                            or (block.get("name") == "Bash" and background):
                        launched.add(block.get("id"))
            if text is not None:
                continue
            if record.get("type") != "user":
                continue
            if _is_interrupt(record):
                pending = None  # the turn was cut; Stop never ran
                continue
            typed = gate.human_text(record)
            if not typed:
                continue
            if pending is not None:
                ends += 1
                if grant:
                    granted += 1
                    if pending.strip() and _fires(pending):
                        fires += 1
                pending = None
            if not grant and gate.has_phrase(typed, config["grant_phrases"]):
                grant = True
    if pending is not None:
        ends += 1
        if grant:
            granted += 1
            if pending.strip() and _fires(pending):
                fires += 1
    return ends, granted, fires


def _is_interrupt(record):
    content = (record.get("message") or {}).get("content")
    return isinstance(content, str) and content.startswith(INTERRUPT)


# ------------------------------------------------------------------- main ---
def main():
    parser = argparse.ArgumentParser(
        description="Arm the autonomy-grant gate with a project's own numbers.")
    parser.add_argument("transcript_dir", metavar="TRANSCRIPT-DIR",
                        help="the host's transcript directory for this project")
    parser.add_argument("-p", "--project", default=os.getcwd(), metavar="DIR",
                        help="project root the vocabulary is read from "
                             "(default: the working directory)")
    args = parser.parse_args()

    config, complaint = gate.load_config(args.project)
    failures = self_check(config)
    if failures:
        print("SELF-CHECK FAILED — no numbers printed. The gate is NOT armed.")
        for line in failures:
            print(f"  {line}")
        return 1

    try:
        names = os.listdir(args.transcript_dir)
    except OSError as error:
        print(f"cannot read {args.transcript_dir}: {error}")
        return 1
    paths = sorted(os.path.join(args.transcript_dir, name)
                   for name in names if name.endswith(".jsonl"))
    if not paths:
        print(f"no *.jsonl transcripts in {args.transcript_dir}")
        return 1

    ends = granted = fires = outside = 0
    for path in paths:
        file_ends, file_granted, file_fires = count_file(path, config)
        ends += file_ends
        granted += file_granted
        fires += file_fires
        # The control, read independently: the hook's OWN whole-file predicate,
        # the one production runs, against the walk's incremental standing one.
        if file_fires and not gate.scan(path, config, want_text=False)[0]:
            outside += file_fires

    override = gate.find_config(args.project)
    print(f"vocabulary in force  : "
          f"{override if override else 'the defaults (no override file)'}")
    if complaint:
        print(f"  override complaint : {complaint}")
    prefixes = config["in_flight_prefixes"] + config["stopped_prefixes"]
    print(f"  grant phrases      : {', '.join(config['grant_phrases'])}")
    print(f"  state prefixes     : {', '.join(prefixes)}")
    print(f"  stop reasons       : {', '.join(config['stop_reasons'])}")
    print()
    print(f"transcripts scanned                 : {len(paths)}")
    print(f"turn-ends                           : {ends}")
    print(f"turn-ends under an active grant     : {granted}")
    print(f"  ... of those, lacking a state line: {fires}")
    verdict = "(must be 0)" if outside == 0 else "<-- NOT 0: NOT ARMED"
    print(f"fires with no grant active          : {outside}   {verdict}")
    if outside:
        print("\nThe grant parser is wrong. Do not report this gate as armed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
