#!/usr/bin/env python3
"""
Skill Validator - Checks compliance with Agent Skills specification.
"""

import sys
import re
import yaml
from pathlib import Path

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata"}

def validate_skill(skill_path):
    skill_path = Path(skill_path)
    skill_md = skill_path / 'SKILL.md'
    
    if not skill_md.exists():
        return False, "SKILL.md not found."

    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found."

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Missing or invalid YAML frontmatter."

    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return False, "Frontmatter must be a YAML dictionary."
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"

    # Check for unexpected properties
    unexpected_keys = set(data.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        allowed = ", ".join(sorted(ALLOWED_PROPERTIES))
        unexpected = ", ".join(sorted(unexpected_keys))
        return False, f"Unexpected key(s) in SKILL.md frontmatter: {unexpected}. Allowed: {allowed}"

    # Spec Validation
    if 'name' not in data:
        return False, "Missing required field: 'name'"
    if 'description' not in data:
        return False, "Missing required field: 'description'"

    name = data['name']
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not re.match(r'^[a-z0-9-]+$', name):
        return False, f"Name '{name}' must be kebab-case (lowercase, numbers, hyphens only)."
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, f"Name '{name}' cannot start/end with a hyphen or contain consecutive hyphens."
    if len(name) > MAX_SKILL_NAME_LENGTH:
        return False, f"Name is too long ({len(name)} characters). Maximum is {MAX_SKILL_NAME_LENGTH} characters."
        
    desc = data['description']
    if not isinstance(desc, str):
        return False, f"Description must be a string, got {type(desc).__name__}"
    desc = desc.strip()
    if "<" in desc or ">" in desc:
        return False, "Description cannot contain angle brackets (< or >)."
    if len(desc) > 1024:
        return False, f"Description is too long ({len(desc)} characters). Maximum is 1024 characters."

    return True, "Skill is valid."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py <skill-folder>")
        sys.exit(1)
    
    valid, msg = validate_skill(sys.argv[1])
    print(msg)
    sys.exit(0 if valid else 1)