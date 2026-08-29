# evals

One minimal case per surviving component of `sdd-generators`, so the question
"does this plugin earn its always-on token cost" gets a number instead of an
argument.

```sh
claude plugin eval plugins/sdd-generators \
  --ablation with-without \
  --allow-tools Bash Write Edit \
  --judge-model sonnet \
  --max-cost-usd 60
```

Target the plugin **by path**, not by name. `evals/` ships inside the plugin root, so a
name target does not error — it silently resolves the *installed* snapshot and scores
that instead of this working tree, which is the worse failure. Results land in
`plugins/sdd-generators/evals/results/<timestamp>/`.

`--allow-tools` is the operator grant for **gated** tools only (`Bash`, `Write`, `Edit`,
`WebFetch`, `mcp__*`). `Skill`, `Agent`, `Read`, `Glob` and `Grep` are not gated, so they
are governed by each case's own `allowed_tools` and need no grant here.

The ceiling is deliberately loose: 9 cases x `runs: 3` x 2 ablation arms is ~54 agent
runs, and hitting `--max-cost-usd` aborts mid-suite with exit 2 and partial results.

`--judge-model` matters: every scored `llm` grader carries the discipline signal,
and the default judge is haiku. Judge at sonnet tier or above, or the rubrics get
graded more coarsely than they were written.

`--ablation with-without` runs each case twice — once with the plugin, once
without — and reports the score delta. That delta is the plugin's value: if a
case scores the same in both arms, the component it covers is not earning its
place.

Each case is graded on the **discipline the component adds**, never on "a
document appeared" — the no-plugin arm produces documents too. The scored
graders check the things the plugin exists to enforce: one decision per ADR,
WHAT separated from HOW, a naming registry the diagrams actually use, an unowned
requirement raised rather than absorbed, a planted contradiction caught with
file evidence.

So that the delta is not diluted, the discipline grader in each case outweighs the
existence graders around it — existence is largely something the no-plugin arm also
achieves, and a case scored mostly on it reports a delta near zero no matter how much
the plugin actually added.

The `tool_used: Skill` graders carry no `arm:`, so under ablation they are a
plugin-fired indicator rather than part of the score. The `tool_used: Agent` graders
match on `subagent_type`, never on the agent's name appearing in the prompt text —
otherwise the no-plugin arm passes them by relaying the word.

Two notes for anyone editing these cases:

- `focus: files` exposes only the **list of paths** created during a run, never
  file contents. To grade what a file says, point the grader at
  `{source: file, path: ...}` — which is why each prompt pins its output path.
- Cases run in a sandbox cwd. No absolute paths and no `~/` in prompts or
  graders.
