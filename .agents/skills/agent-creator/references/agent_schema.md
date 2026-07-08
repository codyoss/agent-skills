# Agent Profile Schema Reference

## Overview

Custom agent profiles are defined using `agent.json` files. This document is the authoritative reference for the JSON schema, valid tool names, and system prompt configuration options.

## Schema

```json
{
  "name": "<string>",
  "description": "<string>",
  "hidden": <boolean>,
  "config": {
    "customAgent": {
      "systemPromptSections": [
        {
          "title": "<string>",
          "content": "<string>"
        }
      ],
      "toolNames": ["<string>", ...],
      "systemPromptConfig": {
        "includeSections": ["<string>", ...]
      }
    }
  }
}
```

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Unique identifier. Use `snake_case` (lowercase, digits, underscores). Max 64 characters. Must match the directory name. |
| `description` | string | Yes | Explains the agent's purpose. Used by the parent agent to decide when to spawn it. |
| `hidden` | boolean | No | If `true`, the agent is not shown in UI agent lists. Defaults to `false`. Set to `true` for subagents that should only be spawned programmatically. |

### `config.customAgent` Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `systemPromptSections` | array | Yes | Array of `{title, content}` objects injected into the agent's system prompt. |
| `toolNames` | array | Yes | Whitelist of tools the agent can use. Only listed tools are available. |
| `systemPromptConfig` | object | No | Controls which standard system prompt sections are included. |

### `systemPromptSections` Entry

| Field | Type | Description |
|---|---|---|
| `title` | string | Header for the prompt section (e.g., "Agent System Instructions"). |
| `content` | string | The system prompt content. Use `\n` for newlines inside the JSON string. |

---

## Valid Tool Names

### Read-Only Tools
These tools allow the agent to research and communicate without modifying the workspace:

| Tool | Purpose |
|---|---|
| `send_message` | **Required.** Communicate with parent agent. |
| `find_by_name` | Search for files and symbols by name. |
| `grep_search` | Search file contents with ripgrep. |
| `view_file` | Read file contents. |
| `list_dir` | List directory contents. |
| `read_url_content` | Fetch content from URLs. |
| `search_web` | Perform web searches. |
| `schedule` | Set timers and cron jobs. |
| `manage_task` | Manage background tasks. |

### Write/Execute Tools
These tools allow the agent to modify files and run commands:

| Tool | Purpose |
|---|---|
| `multi_replace_file_content` | Edit multiple non-contiguous sections of a file. |
| `replace_file_content` | Edit a single contiguous section of a file. |
| `write_to_file` | Create new files. |
| `run_command` | Execute shell commands. |

### Specialized Tools

| Tool | Purpose |
|---|---|
| `generate_image` | Generate images from text prompts. |
| `ask_question` | Ask the user multiple-choice questions. |
| `ask_permission` | Request additional permissions from the user. |

---

## Valid `includeSections` Values

These control which standard prompt sections the harness injects alongside your custom prompt:

| Section | Description |
|---|---|
| `user_information` | User's OS, workspace paths, and environment info. |
| `mcp_servers` | Available MCP server tools and configurations. |
| `skills` | Available skill names and descriptions for progressive disclosure. |
| `subagent_reminder` | Instructions for spawning and managing subagents. |
| `messaging` | Instructions for the messaging system between agents. |
| `artifacts` | Instructions for creating and managing artifact documents. |
| `user_rules` | User-defined rules from `GEMINI.md`, `AGENTS.md`, and `.agents/rules/`. |

---

## Common Tool Presets

### Verifier / Reviewer (read-heavy, can run tests)
```json
"toolNames": [
  "send_message", "find_by_name", "grep_search", "view_file", "list_dir",
  "read_url_content", "search_web", "schedule", "manage_task",
  "run_command"
]
```

### Implementer (full read/write/execute)
```json
"toolNames": [
  "send_message", "find_by_name", "grep_search", "view_file", "list_dir",
  "read_url_content", "search_web", "schedule", "manage_task",
  "multi_replace_file_content", "replace_file_content", "write_to_file",
  "run_command"
]
```

### Researcher (read-only, no execution)
```json
"toolNames": [
  "send_message", "find_by_name", "grep_search", "view_file", "list_dir",
  "read_url_content", "search_web", "schedule", "manage_task"
]
```
