# Agent Skill Design Patterns

## Workflow Patterns

### 1. Sequential Workflow
Best for complex, multi-step tasks where order matters.
*Structure:* Define numbered steps in the `SKILL.md`.

> **Example:**
> 1. Analyze the input file.
> 2. Run `scripts/extract_data.py`.
> 3. Validate results against `references/schema.json`.
> 4. Generate the report.

### 2. Conditional Workflow
Best for tasks with branching logic or multiple modes of operation.
*Structure:* Use "If/Then" logic to guide the agent to the right sub-section or reference file.

> **Example:**
> * If the user wants to **Create**, go to the Creation Section.
> * If the user wants to **Edit**, see `references/editing_guide.md`.

## Output Patterns

### 1. Template Pattern
Use this when the output must follow a strict format.
*Structure:* Provide a markdown code block with the exact structure required.

> **Example:**
> "ALWAYS produce the report in this format:"
> ```markdown
> # Executive Summary
> [Summary here]
> # Technical Details
> - [Detail 1]
> ```

### 2. Examples Pattern
Use this when "showing" is better than "telling."
*Structure:* Provide Input/Output pairs.

> **Example:**
> **Input:** "Fix the date bug"
> **Output:** `fix(ui): resolve date formatting in sidebar`