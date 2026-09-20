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
refuse nothing unless the project itself declares the rule: they walk up from
the working directory looking for a constitution that carries an
operator-decision section. A project adopts the enforcement by having the rule,
and by nothing else — no flag, no settings entry, no second file to drift.

Refusing nothing is not costing nothing. Each hook is a `python3` process,
measured at about 17 ms per Bash call and per turn end, in every project.

**The constitution is the authority, so the vocabulary is read out of it.**
The grade words and the line above which the operator decides are the
project's, never this file's. `grade_vocabulary()` parses them from the section
the hooks already open. When the parse fails the hooks degrade to a weaker
check that is still true — never to some other project's words.

    python3 check-od-record.py --explain [dir]

prints what was resolved for a directory: the constitution, the vocabulary and
the threshold. That is the only way to see whether a project is gated, and by
which file.
"""
import collections
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

# The section heading that declares the discipline, and the whole of the opt-in.
# Tolerant of numbering, of the two spellings the `constitution` generator in
# the kit's `sdd-generators` plugin can emit, and of the few near-synonyms a
# project is likely to reach for.
# Deliberately not wider than that: a heading set loose enough to catch every
# phrasing would switch the gate on in projects that never adopted the rule,
# which is the failure this predicate exists to avoid. A project whose heading
# is not here gets no enforcement — run `--explain` to see that it is not gated.
OD_SECTION = re.compile(
    r"^#{1,6}\s*(?:\d+[.)]\s*)?(?:"
    r"operator[- ]decisions?(?:\s+(?:gate|rule))?"
    r"|decis(?:õ|o)es\s+do\s+operador"
    r"|decisions?\s+reserved\s+(?:to|for)\s+the\s+(?:operator|owner)"
    r"|decisions?\s+(?:that\s+are\s+)?the\s+operator'?s"
    r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Text that ASSIGNS a decision. Every phrase here is PERFORMATIVE: it only
# gets written when the writer is handing something over. Nothing here is a
# bare possessive, a policy catchphrase, or a phrase that can merely DESCRIBE
# an item — that distinction is the whole of the narrowing, and it was measured
# rather than argued.
#
# Measured over 200 real comment bodies from this estate's three tracker
# repositories: the earlier pattern refused 40 of them — one in five — almost
# all on `the operator's` alone ("the operator's `db` container", "the
# operator's local tsc") or on a policy catchphrase quoted inside a findings
# document. This pattern refuses 0 of the same 200 while still catching every
# constructed handover in the review's harnesses.
#
# Two phrases the review proposed keeping are NOT here, because measurement
# refuted them: `operator's call` and an indefinite `an/one operator decision`
# appear in this estate's cascade findings documents as DESCRIPTIONS of an item
# ("whether this item owns provisioning it is the operator's call"), and keeping
# either holds the refusal rate at 12 of 200. `the operator decision` — definite
# article, no hyphen, so "the operator-decision section" is prose about the rule
# — keeps the canonical handover sentence gated.
OWNERSHIP_CLAIM = re.compile(
    r"\bthe operator decision\b"
    r"|\b(?:this|that|it)(?:'s|\s+(?:is|was|remains|stays))\s+(?:an?|the)\s+"
    r"operator[- ]decision\b"
    r"|\bawaiting (?:his|your|the operator'?s) word\b"
    r"|aguarda(?:m|ndo)? (?:a )?sua palavra"
    r"|\bblocked-by-operator\b"
    r"|\byours to (?:decide|call|rule|settle)\b"
    r"|\bfor you to (?:decide|call|rule|settle)\b"
    r"|\b(?:é|e) sua decis(?:ão|ao)\b|\bdecis(?:ão|ao) (?:é|e) sua\b",
    re.IGNORECASE,
)

# The explicit non-decision: a record of something already decided elsewhere.
# It still owes its anchors — it has to point at where that decision lives —
# but not the panel, because a panel adjudicates and there is nothing here to
# adjudicate. Making it visible in the artifact is the whole of its cost.
#
# This one stays a constant on purpose: `n/a` is the hook's own spelling for
# "no grade to give", and carries no word out of anybody's constitution. A
# function taking a vocabulary it would never read would be a worse lie than
# the constant.
GRADE_NA = re.compile(r"\b(?:grade|grau)\s*[:—–=-]\s*n/?a\b", re.IGNORECASE)

# The label a grade is written under. This is a recognition vocabulary for
# FINDING a grade in text, not a rule about what a grade may be called; the
# WORDS are the constitution's and are parsed from it below.
_LABEL = r"(?:grade|grau)(?![\w-])"

# A grade is STATED when its label heads a clause and the word follows it
# closely: `Grade: major`, `| Grau | crítico |`, `**Grade:** minor`.
#
# The anchor is NOT a claim about the form a grade must take. No constitution
# this plugin has read says one, and quoting one as if it did is the drift
# this file exists to prevent. What the anchor does is keep a turn that
# EXPLAINS the rule from blocking itself: explaining it reads "then grade the
# change with one word: `low`, `minor`, …", and without the anchor the gate
# refuses the very turn that edits the rule it enforces. The reviewer
# reproduced exactly that.
#
# `(?<![^\W\d_][ \t])` rejects a label preceded by a word — "the grade of the
# regression is minor", "que diga grade major" — while leaving a label that
# starts a line, a bullet, a table cell or a clause after `:`, `—`, `**`.
_CLAUSE_START = r"(?<![^\W\d_][ \t])"
_GAP = 24

GradeVocabulary = collections.namedtuple("GradeVocabulary", "words threshold")
"""`words` in the constitution's own order; `threshold` indexes the word the
section draws the line at, or is None when the section states no line."""

# The sentence that introduces the grade is the one that uses the verb.
_GRADE_VERB = re.compile(r"\bgrad(?:e[sd]?|ing)\b|\bgrau\b|\bgradua", re.IGNORECASE)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_BACKTICKED = re.compile(r"`([^`\n]{1,32})`")
_ONE_WORD = re.compile(r"^[^\W\d_][\w-]*$", re.UNICODE)
_MAX_WORDS = 12


def section_text(text):
    """The body of the operator-decision section, or None."""
    match = OD_SECTION.search(text)
    if not match:
        return None
    level = len(re.match(r"\s*(#+)", match.group(0)).group(1))
    rest = text[match.end():]
    following = re.compile(r"^#{1,%d}\s+\S" % level, re.MULTILINE).search(rest)
    return rest[:following.start()] if following else rest


def grade_vocabulary(text):
    """The project's grade words and threshold, read out of its constitution.

    The vocabulary is the ordered backticked one-word tokens of the sentence
    that introduces the grade — "grade the change with one word: `low`,
    `minor`, `moderate`, `major`, `critical`". The threshold is the word the
    section puts the line at — "At `moderate` or below …", "Above `moderate`".

    Returns None when the section states no vocabulary. Callers must then fall
    back to a weaker check that is still true, never to another project's
    words: the whole defect this function exists to remove was the five words
    of one estate's constitution shipped as if they were everybody's.
    """
    body = section_text(text)
    if not body:
        return None
    for sentence in _SENTENCE.split(body):
        if not _GRADE_VERB.search(sentence):
            continue
        words, seen = [], set()
        for token in _BACKTICKED.findall(sentence):
            token = token.strip().lower()
            if _ONE_WORD.match(token) and token not in seen:
                seen.add(token)
                words.append(token)
        if 2 <= len(words) <= _MAX_WORDS:
            return GradeVocabulary(tuple(words), _threshold_index(body, words))
    return None


def _threshold_index(body, words):
    """Which word the section draws the line at, or None if it draws none."""
    alternation = "|".join(re.escape(word) for word in words)
    for pattern in (
        r"\bat\s+`?(%s)`?\s+or\s+below" % alternation,
        r"`?(%s)`?\s+or\s+below" % alternation,
        r"\babove\s+`?(%s)`?" % alternation,
        r"\bacima\s+de\s+`?(%s)`?" % alternation,
        r"`?(%s)`?\s+ou\s+(?:abaixo|menos)" % alternation,
    ):
        found = re.search(pattern, body, re.IGNORECASE)
        if found:
            return words.index(found.group(1).lower())
    return None


def grade_stated(vocabulary):
    """A pattern matching a grade written as a grade.

    With a vocabulary, the word must be one of the project's. Without one, the
    check degrades to "a grade label carries some value" — weaker, and true.
    Guessing this estate's words in somebody else's project is the defect.
    """
    if vocabulary is None:
        return re.compile(
            r"%s%s\s*[:—–=-]\s*[^\W\d_][\w/-]*" % (_CLAUSE_START, _LABEL),
            re.IGNORECASE)
    alternation = "|".join(re.escape(word) for word in vocabulary.words)
    return re.compile(
        r"%s%s[^\n]{0,%d}?\b(?:%s)\b|%s"
        % (_CLAUSE_START, _LABEL, _GAP, alternation, GRADE_NA.pattern),
        re.IGNORECASE)


def stated_grades(text, vocabulary):
    """Every grade word this text states, in order of appearance.

    The word taken is the nearest one after the label, so "Grade: minor, and
    the critical path is unchanged" states `minor` and not `critical`.
    """
    if vocabulary is None:
        return []
    alternation = "|".join(re.escape(word) for word in vocabulary.words)
    pattern = re.compile(
        r"%s%s[^\n]{0,%d}?\b(%s)\b" % (_CLAUSE_START, _LABEL, _GAP, alternation),
        re.IGNORECASE)
    return [match.group(1).lower() for match in pattern.finditer(text)]


def above_threshold(text, vocabulary):
    """True when the text states a grade the constitution puts above the line.

    Skipped entirely — always False — when the vocabulary or the threshold
    could not be read. A guessed threshold would be this estate's rule wearing
    another project's name.
    """
    if vocabulary is None or vocabulary.threshold is None:
        return False
    above = set(vocabulary.words[vocabulary.threshold + 1:])
    return any(word in above for word in stated_grades(text, vocabulary))


# `path/to/file.ext:123` — where the cause and the remedy were verified.
# A host and a port have the same shape (`example.com:8080`), so an anchor
# counts only when it carries a directory or a source-file extension. Every
# real "where verified" anchor carries a path; the extension list is what keeps
# a bare `login.go:844` working, and is lexical rather than policy.
_ANCHOR = re.compile(
    r"(?<![\w:/-])([\w./-]*[\w-])\.([A-Za-z][A-Za-z0-9]{0,5}):(\d{1,7})(?!\w)")
SOURCE_EXTENSIONS = frozenset("""
    c cc cpp cxx h hpp cs java kt kts scala swift m mm rs go rb php pl pm py pyi
    js mjs cjs jsx ts tsx vue svelte sql graphql proto thrift
    sh bash zsh fish ps1 bat
    md mdx rst txt adoc org tex
    json yaml yml toml ini cfg conf properties env lock mod sum
    html htm css scss sass less xml xsd xsl svg
    tf tfvars hcl gradle bzl cmake mk make dockerfile puml plantuml mermaid
    ipynb r jl lua dart ex exs erl hs ml clj cljs groovy vb f90 asm s
""".split())
MIN_ANCHORS = 2
# Two DISTINCT anchor strings, which two lines of one file satisfy. Kept that
# way on purpose: a cause and its remedy are very often one function and its
# caller in the same file, and requiring two files would make that record
# impossible to write truthfully. "Two places" is two places, not two files.


def anchors(text):
    """The distinct source anchors in the text."""
    found = set()
    for match in _ANCHOR.finditer(text):
        path, extension = match.group(1), match.group(2).lower()
        if "/" in path or extension in SOURCE_EXTENSIONS:
            found.add(match.group(0))
    return found


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


def _home():
    """The real path of `$HOME`, or None when it is unset or unusable."""
    home = os.environ.get("HOME") or ""
    if not home:
        return None
    try:
        return os.path.realpath(home)
    except OSError:
        return None


def find_constitution(cwd):
    """The nearest enclosing project whose constitution declares the rule.

    Returns `(project_root, constitution_path)`, or `None` when no ancestor
    directory carries one — in which case the caller must do nothing at all.

    The walk stops BELOW `$HOME`: a `CLAUDE.md` or `AGENTS.md` in the home
    directory is a person's standing instructions, not a project's
    constitution, and letting one switch the gate on would gate every project
    on the machine including those that never adopted the rule. When `$HOME`
    is unset, or the working directory is outside it, the walk runs to `/` as
    before — refusing to look at all would be a silent no-op.

    A working directory that no longer exists is NOT a reason to stop. Its
    ancestors still do, and the session keeps running in it — a branch checkout
    or a deleted scratch directory is enough to produce one. Returning None
    there switched the whole gate off for the rest of the session, silently;
    the `open()` calls below already fail closed on a path that is not there.
    """
    if not cwd:
        return None
    try:
        current = os.path.realpath(cwd)
    except OSError:
        return None
    home = _home()
    if home is not None and not (current == home
                                 or current.startswith(home + os.sep)):
        home = None  # outside it: `$HOME` bounds nothing here
    while True:
        if current == home:
            return None
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


def read_vocabulary(constitution):
    """The grade vocabulary of a constitution path, or None."""
    try:
        with open(constitution, encoding="utf-8", errors="ignore") as handle:
            return grade_vocabulary(handle.read())
    except OSError:
        return None


def explain(cwd):
    """One paragraph saying whether a directory is gated, and by what.

    There is otherwise no way to ask the question, and a project whose heading
    `OD_SECTION` does not recognise looks identical to one that is gated and
    quiet. This also shows what the vocabulary parser actually read.
    """
    found = find_constitution(cwd)
    if not found:
        return (f"operator-decision gate: INERT for {cwd}\n"
                f"  no ancestor directory (below $HOME) carries a constitution "
                f"with an operator-decision section.\n"
                f"  looked for: {', '.join(CONSTITUTION_NAMES)}")
    project_root, constitution = found
    vocabulary = read_vocabulary(constitution)
    lines = [f"operator-decision gate: ACTIVE for {cwd}",
             f"  project root:  {project_root}",
             f"  constitution:  {constitution}"]
    if vocabulary is None:
        lines.append("  vocabulary:    NOT PARSED — the section states no grade "
                     "words. A grade label with any value satisfies the check, "
                     "and the above-threshold rule is skipped entirely.")
    else:
        lines.append(f"  vocabulary:    {', '.join(vocabulary.words)}")
        if vocabulary.threshold is None:
            lines.append("  threshold:     NOT PARSED — the section draws no "
                         "line. The above-threshold rule is skipped entirely.")
        else:
            at = vocabulary.words[vocabulary.threshold]
            above = vocabulary.words[vocabulary.threshold + 1:]
            lines.append(f"  threshold:     {at} "
                         f"(above it: {', '.join(above) or 'nothing'})")
    return "\n".join(lines)
