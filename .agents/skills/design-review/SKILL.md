---
name: design-review
description: >
  Expert design document reviewer. Use when asked to review, critique, challenge, or
  improve a software design document, architecture doc, or technical spec. Applies a
  structured methodology: line-by-line challenge, dependency audit, and implementation
  readiness assessment. Don't use for code reviews or general Q&A.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# Design Review

This skill applies a rigorous, opinionated review methodology to software design documents. The goal is to produce a design that is **bulletproof and implementation-ready** — detailed enough to hand to an agent for a one-shot implementation.

## Core Mindset

Challenge every line. Do not agree with a choice simply because the author made it. Agree when the choice is correct; push back when it is not. A weak review produces a broken implementation.

The two outputs of a review are:
1. **A critique artifact** documenting findings with ✅ / ⚠️ / ❌ verdicts.
2. **An updated document** incorporating all agreed-upon changes.

---

## Review Methodology

### Pass 1 — Read & Research

Before writing a single critique line:

1. **Read the entire document end-to-end** without stopping. Form a mental model of the system.
2. **Research every dependency** listed in the doc. For each one, look up:
   - What it actually does (don't assume from the name).
   - Whether existing deps in the list already cover that job.
   - Whether the stdlib could replace it.
3. **Identify the execution flow** and trace through it mentally. Look for ordering constraints that could break the design (e.g., needing data before a framework is initialized).

### Pass 2 — Line-by-Line Challenge

Work through each section. For every claim, ask:

- **Is this accurate?** (e.g., does the library actually work the way the doc says?)
- **Is this specific enough?** (Could two engineers implement this differently based on this description?)
- **Is this necessary?** (Does this add complexity without a clear benefit?)
- **Is anything missing?** (What would break at implementation time that this section doesn't address?)

Use the checklist in `references/review-checklist.md` to ensure comprehensive coverage.

### Pass 3 — Dependency Audit

For every dependency listed:

1. Is it actually used? Can it be removed?
2. Does another dep in the list already cover this responsibility? (Overlap = eliminate one.)
3. Are there missing deps required to implement what the doc describes?

See `references/dependency-audit.md` for heuristics and common patterns.

### Pass 4 — Implementation Readiness Gap Fill

After challenges are agreed upon, upgrade the document to be implementation-ready:

A document is **implementation-ready** when a competent agent could produce correct, complete code from it alone. Check:

- [ ] Every public function/method has a clearly defined signature and contract.
- [ ] All data structures are fully defined (no abstract `*Schema` types — say which library type).
- [ ] Every I/O boundary is defined: input format, priority order, error format, exit codes.
- [ ] Every config file / env var has a concrete format and example.
- [ ] The execution flow is specified as ordered steps, not prose.
- [ ] Package responsibilities are stated as concise contracts, not vague labels.
- [ ] All edge cases that are deferred (e.g., "V2") are explicitly marked as out of scope.

---

## Output Format

### Critique Artifact

Write a markdown critique document with:

```markdown
## Section N: <Name>

✅ **<Claim>** — Brief agreement rationale.
⚠️ **<Claim>** — Concern + recommendation.
❌ **<Claim>** — Pushback + required change.
```

Group by original document section. End with a **Summary Table** of all recommended changes ordered by priority (Critical → High → Medium → Low).

### Updating the Document

After the user agrees to findings, apply all changes to the original document in a single editing pass. Prefer surgical edits over full rewrites unless the document is structurally unsound.

---

## References

- [references/review-checklist.md](references/review-checklist.md) — Section-by-section checklist for comprehensive design review coverage.
- [references/dependency-audit.md](references/dependency-audit.md) — Heuristics for auditing dependency lists.
