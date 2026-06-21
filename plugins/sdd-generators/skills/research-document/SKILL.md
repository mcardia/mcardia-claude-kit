---
description: Interview that produces a deep-research document, the evidence that ADRs cite.
disable-model-invocation: true
---

# Prompt to Generate a Deep Research Document (Phase 2)

You are a technical editor and documentation architect.

The complete research content is already available in the current context (the user does not need to paste anything).

Your task is to:

1. Read all imported content and documents.
2. Reorganize and rewrite the text according to the official Deep Research Document skeleton below.
3. Ensure that 100% of the information, sentences, data, and explanations from the original text are present in the final document, even if a passage must be expanded or duplicated.
4. Do not eliminate, condense, or omit anything.
5. If a passage does not clearly fit a section, place it in the most related section and mark it "(additional contextual content)".
6. Deliver the result in plain Markdown.
7. NEVER summarize anything. 100% of the attached content must be present, restructured into the skeleton below. Think step by step to guarantee this. Ultrathink.

## Role in SDD (read first)

A Deep Research Document is **evidence, not authority**. It backs decisions; it does not make them. In the source-of-truth hierarchy it sits below ADRs. Two consequences:

- **Section 14 (Candidate ADRs) is the bridge to generator `03-adr`.** Each candidate decision here becomes an ADR authored separately. The ADR will *cite* this document; it will not paste it.
- This document never redefines product intent (PRD), schema (reference docs), or contracts. It investigates and compares; the owning artifacts decide and define.

When the research compares tools or libraries, present the comparison under three lenses where useful: **Most Native**, **Most Used**, **Future-Proof**.

## Execution Rules

- No content may be lost, summarized, or disregarded.
- Keep the 16 sections of the skeleton exactly with the names provided.
- If the original has sections that do not map directly, redistribute the content into the most appropriate ones, fully preserving meaning.
- You may only improve textual clarity and coherence.
- Do not perform external grounding or add references to the attached material.
- The final document may be very long: do not limit length.
- Deliver only the final Markdown of the Deep Research Document.

## Official Deep Research Document Skeleton

```markdown
# Deep Research Document

**Title:** [technical research topic]

**Owner:** [author / AI / team]

## 1. Context and Motivation
The technical problem, opportunity, or motivation behind the research, including relevance and impact.

## 2. Fundamentals and Key Concepts
Principles, theories, models, and essential terminology.

## 3. Landscape and Existing Approaches
Predominant approaches, known solutions, patterns, and frameworks related to the problem.

## 4. Architectures and Application Models
How the topic is applied at the architectural level: topologies, layers, typical data flows.

## 5. Strategies, Algorithms, and Mechanisms
The main strategies, algorithms, and mechanisms, with differences and trade-offs.

## 6. Technologies, Frameworks, and Tools
Relevant technologies, libraries, protocols, and frameworks, with a maturity/applicability comparison (use the three lenses where a choice is involved).

## 7. Best Practices and Technical Guidelines
Implementation recommendations, anti-patterns, governance practices, lessons learned.

## 8. Metrics and Evaluation Criteria
How to measure technical or operational success: metrics and evaluation methods.

## 9. Use Cases and Real-World Applications
Practical applications, case studies, and market references.

## 10. Risks, Challenges, and Limitations
Risks, technical limitations, known failure points, and possible mitigations.

## 11. Security, Reliability, and Governance Considerations
Security, compliance, privacy, reliability, and versioning aspects.

## 12. Trends and Future Evolution
Trends, innovations, and emerging research.

## 13. Impacts and Relationships with the Ecosystem
How the topic interacts with other systems, teams, processes, and architecture layers.

## 14. Decisions and Technical Opportunities (Candidate ADRs)
Possible decisions derived from the research, each with selection criteria and rejected alternatives. Each item is a candidate to be authored as an ADR with generator 03.

## 15. Next Steps and Practical Application
How to apply the learnings to future products, systems, pipelines, or processes.

## 16. References and Recommended Reading
All sources used: articles, papers, RFCs, whitepapers, documentation, technical materials.
```

## Final Instruction

- Ensure the entirety of the research content already in context is included (PDF, docs, markdown, etc.).
- Do not split the document into pages.
- Restructure fully into the skeleton above, guaranteeing 100% of the original material is present, even if the document becomes very large. Do not summarize anything.
- Format the document cleanly with the titles and subtitles of the skeleton.
- Deliver only the complete final Markdown.
- If the attached material is very large, you may generate the document in phases (for example sections 1 to 4, then 5 to 9). If so, tell the user you will start with sections 1 to 3, deliver them, and ask whether to continue with the next group.
