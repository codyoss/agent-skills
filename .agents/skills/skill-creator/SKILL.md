---
name: skill-creator
description: >
  Guide for creating, updating, and validating AI agent skills.
  Use when building new skills, updateing existing skills, or reviewing skills.
  Don't use for coding.
metadata:
  version: 1.1.0
  author: "Cody Oss"
license: "MIT"
---

# Skill Creator

This skill provides guidance for creating and maintaining effective Agent Skills.

## About Skills

Skills are modular, self-contained packages that extend an agent's capabilities by providing specialized knowledge,
workflows, and tools. They act as "onboarding guides" for specific domains or tasks, transforming a general-purpose
model into a specialized agent equipped with procedural knowledge.

### What Skills Provide

1.  **Specialized workflows**: Multi-step procedures for specific domains.
2.  **Tool integrations**: Instructions for working with specific file formats or APIs.
3.  **Domain expertise**: Company-specific knowledge, schemas, and business logic.
4.  **Bundled resources**: Scripts, references, and assets for complex tasks.

## Core Principles

### Concise is Key
The context window is a limited resource. Skills share this window with the system prompt, conversation history, and the
user's request.

**Default assumption: The agent is already capable.** Only add context the agent doesn't already have. Challenge every
piece of information: "Does the agent really need this explanation?"

### Set Appropriate Degrees of Freedom
Match the level of specificity to the task's fragility:

* **High freedom (text-based instructions)**: Use when multiple approaches are valid or decisions depend on context.
* **Medium freedom (pseudocode)**: Use when a preferred pattern exists but variation is acceptable.
* **Low freedom (specific scripts)**: Use when operations are fragile, error-prone, or strict consistency is required.

## Anatomy

Every skill has a required `SKILL.md` file and optional bundled resources:

```text
skill-name/
├── SKILL.md          # Required: Instructions and metadata
├── scripts/          # Executable code (Python, Bash, etc.)
├── references/       # Documentation loaded on demand
└── assets/           # Static files (templates, images, fonts)
```

### SKILL.md (Required)

The core file containing:

* **Frontmatter** (YAML): Required `name` and `description` fields.
    *   **Description is Critical**: This is the *only* semantic signal the agent uses to decide whether to load your skill. It must clearly define the **User Intent** (what they want) and **Context** (when to use it).
* **Body** (Markdown): Instructions and guidance. Loaded only after the skill is triggered.

#### Naming Conventions
* **Lowercase kebab-case**: Use `task-oriented-name` (e.g., `api-migration-expert`).
* **Action-oriented**: Start with a verb or a clear role (e.g., `ui-component-builder`, `refactoring-go`).
* **Keep it short**: Aim for 2-4 words.

#### Writing Effective Descriptions
The description is the **only** signal used for skill discovery. It must be precise to ensure it triggers when needed and stays dormant otherwise.

*   **Specify Intent**: Use "Use when..." to define the primary trigger.
*   **Define Scope**: Mention specific technologies, languages, or workflows (e.g., "Use when refactoring Go code for performance").
*   **Establish Negative Constraints**: Use "Don't use for..." to prevent false positives for generic requests.
*   **Avoid Generic Phrases**: Words like "helps with" or "assistant for" are too broad. Be specific about the *transformation* or *output*.

**Example:**
> Use when setting up a new React project with TypeScript using the Vite template. Includes scaffolding scripts and folder structure guidelines. Don't use for general React debugging.

### Bundled Resources (Optional)

* **Scripts** (scripts/): Executable code for deterministic or repetitive tasks (e.g., scripts/rotate_pdf.py).
* **References** (references/): Documentation loaded into context only when needed (e.g., references/api_docs.md, references/policies.md).
* **Assets** (assets/): Files used in the final output but not read into context (e.g., assets/template.pptx, assets/logo.png).

### Skill Creation Process

1. **Understand the Goal**: Identify the specific user requests the skill should handle.
2. **Plan Resources**: Determine if scripts, reference docs, or assets are needed.
3. **Initialize**: Run the initialization script to generate the structure.

```bash
python3 scripts/init_skill.py <skill-name> --path <output-path>
```

4. **Edit**: Implement the logic in SKILL.md and populate resources.
5. **Validate**: Run the validation script to check for errors.

```bash
python3 scripts/validate_skill.py <skill-folder>
```

### Progressive Disclosure

Structure your skill to minimize token usage:

1. **Metadata**: Only name and description are loaded initially (100 words max).
2. **Instructions**: The SKILL.md body is loaded upon activation (500 lines max).
3. **Resources**: Files in scripts/ or references/ are accessed only if the agent decides they are necessary for the specific turn (unlimited length).

> [!IMPORTANT]
> To enable discovery, all bundled scripts and references MUST be explicitly mentioned in the `SKILL.md` body. If there are a lot of scripts or references, consider using a Table of Contents at the end of the body.

### Common Pitfalls

*   **Vague Descriptions**: "Helps with coding" is too broad. Use "Helps with refactoring legacy Java code using the Factory pattern."
*   **Overloading Context**: putting *everything* in `SKILL.md`. Move detailed reference tables or long examples to `references/`.
*   **Fragile Parsing**: Relying on the agent to "read" a complex file structure without a script. Use a script to parse/summarize if the format is strict.
*   **Assuming State**: The agent doesn't remember previous turns perfectly unless they are in the context output. Re-read files if you need fresh state.