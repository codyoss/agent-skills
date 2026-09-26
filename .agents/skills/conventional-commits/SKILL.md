---
name: conventional-commits
description: Use when generating, formatting, or reviewing Git commit messages following the Conventional Commits specification. Enforces semantic types, scopes that match the repository's existing conventions, 72-character body wrapping, GitHub issue references, and breaking-change indicators. Don't use for general Git repository status checks, branch management, or other Git commands.
metadata:
  version: 1.1.0
  author: "Cody Oss"
license: "MIT"
---

# Conventional Commits Formatter

## Overview

This skill ensures that all Git commit messages comply with the Conventional Commits 1.0.0 specification, providing human and machine-readable context to changes.

## Instructions

Follow these steps when tasked with writing a commit message or executing a commit:

### Step 1: Analyze Staged Changes
1. Run `git diff --cached` to inspect the changes. If no files are staged, check `git status` and ask the user to stage target files first.
2. Run `git log --oneline -20` and check for a commitlint config (`commitlint.config.*`, `.commitlintrc*`). **The repository's established conventions win** over the defaults below: reuse its existing scopes, casing, and allowed types.
3. If the staged diff mixes unrelated changes (e.g., a bug fix plus an unrelated refactor), suggest splitting it into separate commits before drafting a message.

### Step 2: Determine Semantic Type and Scope
1. Choose the most appropriate semantic type from the allowed set:
   - **feat**: A new feature (corresponds to `MINOR` in Semantic Versioning)
   - **fix**: A bug fix (corresponds to `PATCH` in Semantic Versioning)
   - **docs**: Documentation-only changes
   - **style**: Layout or formatting changes (no production code changed)
   - **refactor**: Code changes that neither fix a bug nor add a feature
   - **perf**: Performance improvements
   - **test**: Adding or correcting tests
   - **build**: Changes affecting the build system or external dependencies
   - **ci**: CI configuration changes (e.g., GitHub Actions workflows)
   - **chore**: Auxiliary maintenance tasks (e.g., updating `.gitignore`)
   - **revert**: Reverting a previous commit
2. Pick an optional scope. Prefer a scope already used in `git log`; otherwise derive one from the modified package or directory (e.g., `feat(cli)` or `docs(readme)`). Use lowercase kebab-case. Omit the scope if the change spans many areas.
3. For a breaking change, append `!` after the type/scope (e.g., `refactor(api)!: remove deprecated methods`) **and** add a `BREAKING CHANGE: <what breaks and how to migrate>` footer.

### Step 3: Format the Header, Body, and Footer
1. **Header Format**: `<type>[(scope)][!]: <description>`. Use the imperative mood ("add script", not "added script"). Do not capitalize the first letter, do not end with a period, and keep the header at most 72 characters (aim for ~50).
2. **Body Format**: Separate from the header with a blank line. Wrap lines at **at most** 72 characters. Explain the motivation (the "why") rather than the implementation (the "how"), and contrast new behavior with old. Use bullet points for logical sub-changes. Omit the body for trivial changes.
3. **Footer Format**: Use Git trailer syntax (`<Key>: <Value>`), one per line, after a blank line.
   - For `fix` commits, look for an associated GitHub issue: check the branch name (e.g., `fix/123-...`), the PR description, and the conversation. Only if none is found, ask once: *"Is there a GitHub issue ID associated with this fix?"*, and accept "no".
   - Examples: `Fixes: #123`, `Refs: #456`, `BREAKING CHANGE: config key 'timeout' is now 'timeout_ms'`.

### Step 4: Review and Commit
1. Present the complete drafted commit message to the user.
2. If the user already asked you to commit (e.g., "commit this"), or you were invoked by another workflow that authorizes committing, commit directly. Otherwise ask: *"Would you like me to commit with this message?"* and wait for confirmation.
3. Commit with a heredoc so the multi-line body keeps its formatting, not with `-m`:
   ```bash
   git commit -F - <<'EOF'
   fix(pager): correct off-by-one in page boundary

   The last item of each page was repeated as the first item of the
   next page because the end index was inclusive.

   Fixes: #123
   EOF
   ```
