---
name: pr-feedback-resolver
description: >
  Use when you have a GitHub PR open and need to address reviewer feedback (general comments, line-by-line reviews, or CI/CD failures) for the current branch. 
  Don't use for creating new PRs or performing code reviews on someone else's PR.
---

# PR Feedback Resolver

## Overview

This skill guides the agent on how to use the GitHub CLI (`gh`) to automatically fetch PR feedback, modify the code to address the feedback, and commit the changes using the Conventional Commits format, leaving them ready to be pushed.

## Workflow Instructions

Follow these steps exactly when asked to address PR feedback:

> [!IMPORTANT]
> **DO NOT PUSH THE COMMITS.** You must only stage and commit your changes locally. Pushing changes is the user's responsibility after they have reviewed your commits.

### Step 1: Retrieve PR Feedback
Use the `gh` CLI to fetch all relevant feedback for the currently checked out branch or pull request. You must run these commands to gather context:

1. **Get general comments and line-by-line reviews:**
   Run `gh pr view --comments`.
   - *Alternative:* If `gh pr view --comments` fails or returns GraphQL deprecation warnings, fetch JSON details: `gh pr view --json title,body,comments,reviews`.
   - *Fallback:* If GraphQL continues to fail, use the REST API endpoint: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments`.
   *(This will show general PR comments and line-specific review comments.)*

2. **Check for CI/CD failures:**
   If automated checks or CI/CD workflows are configured, run `gh pr checks` to see if any automated checks failed. (If no checks are configured or active, note this and proceed).
   *(If there are failures, you may need to view the logs or specific failed job details using `gh run view <run-id>` or similar).*

### Step 2: Analyze and Plan
1. Read through the feedback gathered in Step 1.
2. If there are code suggestions, identify the files and lines that need modification.
3. If there are CI/CD failures, identify the root cause (e.g., linting errors, test failures).
4. If the feedback is ambiguous, ask the user for clarification before proceeding.

### Step 3: Implement Changes
1. Use your standard editing tools to apply the necessary changes to the codebase.
2. Ensure you address all pieces of feedback. If you cannot address something, note it down to inform the user later.
3. **Run local tests:** Discover and execute the package test suite (e.g., `go test ./...` or language equivalent). All tests **must pass** before you proceed to committing.

### Step 4: Commit Changes
Once all changes are implemented and verified locally, you must commit them.

1. **Format:** Use the **Conventional Commits** specification for your commit messages (e.g., `fix: resolve null pointer in user auth`, `refactor(api): simplify response parsing`).
2. **Action:** Run `git add <modified-files>` followed by `git commit -m "<your-message>"`.
3. **Verify Local State:** Run `git status` and verify that your local branch is ahead of the tracking branch (meaning the commits exist locally but have **not** been pushed to remote).

> [!WARNING]
> **DO NOT** push the changes. Stop immediately after committing.

## Output
When finished, provide a summary of:
1. The feedback addressed.
2. The changes made.
3. Any feedback that could not be addressed or requires the user's attention.
4. A reminder to the user to push the changes if they look good.
