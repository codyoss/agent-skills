---
name: skill-creator
description: Guide for creating effective Agent Skills. Use this skill when the user wants to create a new skill, update an existing one, or needs advice on structuring agent capabilities, workflows, or tool integrations.
---

# Skill Creator

This skill provides guidance for creating effective Agent Skills.

## About Skills

Skills are modular, self-contained packages that extend an agent's capabilities by providing specialized knowledge, workflows, and tools. They act as "onboarding guides" for specific domains or tasks, transforming a general-purpose model into a specialized agent equipped with procedural knowledge.

### What Skills Provide

1.  **Specialized workflows**: Multi-step procedures for specific domains.
2.  **Tool integrations**: Instructions for working with specific file formats or APIs.
3.  **Domain expertise**: Company-specific knowledge, schemas, and business logic.
4.  **Bundled resources**: Scripts, references, and assets for complex tasks.

## Core Principles

### Concise is Key
The context window is a limited resource. Skills share this window with the system prompt, conversation history, and the user's request.

**Default assumption: The agent is already capable.** Only add context the agent doesn't already have. Challenge every piece of information: "Does the agent really need this explanation?"

### Set Appropriate Degrees of Freedom
Match the level of specificity to the task's fragility:

* **High freedom (text-based instructions)**: Use when multiple approaches are valid or decisions depend on context.
* **Medium freedom (pseudocode)**: Use when a preferred pattern exists but variation is acceptable.
* **Low freedom (specific scripts)**: Use when operations are fragile, error-prone, or strict consistency is required.

### Anatomy of a Skill

Every skill consists of a directory containing a required `SKILL.md` file and optional bundled resources:

```text
skill-name/
├── SKILL.md          # (Required) Instructions and metadata
├── scripts/          # (Optional) Executable code (Python, Bash, etc.)
├── references/       # (Optional) Documentation loaded on demand
└── assets/           # (Optional) Static files (templates, images, fonts)
```

### SKILL.md (Required)

The core file containing:

* **Frontmatter** (YAML): Required `name` and `description` fields.
    *   **Description is Critical**: This is the *only* semantic signal the agent uses to decide whether to load your skill. It must clearly define the **User Intent** (what they want) and **Context** (when to use it).
* **Body** (Markdown): Instructions and guidance. Loaded only after the skill is triggered.

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

1. **Metadata**: Only name and description are loaded initially.
2. **Instructions**: The SKILL.md body is loaded upon activation.
3. **Resources**: Files in scripts/ or references/ are accessed only if the agent decides they are necessary for the specific turn.

### Common Pitfalls

*   **Vague Descriptions**: "Helps with coding" is too broad. Use "Helps with refactoring legacy Java code using the Factory pattern."
*   **Overloading Context**: putting *everything* in `SKILL.md`. Move detailed reference tables or long examples to `references/`.
*   **Fragile Parsing**: Relying on the agent to "read" a complex file structure without a script. Use a script to parse/summarize if the format is strict.
*   **Assuming State**: The agent doesn't remember previous turns perfectly unless they are in the context output. Re-read files if you need fresh state.