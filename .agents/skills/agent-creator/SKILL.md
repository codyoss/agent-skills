---
name: agent-creator
description: >
  Guide for creating, validating, and managing custom agent profiles (agent.json).
  Use when building new subagent definitions, updating existing agent profiles,
  or reviewing agent configurations for the Antigravity harness.
  Don't use for creating skills (use skill-creator instead) or for general coding.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# Agent Creator

This skill provides guidance for creating custom agent profiles that can be spawned as subagents by the Antigravity harness.

## About Custom Agents

Custom agents are specialized subagent definitions stored as `agent.json` files. When the parent agent encounters a task that matches a custom agent's description, it can spawn the agent using `invoke_subagent` with the agent's type name.

Custom agents differ from skills:
* **Skills** provide instructions that extend the *current* agent's knowledge.
* **Custom Agents** define *entirely separate agents* with their own system prompts, tool permissions, and context sections.

> **Cross-platform note:** Other platforms use different formats for the same concept. For example, Codex CLI uses `.toml` files with `[agents.<name>]` tables containing `description`, `config_file`, and `nickname_candidates` fields. The underlying design principles (single responsibility, minimal tool surface, lean prompts) are universal regardless of format.

---

## Directory Structure

```text
.agents/agents/<agent_name>/
└── agent.json    # Required: Agent profile definition
```

**Discovery locations:**
* **Workspace-specific:** `<workspace-root>/.agents/agents/<agent_name>/agent.json`
* **Global:** `~/.gemini/config/agents/<agent_name>/agent.json`

The directory name MUST match the `name` field in `agent.json`.

---

## Agent Profile Schema

See [references/agent_schema.md](references/agent_schema.md) for the complete JSON schema, all valid tool names, valid `includeSections` values, and common tool presets.

---

## Core Design Principles

### 1. Single Responsibility
Each agent should do one thing well. Avoid creating "Swiss Army knife" agents that handle unrelated tasks. Instead, create multiple focused agents.

### 2. Minimal Tool Surface
Grant only the tools the agent needs:
* **Verifiers** need `run_command` (to execute tests) but typically do not need `write_to_file`.
* **Researchers** need read tools and `search_web` but no write/execute tools.
* **Implementers** need the full tool set.

### 3. Lean System Prompts
The system prompt shares the context window with everything else. Write prompts that are:
* **Imperative**: "You are X. Your task is Y. Do Z."
* **Specific**: Name exact files, packages, commands, and output formats.
* **Non-redundant**: Do not teach the agent general coding — it already knows how to code. Focus on project-specific constraints and domain knowledge.

### 4. Always Include `send_message`
Every custom agent must include `send_message` in its tool list. Without it, the agent cannot report results back to the parent.

---

## Agent Creation Process

### Step 1: Define the Role
Identify the specific role this agent fills. Good agents map to clear job descriptions:
* "Run all tests and report pass/fail with details"
* "Implement feature X according to the design doc"
* "Review code changes against the project's style guide"

### Step 2: Choose the Tool Preset
Select the minimal tool set from the presets in [references/agent_schema.md](references/agent_schema.md):
* **Researcher**: Read-only, no execution. For codebase analysis and documentation review.
* **Verifier**: Read + execute. For running tests and auditing implementations.
* **Implementer**: Full read/write/execute. For writing code and making changes.

### Step 3: Initialize
Run the initialization script to generate the directory structure:
```bash
python3 scripts/init_agent.py <agent-name> --path <output-path>
```
Use `--read-only` to create a researcher agent with no write/execute tools.

### Step 4: Write the System Prompt
Edit the `content` field in `systemPromptSections`. A good system prompt includes:

1. **Identity & Role**: "You are [Name], a [role description]."
2. **Task Definition**: "Your task is to [specific objective]."
3. **Constraints & Standards**: Project-specific coding rules, naming conventions, or architectural guidelines.
4. **Steps**: Numbered steps the agent should follow.
5. **Output Format**: "Report your findings as a markdown document" or "Send a message to the parent agent with your results."

**Example:**
```
You are a meticulous verification subagent.
Your task is to verify the implementation of <FEATURE> against its requirements.

Steps:
1. Read the feature requirements in docs/roadmap.md.
2. Inspect the codebase changes (run `git diff` or view files).
3. Verify all requirements are met.
4. Run the full test suite (`go test ./...`).
5. Report findings. Explicitly state if you give the implementation a "clean bill of health".
```

### Step 5: Write the Description
The `description` field tells the parent agent when to spawn this subagent. Write it like a job posting:
* What the agent does
* What tools/capabilities it has
* What kind of tasks it handles

### Step 6: Validate
Run the validation script to catch structural errors:
```bash
python3 scripts/validate_agent.py <agent-folder>
```

---

## System Prompt Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| "You are a helpful assistant" | Be specific: "You are a Go test auditor for the clai CLI project" |
| Restating general coding knowledge | Only include project-specific constraints |
| Stuffing entire design docs into the prompt | Reference file paths and instruct the agent to read them |
| No output format specified | Define exactly how the agent should report results |
| Missing `send_message` in tool list | Always include it — agents must communicate with their parent |
