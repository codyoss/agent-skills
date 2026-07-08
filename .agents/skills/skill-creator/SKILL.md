---
name: skill-creator
description: >
  Guide for creating, updating, and validating AI agent skills.
  Use when building new skills, updating existing skills, or reviewing skills.
  Don't use for coding.
metadata:
  version: 1.2.0
  author: "Cody Oss"
license: "MIT"
---

# Skill Creator

This skill provides guidance for creating and maintaining effective Agent Skills.

## About Skills

Skills are modular, self-contained packages that extend an agent's capabilities by providing specialized knowledge, workflows, and tools. They act as "onboarding guides" for specific domains or tasks, transforming a general-purpose model into a specialized agent equipped with procedural knowledge.

### What Skills Provide

1. **Specialized workflows**: Multi-step procedures for specific domains.
2. **Tool integrations**: Instructions for working with specific file formats or APIs.
3. **Domain expertise**: Company-specific knowledge, schemas, and business logic.
4. **Bundled resources**: Scripts, references, and assets for complex tasks.

---

## Core Principles

### Concise is Key
The context window is a limited resource. Skills share this window with the system prompt, conversation history, and the user's request.

**Default assumption: The agent is already capable.** Only add context the agent doesn't already have. Challenge every piece of information: "Does the agent really need this explanation?" and "Does this paragraph justify its token cost?" Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom
Match the level of specificity to the task's fragility:

* **High freedom (text-based instructions)**: Use when multiple approaches are valid or decisions depend on context.
* **Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists but variation is acceptable.
* **Low freedom (specific scripts, few parameters)**: Use when operations are fragile, error-prone, or strict consistency is required.

---

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
    * **Description is Critical**: This is the *only* semantic signal the agent uses to decide whether to load your skill. It must clearly define the **User Intent** (what they want) and **Context** (when to use it).
* **Body** (Markdown): Instructions and guidance. Loaded only after the skill is triggered.

#### Naming Conventions
* **Lowercase kebab-case**: Use `task-oriented-name` (e.g., `api-migration-expert`). Maximum 64 characters.
* **Action-oriented**: Start with a verb or a clear role (e.g., `ui-component-builder`, `refactoring-go`).
* **Keep it short**: Aim for 2-4 words.

#### Writing Effective Descriptions
The description is the **only** signal used for skill discovery. It must be precise to ensure it triggers when needed and stays dormant otherwise.
* **Specify Intent**: Use "Use when..." to define the primary trigger.
* **Define Scope**: Mention specific technologies, languages, or workflows.
* **Establish Negative Constraints**: Use "Don't use for..." to prevent false positives for generic requests.
* **Avoid Generic Phrases**: Words like "helps with" or "assistant for" are too broad. Be specific about the output.

**Example:**
> Use when setting up a new React project with TypeScript using the Vite template. Includes scaffolding scripts and folder structure guidelines. Don't use for general React debugging.

### Bundled Resources (Optional)
* **Scripts** (scripts/): Executable code for deterministic or repetitive tasks (e.g., `scripts/rotate_pdf.py`).
* **References** (references/): Documentation loaded into context only when needed (e.g., `references/api_docs.md`). Avoid duplicating info between `SKILL.md` and `references/`.
* **Assets** (assets/): Files used in the final output but not read into context (e.g., templates, logos, fonts).

### What NOT to Include
Do NOT create extraneous documentation or auxiliary files in the skill directory, including:
* `README.md`
* `INSTALLATION_GUIDE.md`
* `QUICK_REFERENCE.md`
* `CHANGELOG.md`

A skill should only contain the information needed for an AI agent to do the job. Do not include setup, testing, or human-facing instructions in auxiliary files.

---

## Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:
1. **Metadata (name + description)**: Always in context (~100 words max).
2. **SKILL.md body**: Loaded upon activation (<500 lines max).
3. **Bundled resources**: Accessed only if the agent decides they are necessary (unlimited).

All bundled resources MUST be explicitly mentioned in the `SKILL.md` body to enable discovery.

### Progressive Disclosure Patterns

**Pattern 1: High-level guide with references**
Keep the core workflow in `SKILL.md` and link out to sub-files:
```markdown
- **Form filling**: See [FORMS.md](references/FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](references/REFERENCE.md) for all methods
```

**Pattern 2: Domain-specific or Variant organization**
Organize by domain or framework to avoid loading irrelevant context:
```markdown
- For **AWS deployment patterns**, read [aws.md](references/aws.md)
- For **GCP deployment patterns**, read [gcp.md](references/gcp.md)
```

**Pattern 3: Conditional details**
Show basic content and link to advanced content only when needed:
```markdown
For simple edits, modify the XML directly.
**For tracked changes**: See [REDLINING.md](references/REDLINING.md)
```

---

## Skill Creation Process

Follow these steps in order when building or updating a skill:

### Step 1: Understand the Goal
Identify the specific user requests the skill should handle. Ask the user concrete clarifying questions, such as:
* "What functionality should the skill support? Can you give examples of how it will be used?"
* "What would a user say that should trigger this skill?"
* "Where should I create this skill? (Default is local `.agents/skills/`)"

### Step 2: Plan Resources
Analyze each concrete example to identify reusable resources:
* **Scripts**: Need to execute code repeatedly (e.g., pdf rotation)? Plan a Python/Bash script.
* **References**: Need to lookup table schemas or API rules? Plan a reference markdown file.
* **Assets**: Need boilerplate templates or logos? Plan an asset directory.

### Step 3: Initialize
Run the initialization script to generate the structure:
```bash
python3 scripts/init_skill.py <skill-name> --path <output-path> [--resources scripts,references,assets] [--examples]
```

### Step 4: Edit
Implement the logic in `SKILL.md` and populate resource folders. Use imperative mood in instructions ("Do this", "Check that"). Testing scripts by running them is required.

### Step 5: Validate
Run the validation script to catch basic formatting and spec issues early:
```bash
python3 scripts/validate_skill.py <skill-folder>
```

### Step 6: Automated Evaluation
Set up an evaluation dataset and run the evaluation script to test trigger accuracy and task execution:
1. **Trigger Evals**: Create a JSON list containing queries with `should_trigger` boolean flags (see [schemas.md](references/schemas.md)).
2. **Task Evals**: Create a JSON dictionary containing prompts and expectations (see [schemas.md](references/schemas.md)).
3. **Run Evals**:
   ```bash
   python3 scripts/run_eval.py --eval-set <path-to-json> --skill-path <path-to-skill>
   ```

### Step 7: Iterate & Forward-Test
Keep iterating on the skill's instructions, description, and scripts based on the evaluation pass rate until they are robust. Perform manual interactive checks where needed using subagents.

---

## Forward-Testing Methodology

To forward-test complex skills manually, stress test them by launching subagents (via `invoke_subagent`) with minimal context:

1. **Anti-Contamination**: Subagents should *not* know they are testing a skill. They should be treated as an agent asked to perform a real task.
   * **Good Prompt**: `Use skill-name at /path/to/skill to resolve task X`
   * **Bad Prompt**: `Pretend you are a user and test the skill at /path/to/skill`
2. **Fresh contexts**: Use fresh threads/conversations for independent validation runs.
3. **Pass raw input**: Provide raw input/artifacts instead of your diagnostic conclusions or expected answers.
4. **Clean up**: Remove test/subagent output files from disk after testing to avoid contaminating subsequent runs.