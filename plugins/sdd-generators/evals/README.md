# evals

One minimal case per surviving component of `sdd-generators`, so the question
"does this plugin earn its always-on token cost" gets a number instead of an
argument.

```sh
claude plugin eval sdd-generators \
  --ablation with-without \
  --allow-tools Bash Write Edit \
  --max-cost-usd 15
```

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

The `tool_used: Skill` graders carry no `arm:`, so under ablation they are a
plugin-fired indicator rather than part of the score.

Two notes for anyone editing these cases:

- `focus: files` exposes only the **list of paths** created during a run, never
  file contents. To grade what a file says, point the grader at
  `{source: file, path: ...}` — which is why each prompt pins its output path.
- Cases run in a sandbox cwd. No absolute paths and no `~/` in prompts or
  graders.
