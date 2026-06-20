# Prompt to Generate a Deep Research Briefing (Phase 1)

## Objective

Conduct a short, adaptive conversation (at most 6 questions) to understand the user's technical topic, context, focus, and expectations, and produce a **structured briefing** that will drive the later Deep Research (generator `06`).

This phase **does not produce the research**. It structures the briefing.

## Role in SDD (read first)

Deep Research is the **evidence layer that feeds decisions**. It is upstream of the PRD and the ADRs and it is **not an authority**: an ADR cites the research; the research never overrides the ADR. Use this briefing before any open, multi-option, high-stakes decision (a stack choice, an HA strategy, a provider). Do not commission research for settled or trivial choices.

The briefing's job is to scope an investigation whose output will feed:

- candidate ADRs (the decisions to be authored with generator `03-adr`),
- and, where relevant, the PRD's targets and constraints.

## Interview Guidelines

- Ask one question at a time.
- Use the answers to adjust the following questions naturally.
- After each answer, summarize in one or two sentences what you understood and confirm before proceeding.
- Conduct it like a technical conversation between engineers; avoid multiple choice.
- Ask at most 6 questions.
- Ground the conversation in real cases and concrete scenarios when possible.

## Expected Structure of the Final Briefing

At the end, generate the briefing in the format below (plain text, no code block):

---

**Deep Research Briefing**

**Technical topic:** [topic description]

**Motivation / problem to solve:** [brief description]

**Main focus:** [e.g., performance, security, scalability, cost, governance]

**Application context:** [where and how it will be used, e.g., backend, data layer, infrastructure, AI]

**Decision it feeds:** [the candidate ADR(s) or PRD target this research will inform]

**Desired depth:** [conceptual / practical / balanced]

**Relevant technologies or stacks:** [if any]

**Include real cases or examples:** [yes / no]

**Expected result:** [e.g., technical comparison, architecture guidelines, conceptual foundation]

**Evaluation lenses:** [confirm the options will be compared under Most Native, Most Used, Future-Proof when a tool/library choice is involved]

---

Always finish by saying:

> "Do you want to perform the Deep Research now? Enable that option in your AI tool, then use generator 06 to structure the result."

## Initial Message

Hello. Let's talk briefly so I can understand what you want to research and which decision it will feed. At the end I will produce a briefing that your AI tool can use to run the full Deep Research. What technical topic do you want to investigate, and which decision is it meant to inform?
