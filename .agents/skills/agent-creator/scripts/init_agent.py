#!/usr/bin/env python3
"""
Agent Profile Initializer - Creates a new custom agent profile from template.

Usage:
    init_agent.py <agent-name> --path <path>
"""

import sys
import re
import argparse
import json
from pathlib import Path

MAX_AGENT_NAME_LENGTH = 64

AGENT_TEMPLATE = {
    "name": "",
    "description": "[TODO: Describe what this agent does and when the parent should spawn it.]",
    "hidden": True,
    "config": {
        "customAgent": {
            "systemPromptSections": [
                {
                    "title": "Agent System Instructions",
                    "content": "[TODO: Write the agent's system prompt. Use imperative mood. Define: role, goals, coding standards, and output format.]"
                }
            ],
            "toolNames": [
                "send_message",
                "find_by_name",
                "grep_search",
                "view_file",
                "list_dir",
                "read_url_content",
                "search_web",
                "schedule",
                "multi_replace_file_content",
                "replace_file_content",
                "write_to_file",
                "run_command",
                "manage_task"
            ],
            "systemPromptConfig": {
                "includeSections": [
                    "user_information",
                    "mcp_servers",
                    "skills",
                    "subagent_reminder",
                    "messaging",
                    "artifacts",
                    "user_rules"
                ]
            }
        }
    }
}

READ_ONLY_TOOLS = [
    "send_message",
    "find_by_name",
    "grep_search",
    "view_file",
    "list_dir",
    "read_url_content",
    "search_web",
    "schedule",
    "manage_task"
]

FULL_TOOLS = READ_ONLY_TOOLS + [
    "multi_replace_file_content",
    "replace_file_content",
    "write_to_file",
    "run_command"
]


def normalize_agent_name(name):
    """Normalize an agent name to lowercase with underscores."""
    normalized = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    normalized = re.sub(r"_{2,}", "_", normalized)
    return normalized


def init_agent(agent_name, path, read_only=False):
    """Initialize a new agent profile directory with a template agent.json."""
    normalized_name = normalize_agent_name(agent_name)
    if not normalized_name:
        print("Error: Agent name must contain alphanumeric characters.")
        return None

    if len(normalized_name) > MAX_AGENT_NAME_LENGTH:
        print(f"Error: Agent name exceeds maximum length of {MAX_AGENT_NAME_LENGTH} characters.")
        return None

    agent_dir = Path(path).resolve() / normalized_name

    if agent_dir.exists():
        print(f"Error: Directory already exists: {agent_dir}")
        return None

    try:
        agent_dir.mkdir(parents=True, exist_ok=False)

        template = json.loads(json.dumps(AGENT_TEMPLATE))
        template["name"] = normalized_name

        if read_only:
            template["config"]["customAgent"]["toolNames"] = READ_ONLY_TOOLS

        agent_json_path = agent_dir / "agent.json"
        agent_json_path.write_text(json.dumps(template, indent=2) + "\n")

        print(f"Agent '{normalized_name}' initialized at {agent_dir}")
        print(f"\nNext steps:")
        print(f"1. Edit {agent_json_path} to customize the system prompt")
        print(f"2. Update the description to explain when to spawn this agent")
        print(f"3. Run validate_agent.py to check the profile")
        return agent_dir
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new custom agent profile.")
    parser.add_argument("agent_name", help="Agent name (will be normalized to snake_case)")
    parser.add_argument("--path", required=True, help="Output directory for the agent")
    parser.add_argument("--read-only", action="store_true", help="Create a read-only agent (no write/execute tools)")
    args = parser.parse_args()

    init_agent(args.agent_name, args.path, args.read_only)
