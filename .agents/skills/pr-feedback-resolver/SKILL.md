---
name: pr-feedback-resolver
description: >
  Use when you have a GitHub PR open and need to address reviewer feedback (general comments, inline review threads, or CI/CD failures) for the current branch,
  e.g. "address the review comments", "fix what the reviewer asked for", "CI is failing on my PR".
  Don't use for creating new PRs or performing code reviews on someone else's PR.
metadata:
  version: 1.1.0
  author: "Cody Oss"
license: "MIT"
---

# PR Feedback Resolver

## Overview

This skill guides the agent on how to use the GitHub CLI (`gh`) to fetch PR feedback, triage it, modify the code to address it, and commit the changes locally using the Conventional Commits format, leaving them ready to be pushed.

## Workflow Instructions

Follow these steps exactly when asked to address PR feedback:

> [!IMPORTANT]
> **DO NOT PUSH THE COMMITS.** You must only stage and commit your changes locally. Pushing changes is the user's responsibility after they have reviewed your commits.

### Step 1: Retrieve PR Feedback
Run these commands from the PR's branch. `gh` fills in `{owner}` and `{repo}` from the current repository.

1. **Get the PR number and top-level feedback** (conversation comments and review summaries):
   ```bash
   gh pr view --json number,title,body,comments,reviews
   ```
   This does **not** include inline (line-level) review comments.

2. **Get inline review threads with their resolution state.** Resolved and outdated threads have usually been handled already; skip them unless the user says otherwise.
   ```bash
   gh api graphql -F owner='{owner}' -F repo='{repo}' -F pr=<number> -f query='
     query($owner: String!, $repo: String!, $pr: Int!) {
       repository(owner: $owner, name: $repo) {
         pullRequest(number: $pr) {
           reviewThreads(first: 100) {
             nodes {
               isResolved
               isOutdated
               path
               line
               comments(first: 50) { nodes { author { login } body url } }
             }
           }
         }
       }
     }'
   ```
   - *Fallback:* If GraphQL fails, use REST (no resolution state, so judge from the reply chain): `gh api repos/{owner}/{repo}/pulls/<number>/comments --paginate`.

3. **Check for CI/CD failures:**
   Run `gh pr checks`. If no checks are configured, note this and proceed. For each failed check, get the failing log with `gh run view <run-id> --log-failed` (the run ID is in the check's URL).

### Step 2: Triage
Classify every open item before touching code. Do not apply suggestions blindly.

| Category | Action |
|---|---|
| **Actionable** — a clear, correct change request or suggestion | Implement it. |
| **Question** — reviewer asks "why" or "what about X" | Don't change code unless the answer reveals a bug; draft a reply. |
| **Disagree** — the suggestion is wrong, would introduce a bug, or conflicts with other feedback | Don't implement; explain why in the summary. |
| **Already done / outdated** — addressed by a later commit | Skip; note it. |
| **Noise** — bot comments (coverage, dependabot, linters already reported in CI) | Ignore unless they indicate a real failure. |

If the feedback is ambiguous or two reviewers conflict, ask the user before proceeding on those items.

For CI failures, identify the root cause (lint, test, build). If a failure also occurs on the base branch or is clearly infrastructure/flaky (network timeouts, runner errors), don't try to fix it. Report it instead.

### Step 3: Implement Changes
1. Use your standard editing tools to apply the actionable items.
2. **Verify locally:** Discover and run the project's test suite **and** its linters/formatters (check the CI workflow files for the exact commands CI runs, e.g. `.github/workflows/*.yml`, `Makefile`, `package.json` scripts). Everything you touched must pass before committing.
3. If a test fails in code you didn't touch and it also failed in the PR's CI run before your changes, it is pre-existing: note it and move on rather than looping on it.

### Step 4: Commit Changes
1. **Granularity:** Make one commit per logical change. Group comments that touch the same concern; keep CI/lint fixes in their own commit.
2. **Format:** Follow the `conventional-commits` skill for message format (e.g., `fix(auth): handle nil session in token refresh`, `style: apply gofmt`). The user has already authorized committing by asking you to resolve feedback, so skip that skill's confirmation prompt.
3. **Action:** `git add <modified-files>` then commit. Never use `git add -A` blindly; untracked files may be unrelated.
4. **Verify Local State:** Run `git status` and confirm the commits exist locally and have **not** been pushed.

> [!WARNING]
> **DO NOT** push the changes. Stop immediately after committing.

## Output
When finished, provide a summary of:
1. The feedback addressed, with the commit that addresses each item.
2. Items intentionally not changed (questions, disagreements, pre-existing or flaky failures), with a **draft reply** for each thread the user can paste. Do not post replies yourself.
3. Anything that requires the user's decision.
4. A reminder to the user to push the changes if they look good.
