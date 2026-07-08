---
name: conventional-commits
description: Use when generating, formatting, or reviewing Git commit messages following the Conventional Commits specification. Enforces semantic types, optional scopes based on file paths, 72-character body wrapping, GitHub issue references, and exclamation mark indicators for breaking changes. Don't use for general Git repository status checks, branch management, or other Git commands.
---

# Conventional Commits Formatter

## Overview

This skill ensures that all Git commit messages comply with the Conventional Commits 1.0.0 specification, providing human and machine-readable context to changes.

## Instructions

Follow these steps when tasked with writing a commit message or executing a commit:

### Step 1: Analyze Staged Changes
1. Run `git diff --cached` to inspect the changes. If no files are staged, check `git status` and ask the user to stage target files first.
2. Identify the modified directories, packages, or files to determine the optional scope.

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
2. Identify an optional scope based on the modified files (e.g., `feat(cli)` or `docs(readme)`). Use lowercase kebab-case for scopes.
3. If a change introduces a breaking API change, append a `!` directly after the type or scope (e.g., `refactor(api)!: remove deprecated methods`).

### Step 3: Format the Header, Body, and Footer
1. **Header Format**: Write the header as `<type>[scope][!]: <description>`. Use the imperative mood for the description (e.g., "add script", not "added script"). Do not capitalize the first letter, do not end with a period, and keep the header under 72 characters.
2. **Body Format**: Wrap body lines at exactly 72 characters. Explain the motivation/rationale (the "why") rather than the implementation details (the "how"). Contrast the new behavior with the old behavior. Use bullet points for logical sub-changes.
3. **Footer Format**: Use Git trailer syntax (`<Key>: <Value>`) for GitHub issue tracking.
   - For `fix` commits, explicitly check if there is an associated GitHub issue ID. If not found in context, ask the user: *"Is there a GitHub issue ID associated with this fix?"*
   - Format footers on separate lines at the bottom of the message (e.g., `Fixes: #123` or `Refs: #456`).

### Step 4: Review and Commit
1. Present the complete drafted commit message clearly to the user.
2. Explicitly ask the user: *"Would you like me to commit with this message?"*
3. Execute the `git commit` command only after receiving the user's confirmation.
