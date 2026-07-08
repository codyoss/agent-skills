#!/usr/bin/env python3
"""
Agent Profile Validator - Checks compliance with the agent.json specification.
"""

import sys
import json
from pathlib import Path

MAX_AGENT_NAME_LENGTH = 64

VALID_TOOLS = {
    "send_message", "find_by_name", "grep_search", "view_file", "list_dir",
    "read_url_content", "search_web", "schedule", "multi_replace_file_content",
    "replace_file_content", "write_to_file", "run_command", "manage_task",
    "generate_image", "ask_question", "ask_permission"
}

VALID_SECTIONS = {
    "user_information", "mcp_servers", "skills", "subagent_reminder",
    "messaging", "artifacts", "user_rules"
}


def validate_agent(agent_path):
    """Validate an agent profile directory."""
    agent_path = Path(agent_path)
    agent_json = agent_path / "agent.json"

    if not agent_json.exists():
        return False, "agent.json not found."

    try:
        data = json.loads(agent_json.read_text())
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    if not isinstance(data, dict):
        return False, "agent.json must be a JSON object."

    # Required fields
    if "name" not in data:
        return False, "Missing required field: 'name'"
    if "description" not in data:
        return False, "Missing required field: 'description'"

    name = data["name"]
    if not isinstance(name, str) or not name.strip():
        return False, "'name' must be a non-empty string."
    if len(name) > MAX_AGENT_NAME_LENGTH:
        return False, f"Name is too long ({len(name)} characters). Maximum is {MAX_AGENT_NAME_LENGTH}."
    if not all(c.isalnum() or c == '_' for c in name):
        return False, f"Name '{name}' must contain only alphanumeric characters and underscores."

    desc = data["description"]
    if not isinstance(desc, str) or not desc.strip():
        return False, "'description' must be a non-empty string."
    if "[TODO" in desc:
        return False, "Description still contains a TODO placeholder."

    # Config structure
    config = data.get("config")
    if not isinstance(config, dict):
        return False, "Missing or invalid 'config' object."

    custom_agent = config.get("customAgent")
    if not isinstance(custom_agent, dict):
        return False, "Missing or invalid 'config.customAgent' object."

    # System prompt sections
    prompt_sections = custom_agent.get("systemPromptSections")
    if not isinstance(prompt_sections, list) or len(prompt_sections) == 0:
        return False, "'systemPromptSections' must be a non-empty array."

    for i, section in enumerate(prompt_sections):
        if not isinstance(section, dict):
            return False, f"systemPromptSections[{i}] must be an object."
        if "title" not in section or "content" not in section:
            return False, f"systemPromptSections[{i}] must have 'title' and 'content' fields."
        if "[TODO" in section.get("content", ""):
            return False, f"systemPromptSections[{i}].content still contains a TODO placeholder."

    # Tool names
    tool_names = custom_agent.get("toolNames")
    if not isinstance(tool_names, list):
        return False, "'toolNames' must be an array."
    if "send_message" not in tool_names:
        return False, "'send_message' must be included in toolNames (required for subagent communication)."

    unknown_tools = set(tool_names) - VALID_TOOLS
    if unknown_tools:
        return False, f"Unknown tool(s): {', '.join(sorted(unknown_tools))}"

    # System prompt config
    prompt_config = custom_agent.get("systemPromptConfig")
    if isinstance(prompt_config, dict):
        include_sections = prompt_config.get("includeSections", [])
        unknown_sections = set(include_sections) - VALID_SECTIONS
        if unknown_sections:
            return False, f"Unknown includeSections: {', '.join(sorted(unknown_sections))}"

    return True, "Agent profile is valid."


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_agent.py <agent-folder>")
        sys.exit(1)

    valid, msg = validate_agent(sys.argv[1])
    print(msg)
    sys.exit(0 if valid else 1)
