#!/usr/bin/env python3
"""
Skill Validator - Checks compliance with Agent Skills specification.
"""

import sys
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    skill_path = Path(skill_path)
    skill_md = skill_path / 'SKILL.md'
    
    if not skill_md.exists():
        return False, "SKILL.md not found."

    content = skill_md.read_text()
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    
    if not match:
        return False, "Missing or invalid YAML frontmatter."

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"

    # Spec Validation
    if 'name' not in data:
        return False, "Missing required field: 'name'"
    if 'description' not in data:
        return False, "Missing required field: 'description'"

    name = data['name']
    if not re.match(r'^[a-z0-9-]+$', name):
        return False, f"Name '{name}' must be kebab-case (lowercase, numbers, hyphens only)."
    if len(name) > 64:
        return False, "Name exceeds 64 characters."
        
    desc = data['description']
    if len(desc) > 1024:
        return False, "Description exceeds 1024 characters."

    return True, "Skill is valid."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py <skill-folder>")
        sys.exit(1)
    
    valid, msg = validate_skill(sys.argv[1])
    print(msg)
    sys.exit(0 if valid else 1)