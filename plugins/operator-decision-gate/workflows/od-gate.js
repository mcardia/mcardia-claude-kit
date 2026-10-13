/*
 * The operator-decision gate, as an adversarial panel.
 *
 * Saved here rather than re-authored per use because the cheapest path has to
 * be the correct one, or it loses to the shortcut. Running the whole panel is
 * one call.
 *
 * Why a panel and not one verifier. Records produced without one carried
 * grounds that evaporated when read at source: a decision document said to cap
 * something it does not cap, and an operator ruling said to be reversed turned
 * out to be conditional with its condition already discharged. A single pass
 * checks whether a finding is real; it does not check whether the REASON given
 * for handing it over is real. Three lenses briefed to refute, and a critic
 * over the whole set, is what caught both.
 *
 * Shape: per item, three independent lenses (cause / remedy / ownership) run
 * concurrently; a synthesiser turns those three reports into the record as
 * structured output; then ONE critic reads every record together — that
 * barrier is deliberate, because the questions it asks (category
 * mis-assignment in both directions, interactions between remedies, what no
 * lens was pointed at) are cross-item by nature.
 *
 * What each lens MEANS is defined in the `od-lens` agent and nowhere else.
 * This script names the lens and never restates its definition. The RECORD
 * schema below is a different thing: its field descriptions are the cue the
 * synthesiser reads at the moment it fills each field, so a few of them do
 * echo a rule the agent owns. That is deliberate — a bare `Field 2` steers
 * nothing — and it is why they are worded as cues rather than as the rule.
 * Where any of them differs from the agent or from the project constitution,
 * those win and the synthesiser is told to say so.
 *
 * The judged round. Two kinds of record get one more round: a record whose
 * grade sits ABOVE the constitution's line, and a record that CLAIMS one of
 * the categories the constitution reserves to the operator at every grade. A
 * refuter attacks it at source — the category claim first, where there is
 * one, then the recommendation — and a judge reads the record, the critic and
 * the refutation, rules whether ANY reserved category applies to the record —
 * the one it claims or another — and states its confidence in the
 * recommendation on the scale the `od-lens` agent defines. The route follows
 * from that:
 *
 *   - at or below the line, no category claimed, not judged  -> session
 *   - judged, and the judge does not rule `reserved_category_applies: false`
 *                                                           -> operator
 *   - judged, no reserved category applies, at or below the line
 *                                                           -> session only
 *     when the judge's confidence is `high` or above; operator otherwise
 *   - judged, no reserved category applies, above the line  -> session only
 *     when the judge's confidence is `high` or above AND the judge quotes the
 *     constitution sentence that admits a judged lane; operator otherwise
 *
 * One field, one meaning: `reserved_category_applies` is about the record, not
 * about its claim, and only an explicit `false` releases — so a claim spelled
 * oddly, or a wrong category named where another applies, cannot reach the
 * session through a judge's `false`. A claimed category that falls below the
 * line still needs the judge's `high`: the record may carry the very
 * narrowing of decided text that made the claim, and the judge marks that
 * recommendation `low`.
 *
 * Why a claimed category is judged too. A claim the ownership lens makes and
 * nobody tests goes to the operator unverified, which is the escape the panel
 * exists to stop: the recorded case was a reserved claim resting on the
 * record's own recommendation — a cheap remedy that narrowed what the corpus
 * had decided, and was then called "undecided" because it narrowed it. The
 * `od-lens` rules make the recommendation conform to decided text; this round
 * checks the claim against the corpus before the operator ever sees it.
 *
 * The admission clause is why the lane is safe to ship to every project: the
 * plugin never moves a decision the constitution gives the operator. A
 * project whose operator-decision section does not admit a judged lane gets
 * the extra round as evidence and the same route it had before; a category
 * claim the judge upholds stays with the operator whatever the confidence.
 *
 * Agent count is 4N + 1 + 2M, M being the records judged — those above the
 * line plus those claiming a category. Pass few items.
 *
 * args — either an array of items, or { items, corpus, code, repo }:
 *   corpus  optional path to the design corpus, when it is not the working
 *           directory (a separate documentation repository, say)
 *   code    optional path to the code tree, same
 *   repo    optional `owner/name` for items given as bare issue numbers
 *   items   each is either an issue number, or { key, title, brief } where
 *           `brief` states the finding in full
 */
export const meta = {
  name: 'od-gate',
  description: 'Run the operator-decision gate as an adversarial panel: three lenses per finding, a synthesiser, one critic over the set, and a refuter and a judge for each record above the line or claiming a reserved category',
  whenToUse: 'Before any operator decision is written down — asked or reported. Invoked by /operator-decision-gate:od.',
  phases: [
    { title: 'Lenses', detail: 'cause, remedy and ownership, briefed to refute, per finding' },
    { title: 'Synthesis', detail: 'the record fields per finding, from the three lens reports' },
    { title: 'Critic', detail: 'one pass over every record: categories, grades, performability, interactions' },
    { title: 'Refute', detail: 'records above the line or claiming a reserved category: one refuter attacks the category claim and the recommendation at source' },
    { title: 'Judge', detail: 'the same records: whether the category claim holds, confidence on a fixed scale, and the route they yield' },
  ],
}

const AGENT = 'operator-decision-gate:od-lens'

const input = Array.isArray(args) ? { items: args } : (args || {})
const items = (input.items || []).filter(Boolean)
if (!items.length) throw new Error('od-gate: args must carry at least one finding')

const ROOTS = [
  input.corpus ? `Design corpus (THE AUTHORITY): ${input.corpus}` : null,
  input.code ? `Code: ${input.code}` : null,
  (input.corpus || input.code)
    ? null
    : 'The project is your working directory. Find its constitution yourself — '
      + '`AGENTS.md`, `docs/AGENTS.md` or the methodology document — and read '
      + 'its operator-decision section before anything else.',
].filter(Boolean).join('\n')

/*
 * The shape the synthesiser returns. The project constitution is the authority
 * on what an operator-decision record contains; this is the transport, and
 * where the two differ the constitution wins and the synthesiser says so in
 * its own text.
 */
const RECORD = {
  type: 'object',
  properties: {
    key: { type: 'string' },
    one_line: { type: 'string', description: 'What this is, in one sentence of plain words.' },
    cause_verdict: { type: 'string', enum: ['CONFIRMED', 'PARTLY_CONFIRMED', 'REFUTED', 'UNVERIFIABLE'] },
    decision: { type: 'string', description: 'Field 1 — what is being decided, one sentence.' },
    how_things_stand: { type: 'string', description: 'Field 2 — a reachable scenario: a named actor doing a named thing and what they observe. Never a description of a mechanism.' },
    why: { type: 'string', description: 'Field 3 — the mechanism and the decision or omission that produced it, with anchors.' },
    recommendation_verb: { type: 'string', enum: ['KEEP', 'CHANGE'] },
    recommendation: { type: 'string', description: 'Field 4 — if CHANGE, exactly what changes: files, functions, contract rows. Executable as written by a fresh agent. Where the corpus decides the behavior, this is the branch that conforms to it.' },
    branches: { type: 'string', description: 'Every way forward, the recommended one first: for each, what it changes, its files-changed estimate and its grade. A branch that narrows or reverses decided text is listed here, priced and named as a change to the operator\'s decision, never recommended.' },
    cheapest_tier: { type: 'string', description: 'Every rung of the sizing ladder enumerated, and which one the remedy sits at. The ladder is the constitution\'s where it states a sizing policy, otherwise the plugin\'s four — say which was used.' },
    grade: { type: 'string', description: 'One word, taken from the grade vocabulary the project constitution states in its operator-decision section. Use that section\'s words exactly; do not substitute a scale from anywhere else.' },
    above_line: { type: 'boolean', description: 'True when the constitution\'s operator-decision section puts this grade above the line it draws — the side where the operator decides.' },
    operator_axis: { type: 'string', description: 'The operator-only category this touches, named as the constitution names it, or `none`.' },
    operator_axis_quote: { type: 'string', description: 'If a category is claimed, the corpus sentence that makes it one, quoted with file and line; where the category turns on what is already decided, the search showing no corpus sentence decides the behavior; plus the strongest argument against. If none, name the live candidate and why it fails.' },
    where_verified: { type: 'string', description: 'Field 6 — file:line anchors and commands, for BOTH cause and remedy.' },
    claims_refuted: { type: 'array', items: { type: 'string' }, description: 'Sentences in the finding that do not hold at source. Empty if none.' },
    files_changed_estimate: { type: 'string' },
    blocks_or_blocked_by: { type: 'string' },
  },
  required: ['key', 'one_line', 'cause_verdict', 'decision', 'how_things_stand', 'why',
             'recommendation_verb', 'recommendation', 'branches', 'cheapest_tier', 'grade',
             'above_line', 'operator_axis', 'operator_axis_quote', 'where_verified', 'claims_refuted',
             'files_changed_estimate', 'blocks_or_blocked_by'],
}

/*
 * The judge's verdict. The scale's words are defined in the `od-lens` agent
 * under the judge role; this enum only fixes their spelling and order, so the
 * route below can compare them.
 */
const CONFIDENCE = ['low', 'medium', 'high', 'very-high']
const JUDGEMENT = {
  type: 'object',
  properties: {
    confidence: { type: 'string', enum: CONFIDENCE },
    justification: { type: 'string', description: 'Why this level and not the next one up: each refuter objection, and whether it stands at source, with anchors.' },
    standing_objections: { type: 'array', items: { type: 'string' }, description: 'Refuter objections that hold at source. Empty if none.' },
    reserved_category_applies: { type: 'boolean', description: 'True when ANY of the constitution\'s reserved categories applies to this record — the one it claims, or another it missed. False only when none applies at source (for a category that turns on what is undecided: a corpus sentence decides the behavior). It rules on the record, not on its claim.' },
    category_ruling: { type: 'string', description: 'Which reserved category applies and why, or why none does, with the deciding corpus sentences quoted with file and line.' },
    lane_admitted: { type: 'boolean', description: 'True only when the constitution\'s operator-decision section admits a judged lane above its line FOR THIS RECORD: false when the section admits none, or when an exclusion it states reaches this record.' },
    lane_quote: { type: 'string', description: 'The sentence that admits it, quoted with file and line, and every exclusion it states with why this record is outside it; or the sentence that keeps this record with the operator.' },
  },
  required: ['confidence', 'justification', 'standing_objections',
             'reserved_category_applies', 'category_ruling', 'lane_admitted', 'lane_quote'],
}
const SESSION_FLOOR = CONFIDENCE.indexOf('high')

/*
 * Every test below fails toward the operator: a value that is not exactly the
 * one that releases the session — a missing field, a string where a boolean
 * belongs, a backticked `none` — routes `operator`, except that the backticks
 * the schema's own wording invites are stripped before comparing.
 */
const reserved = (record) =>
  String(record.operator_axis || '').replace(/`/g, '').trim().toLowerCase() !== 'none'

/*
 * Unjudged: only a `none` at or below the line reaches the session, as before.
 * Judged: only an explicit `reserved_category_applies === false` leaves the
 * operator's side, and then the judge's confidence must reach the floor — at
 * or below the line on that alone, above it also on the admitted lane.
 */
function route(record, judgement) {
  if (!judgement) {
    return !reserved(record) && record.above_line === false ? 'session' : 'operator'
  }
  if (judgement.reserved_category_applies !== false) return 'operator'
  const confident = CONFIDENCE.indexOf(judgement.confidence) >= SESSION_FLOOR
  if (record.above_line === false) return confident ? 'session' : 'operator'
  if (record.above_line !== true) return 'operator'
  return confident && judgement.lane_admitted === true ? 'session' : 'operator'
}

function describe(item) {
  const object = typeof item === 'object' && item !== null
  if (object && item.brief) {
    return { key: item.key || item.title || 'finding', source: item.brief }
  }
  /*
   * Without a `brief`, the item must resolve to an issue number. `{ title:
   * 'x' }` used to reach the agent as `#undefined` with an instruction to run
   * `gh issue view undefined`, which fails four agents in silence.
   */
  const number = String((object ? item.issue ?? item.key : item) ?? '').trim().replace(/^#/, '')
  if (!/^\d+$/.test(number)) {
    throw new Error(
      'od-gate: each item is an issue number, or { key, title, brief } with the '
      + 'finding stated in full under `brief`. This one is neither: '
      + JSON.stringify(item))
  }
  const repo = (object && item.repo) || input.repo
  const scope = repo ? ` --repo ${repo}` : ''
  return {
    key: repo ? `${repo}#${number}` : `#${number}`,
    source: `The finding is issue #${number}${repo ? ` in \`${repo}\`` : ''}. Read it with,\n`
          + `literally:\n\n    gh issue view ${number}${scope}\n\n`
          + `Read every comment on the thread, not only the body: a later comment may\n`
          + `already correct the body, and a correction the issue itself carries is not\n`
          + `a finding of yours.`,
  }
}

log(`od-gate: ${items.length} finding(s), ${items.length * 4 + 1} agents before the judged round`)

phase('Lenses')

const records = (await pipeline(
  items.map(describe),

  (item) => parallel(['cause', 'remedy', 'ownership'].map(lens => () => agent(
    `${ROOTS}\n\n# Finding under examination: ${item.key}\n\n${item.source}\n\n`
    + `## Your lens\n\nYour lens is **${lens}**. Your agent definition states what `
    + `that means; apply it as written.\n\n`
    + `Return your report as your final message. That text IS the deliverable.`,
    { label: `${lens}:${item.key}`, phase: 'Lenses', agentType: AGENT },
  ))).then(reports => ({ item, reports: reports.filter(Boolean) })),

  (prev) => agent(
    `${ROOTS}\n\n# Task — write the record for ${prev.item.key}\n\n${prev.item.source}\n\n`
    + `Your lens is **synthesis**. Three independent lens agents examined this `
    + `finding — the cause, the remedy and the ownership axes. Their reports follow.\n\n`
    + `Emit the record through the structured output attached to this call. The `
    + `\`grade\` field takes ONE word, and the words are the project `
    + `constitution's: read its operator-decision section and use the scale it `
    + `states. The schema does not constrain them, and no other scale is `
    + `admissible — least of all one you remember from another project.`
    + prev.reports.map((r, i) => `\n\n===== LENS REPORT ${i + 1} =====\n${r}`).join(''),
    { label: `synthesis:${prev.item.key}`, phase: 'Synthesis', agentType: AGENT, schema: RECORD },
  ),
)).filter(Boolean)

phase('Critic')

const critique = await agent(
  `${ROOTS}\n\n# Task — critic over ${records.length} record(s)\n\n`
  + `Your lens is **critic**. Each record was produced by three adversarial lenses `
  + `and a synthesiser. Apply your lens as your agent definition states it, and add `
  + `one thing it cannot know in advance: the recorded failure here is three angles `
  + `each asking whether a step is bound, whether a sentence is true, whether a `
  + `locator is sound — and none asking whether the journey a user drives is one `
  + `they can complete. Find that question, whatever it is this time.\n\n`
  + `Finish with the execution order for everything the session owns, and the `
  + `reason for the order.\n\n`
  + `## The records\n\n\`\`\`json\n${JSON.stringify(records, null, 2)}\n\`\`\``,
  { label: 'critic', phase: 'Critic', agentType: AGENT },
)

const contested = records.filter(record => record.above_line === true || reserved(record))
log(`od-gate: ${contested.length} record(s) judged — above the line or claiming a `
    + `reserved category — ${contested.length * 2} more agents`)

/*
 * Keyed by the record object, never by its `key`: that string is the
 * synthesiser's, two items can share it, and a shared key would hand one
 * record another's judgement.
 */
const judgements = new Map()
if (contested.length) {
  phase('Refute')
  const judged = await pipeline(
    contested,

    (record) => agent(
      `${ROOTS}\n\n# Task — refute the record for ${record.key}\n\n`
      + `Your lens is **refute**. Apply it as your agent definition states it`
      + (reserved(record)
        ? ` — the record's \`operator_axis\` does not read \`none\`, so attack the category claim first.\n\n`
        : `.\n\n`)
      + `## The record\n\n\`\`\`json\n${JSON.stringify(record, null, 2)}\n\`\`\`\n\n`
      + `## The critic over the whole set\n\n${critique || '(the critic returned nothing)'}\n\n`
      + `Return your report as your final message. That text IS the deliverable.`,
      { label: `refute:${record.key}`, phase: 'Refute', agentType: AGENT },
    ).then(refutation => ({ record, refutation })),

    (prev) => prev.refutation ? agent(
      `${ROOTS}\n\n# Task — judge the record for ${prev.record.key}\n\n`
      + `Your lens is **judge**. Apply it as your agent definition states it, and `
      + `emit the verdict through the structured output attached to this call.`
      + (reserved(prev.record)
        ? ` The record's \`operator_axis\` does not read \`none\`: rule \`reserved_category_applies\` first.\n\n`
        : `\n\n`)
      + `## The record\n\n\`\`\`json\n${JSON.stringify(prev.record, null, 2)}\n\`\`\`\n\n`
      + `## The critic over the whole set\n\n${critique || '(the critic returned nothing)'}\n\n`
      + `## The refutation\n\n${prev.refutation}`,
      { label: `judge:${prev.record.key}`, phase: 'Judge', agentType: AGENT, schema: JUDGEMENT },
    ).then(judgement => ({ record: prev.record, judgement })) : null,
  )
  // By position: `pipeline` returns one result per item, in item order, so
  // this does not depend on the runtime handing a stage the same object.
  contested.forEach((record, index) => {
    if (judged[index]) judgements.set(record, judged[index].judgement)
  })
}

const routed = records.map(record => ({
  ...record,
  judgement: judgements.get(record) || null,
  route: route(record, judgements.get(record)),
}))

return { records: routed, critique }
