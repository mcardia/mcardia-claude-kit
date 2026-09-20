#!/usr/bin/env python3
"""Shared scope detection and patterns for the two operator-decision hooks.

Both hooks answer the same prior question — *does this project run the
operator-decision discipline at all?* — and both recognise the same handful of
things in text. Holding either in two places would be the drift this kit exists
to prevent, so they live here once.

**The scope predicate is the whole design.** A plugin's hooks load in every
project the moment the plugin is installed. An operator-decision gate that
fired everywhere would refuse ordinary work in repositories that never adopted
the rule, and a gate people switch off is a gate that is off. So these hooks
are inert unless the project itself declares the rule: they walk up from the
working directory looking for a constitution that carries an operator-decision
section. A project adopts the enforcement by having the rule, and by nothing
else — no flag, no settings entry, no second file to drift.
"""
import os
import re

# Where a project keeps its constitution, in the order the kit's own generators
# write them. The first one found that carries the section wins.
CONSTITUTION_NAMES = (
    "AGENTS.md",
    "docs/AGENTS.md",
    "CLAUDE.md",
    "docs/methodology.md",
    "docs/standards/methodology.md",
)

# The section heading that declares the discipline. Tolerant of numbering and
# of the two spellings the kit's `constitution` generator can emit.
OD_SECTION = re.compile(
    r"^#{1,6}\s*(?:\d+[.)]\s*)?(?:operator\s+decisions?|decis(?:õ|o)es\s+do\s+operador)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Text that assigns a decision to the operator. Narrow on purpose: these are
# assertions about WHO DECIDES, which is exactly what a grade answers.
OWNERSHIP_CLAIM = re.compile(
    r"operator decision|operator'?s (?:call|at any grade|to|own)|the operator'?s\b"
    r"|awaiting (?:his|the operator'?s) word|aguarda sua palavra"
    r"|registered,? not work|not work until|a finding is not work"
    r"|blocked-by-operator|his at any grade|é seu\b|decis(?:ão|ion) (?:é|is) (?:sua|his)",
    re.IGNORECASE,
)

# The grade the rule produces, spelled AS a grade rather than used as an
# adjective — "a minor change" is prose, "grade: minor" is a disposition.
GRADE_STATED = re.compile(
    r"\bgrade[^\n]{0,40}?\b(low|minor|moderate|major|critical)\b"
    r"|\bgrau[^\n]{0,40}?\b(low|minor|moderate|major|critical)\b"
    r"|\bgrade\s*[:—–-]\s*n/?a\b|\bgrau\s*[:—–-]\s*n/?a\b",
    re.IGNORECASE,
)

# The explicit non-decision: a record of something already decided elsewhere.
# It still owes its anchors — it has to point at where that decision lives —
# but not the panel, because a panel adjudicates and there is nothing here to
# adjudicate. Making it visible in the artifact is the whole of its cost.
GRADE_NA = re.compile(r"\b(?:grade|grau)\s*[:—–-]\s*n/?a\b", re.IGNORECASE)

# A grade above `moderate` IS the handover, whether or not a sentence says so:
# the rule puts everything above that line with the operator. A turn stating
# one owes the record even when it hands over in no other words.
ABOVE_MODERATE = re.compile(
    r"(?:\bgrau\b|\bgrade\b)[^\n]{0,60}?\b(major|critical)\b", re.IGNORECASE)

# `path/to/file.ext:123` — where the cause and the remedy were verified.
ANCHOR = re.compile(r"[\w./-]+\.[A-Za-z0-9]{1,6}:\d+")
MIN_ANCHORS = 2

# The adversarial panel. A magic string only proves the sentence was written,
# not that the panel ran — which is why the panel ships as a saved workflow
# (`od-gate`): the check makes skipping it visible, and being one call is what
# makes running it the cheap path. A check that made the correct path the
# expensive one would lose to the shortcut, which is how this rule failed
# before it was a mechanism.
PANEL = re.compile(
    r"\bod-gate\b|§13 panel|painel §13|tr(?:ê|e)s lentes"
    r"|three (?:independent )?lenses|adversarial(?:ly)?[- ]verif"
    r"|lentes? e (?:um )?cr(?:í|i)tico|lenses? and (?:a )?critic"
    # A project's own adversarial structure for diffs, where the panel
    # adjudicates a decision. Same standing.
    r"|cascata de tr(?:ê|e)s est(?:á|a)gios|cascade stage \d|three-stage cascade"
    r"|MERGE VERDICT",
    re.IGNORECASE,
)


def find_constitution(cwd):
    """The nearest enclosing project whose constitution declares the rule.

    Returns `(project_root, constitution_path)`, or `None` when no ancestor
    directory carries one — in which case the caller must do nothing at all.
    """
    if not cwd:
        return None
    try:
        current = os.path.realpath(cwd)
    except OSError:
        return None
    if not os.path.isdir(current):
        return None
    while True:
        for name in CONSTITUTION_NAMES:
            candidate = os.path.join(current, name)
            try:
                with open(candidate, encoding="utf-8", errors="ignore") as handle:
                    if OD_SECTION.search(handle.read()):
                        return current, candidate
            except OSError:
                continue
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def git_config_path(project_root):
    """The project's git config, resolving a worktree or submodule `.git` file.

    In a linked worktree `.git` is a FILE reading `gitdir: <path>`, and the
    config lives in the COMMON directory that `<path>/commondir` points at, not
    beside it. Missing that is not cosmetic: every remote would read as unknown
    from inside any worktree, and this operator works in worktrees.
    """
    dot_git = os.path.join(project_root, ".git")
    if os.path.isdir(dot_git):
        return os.path.join(dot_git, "config")
    try:
        with open(dot_git, encoding="utf-8", errors="ignore") as handle:
            match = re.match(r"\s*gitdir:\s*(.+?)\s*$", handle.read())
    except OSError:
        return None
    if not match:
        return None
    gitdir = match.group(1)
    if not os.path.isabs(gitdir):
        gitdir = os.path.join(project_root, gitdir)
    direct = os.path.join(gitdir, "config")
    if os.path.exists(direct):
        return direct
    try:
        with open(os.path.join(gitdir, "commondir"), encoding="utf-8",
                  errors="ignore") as handle:
            common = handle.read().strip()
    except OSError:
        return None
    if not os.path.isabs(common):
        common = os.path.join(gitdir, common)
    return os.path.join(common, "config")


def remote_slugs(project_root):
    """`owner/name` for every git remote of the project, lowercased.

    Read out of the git config rather than by running git: a hook runs on every
    matching tool call and must not pay for a subprocess. Returns an empty set
    when there is no readable config, which callers treat as "cannot tell".
    """
    slugs = set()
    config = git_config_path(project_root)
    if not config:
        return slugs
    try:
        with open(config, encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    except OSError:
        return slugs
    for url in re.findall(r"^\s*url\s*=\s*(\S+)", text, re.MULTILINE):
        # git@host:owner/name.git | https://host/owner/name(.git) | ssh://…
        match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
        if match:
            slugs.add(f"{match.group(1)}/{match.group(2)}".lower())
    return slugs
