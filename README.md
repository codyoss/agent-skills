# Antigravity Customizations & Skills

This repository contains custom agents, skills, and plugins for the Antigravity developer environment (`agy`). It provides tools, agent definitions, and shell plugins to enhance your AI-assisted development workflow.

## Directory Structure

- **`.agents/agents/`**: Definitions and configurations for custom agents.
  - `completion_implementer`: Helper agent for implementing code completion features.
  - `mcp_implementer`: Assistant for building Model Context Protocol (MCP) integrations.
  - `milestone_verifier`: Handles verifying milestones during task execution.
  - `verifier_subagent`: Subagent for automated code execution and test verification.
- **`.agents/skills/`**: Instruction manuals and guidelines that extend agent capabilities (e.g., Go standards, commits, TDD loops).
  - `agent-creator`: Guide for creating and managing custom agent profiles.
  - `conventional-commits`: Git commit formatting standards.
  - `design-review`: Templates and methodology for reviewing design docs.
  - `skill-creator`: Guidelines for building and updating agent skills.
  - `subagent-orchestration`: Subagent patterns for Test-Driven Development (TDD).
  - `writing-go`: Best practices and standard guidelines for writing Go.
- **`plugins/`**: Custom CLI/shell integration scripts.
  - `statusline.sh`: A rich terminal statusline plugin displaying tool status, models, token counts, and sandbox states.
- **`scripts/`**: Automation scripts for repository setup and management.
  - `link_customizations.sh`: Script to manage installing/uninstalling customizations.

## Installation / Linking Customizations

To install these customizations (agents, skills, and plugins) to your local machine, use the provided configuration linking script: `scripts/link_customizations.sh`.

This script creates symbolic links from this repository to your global Antigravity configuration directory (`~/.gemini/config/`).

### Usage

Run the script from the root of the repository:

```bash
./scripts/link_customizations.sh [action] [options]
```

#### Actions

- **`link`** (Default): Creates symlinks for agents, skills, and plugins.
  ```bash
  ./scripts/link_customizations.sh link
  ```
- **`unlink`**: Removes the created symlinks from the Antigravity configuration directory.
  ```bash
  ./scripts/link_customizations.sh unlink
  ```

#### Options

- **`-d`, `--dry-run`**: Performs a trial run showing what links would be created or removed without modifying the filesystem.
  ```bash
  ./scripts/link_customizations.sh link --dry-run
  ```
- **`-h`, `--help`**: Shows the command help menu.

### How It Works

1. The script automatically reads the source directories:
   - `.agents/agents` -> Linked to `~/.gemini/config/agents/`
   - `.agents/skills` -> Linked to `~/.gemini/config/skills/`
   - `plugins` -> Linked to `~/.gemini/config/plugins/`
2. It creates the destination directories if they do not exist.
3. If a symlink already exists and is correct, it is skipped.
4. If a file/folder exists at the destination and is not a symlink, it creates a backup copy with a `.bak` extension and replaces the target with a symlink.
