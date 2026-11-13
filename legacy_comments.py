#!/usr/bin/env python3
"""Add "why" comments to a legacy codebase, one API call per file, under a hard budget.

The model never rewrites code. It answers a JSON list of insertions
(line number + comment text); this script inserts each comment above its
line, copying that line's indentation, into a COPY of the tree under
--out. The original tree is never modified.

Every "why" comment must name its source: a commit hash, a ticket id, a
test name, or the marker INFERRED. A report lists every INFERRED comment
so a stronger model or a human can confirm it before it feeds an ADR.

Usage:
  export ANTHROPIC_API_KEY=...
  python3 legacy_comments.py -s ~/src/legacy -o ~/src/legacy-commented -b 3.00
  python3 legacy_comments.py -s ~/src/legacy -o ~/out -b 3.00 --dry-run

Stdlib only (urllib); no SDK needed.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"

# Comment prefix per file extension. Files with any other extension are skipped.
PREFIX = {
    ".py": "#", ".rb": "#", ".sh": "#", ".pl": "#", ".r": "#", ".yaml": "#", ".yml": "#",
    ".js": "//", ".jsx": "//", ".ts": "//", ".tsx": "//", ".go": "//", ".java": "//",
    ".c": "//", ".h": "//", ".cpp": "//", ".hpp": "//", ".cs": "//", ".php": "//",
    ".kt": "//", ".swift": "//", ".rs": "//", ".scala": "//", ".dart": "//",
    ".sql": "--", ".lua": "--",
}
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".venv", "venv", "__pycache__", "target"}

SYSTEM_PROMPT = """You add explanatory comments to legacy source code. The comments are a first step: \
later, architecture decision records and specifications will be reverse-engineered from the code, its \
history and these comments, so a wrong comment becomes a wrong decision on record.

RULES
1. Explain WHY, not WHAT. The code already shows what it does. Write a comment only where a reader \
would ask "why is it like this?": a non-obvious condition, a magic number, an odd ordering, a workaround, \
a business rule, an error that is deliberately swallowed, a retry, a lock, a cache, a special case.
2. Every comment that states a reason MUST end with its source in square brackets:
   - [commit <short-hash>] when the provided git history shows the reason;
   - [ticket <id>] when a ticket or issue id in the history or the code shows it;
   - [test <name>] when a test in the provided context pins the behaviour;
   - [INFERRED] when the reason is your reading of the code alone.
   Never present an inferred reason as fact. If you cannot tell why, prefer no comment over a guess; if \
the spot is important anyway, write "Why this is so is unknown" and mark it [INFERRED].
3. Never claim a guarantee the code does not enforce (no "always", "never", "guaranteed", "thread-safe", \
"validated" unless the code right there makes it true). State only what the code does or what the cited \
source shows.
4. One to three short lines per comment, plain English, no restating of names, no TODOs, no praise, no \
blame. Do not comment trivial lines, imports, getters or obvious loops.
5. Do not change, move or remove any code. Do not repeat a comment that is already present.

OUTPUT
Answer with ONLY a JSON array, no prose, no code fences. Each element:
  {"line": <1-based line number the comment goes ABOVE>, "comment": "<text without the comment prefix>"}
Use "\\n" inside "comment" for a multi-line comment. Answer [] if nothing in the file needs a comment."""


def parse_args():
    p = argparse.ArgumentParser(description="Add sourced 'why' comments to a legacy tree under a budget.")
    p.add_argument("-s", "--src", required=True, help="root of the legacy source tree (read only)")
    p.add_argument("-o", "--out", required=True, help="output root; a commented copy is written here")
    p.add_argument("-b", "--budget", type=float, default=3.0, help="hard spend cap in USD (default 3.00)")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"model id (default {DEFAULT_MODEL})")
    p.add_argument("-i", "--price-in", type=float, default=3.0,
                   help="USD per million input tokens; CHECK the current price (default 3.0)")
    p.add_argument("-u", "--price-out", type=float, default=15.0,
                   help="USD per million output tokens; CHECK the current price (default 15.0)")
    p.add_argument("-c", "--max-chars", type=int, default=60000, help="skip files larger than this (default 60000)")
    p.add_argument("-g", "--git-commits", type=int, default=15, help="commits of history sent per file (default 15)")
    p.add_argument("-n", "--dry-run", action="store_true", help="list files and estimated input cost, call nothing")
    return p.parse_args()


def source_files(root):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in PREFIX and not (set(path.parts) & SKIP_DIRS):
            yield path


def git_history(root, path, count):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", f"-{count}", "--format=%h %ad %s", "--date=short", "--", str(path)],
            capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or "(no git history)"
    except (OSError, subprocess.TimeoutExpired):
        return "(no git history)"


def numbered(text):
    return "\n".join(f"{n:5d}| {line}" for n, line in enumerate(text.split("\n"), 1))


def call_model(args, user_text):
    body = {
        "model": args.model,
        "max_tokens": 4096,
        "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_text}],
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), method="POST", headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as err:
            if err.code in (429, 500, 502, 503, 529) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise


def cost_of(usage, args):
    tokens_in = (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) * 1.25
                 + usage.get("cache_read_input_tokens", 0) * 0.1)
    return tokens_in * args.price_in / 1e6 + usage.get("output_tokens", 0) * args.price_out / 1e6


def insert_comments(text, insertions, prefix):
    lines = text.split("\n")
    for item in sorted(insertions, key=lambda x: x["line"], reverse=True):
        at = int(item["line"]) - 1
        if not 0 <= at <= len(lines):
            continue
        anchor = lines[at] if at < len(lines) else ""
        indent = anchor[:len(anchor) - len(anchor.lstrip())]
        block = [f"{indent}{prefix} {part}".rstrip() for part in str(item["comment"]).split("\n")]
        lines[at:at] = block
    return "\n".join(lines)


def main():
    args = parse_args()
    src, out = pathlib.Path(args.src).expanduser().resolve(), pathlib.Path(args.out).expanduser().resolve()
    if out == src or src in out.parents:
        sys.exit("--out must be outside --src")
    files = [f for f in source_files(src) if f.stat().st_size <= args.max_chars]
    est = sum(f.stat().st_size for f in files) / 4 * args.price_in / 1e6
    print(f"{len(files)} files, estimated input cost USD {est:.2f} (output not included)")
    if args.dry_run:
        return
    if "ANTHROPIC_API_KEY" not in os.environ:
        sys.exit("ANTHROPIC_API_KEY is not set")
    spent, inferred, report = 0.0, [], []
    for path in files:
        if spent >= args.budget:
            print(f"BUDGET REACHED at USD {spent:.2f}; stopped before {path.relative_to(src)}")
            break
        rel = path.relative_to(src)
        text = path.read_text(errors="replace")
        user = (f"FILE: {rel}\n\nGIT HISTORY (newest first):\n{git_history(src, path, args.git_commits)}\n\n"
                f"SOURCE (line numbers on the left are not part of the file):\n{numbered(text)}")
        try:
            resp = call_model(args, user)
        except Exception as err:  # keep going; one bad file must not lose the run
            report.append(f"{rel}: ERROR {type(err).__name__}")
            continue
        spent += cost_of(resp.get("usage", {}), args)
        raw = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
        try:
            insertions = json.loads(raw)
        except json.JSONDecodeError:
            report.append(f"{rel}: unparseable answer, left uncommented")
            insertions = []
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(insert_comments(text, insertions, PREFIX[path.suffix.lower()]))
        for item in insertions:
            if "[INFERRED]" in str(item.get("comment", "")):
                inferred.append(f"{rel}:{item.get('line')}: {item.get('comment')}")
        report.append(f"{rel}: {len(insertions)} comments")
        print(f"USD {spent:.2f}  {rel}: {len(insertions)} comments")
    (out / "_report.txt").write_text("\n".join(report) + f"\n\nTOTAL USD {spent:.2f}\n")
    (out / "_inferred.txt").write_text("\n".join(inferred) + "\n")
    print(f"done: USD {spent:.2f}; {len(inferred)} INFERRED comments listed in {out / '_inferred.txt'}")


if __name__ == "__main__":
    main()
