#!/usr/bin/env python3
"""
Skill Validator - Checks compliance with Agent Skills specification.

Requires PyYAML (`pip install pyyaml`).
"""

import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is required. Install it with `pip install pyyaml`.")
    sys.exit(1)

MAX_SKILL_NAME_LENGTH = 64
MAX_BODY_LINES = 500
ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata"}
# Resource folders whose files must be mentioned in SKILL.md so the agent can discover them.
DISCOVERABLE_RESOURCES = ("scripts", "references")

def validate_skill(skill_path):
    """Returns a list of error messages; an empty list means the skill is valid."""
    skill_path = Path(skill_path)
    skill_md = skill_path / 'SKILL.md'

    if not skill_md.exists():
        return ["SKILL.md not found."]

    content = skill_md.read_text()
    if not content.startswith("---"):
        return ["No YAML frontmatter found."]

    match = re.match(r'^---\n(.*?)\n---\n?', content, re.DOTALL)
    if not match:
        return ["Missing or invalid YAML frontmatter."]

    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return ["Frontmatter must be a YAML dictionary."]
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]

    errors = []

    # Check for unexpected properties
    unexpected_keys = set(data.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        allowed = ", ".join(sorted(ALLOWED_PROPERTIES))
        unexpected = ", ".join(sorted(unexpected_keys))
        errors.append(f"Unexpected key(s) in SKILL.md frontmatter: {unexpected}. Allowed: {allowed}")

    # Spec Validation
    if 'name' not in data:
        errors.append("Missing required field: 'name'")
    else:
        name = data['name']
        if not isinstance(name, str):
            errors.append(f"Name must be a string, got {type(name).__name__}")
        else:
            name = name.strip()
            if not re.match(r'^[a-z0-9-]+$', name):
                errors.append(f"Name '{name}' must be kebab-case (lowercase, numbers, hyphens only).")
            if name.startswith("-") or name.endswith("-") or "--" in name:
                errors.append(f"Name '{name}' cannot start/end with a hyphen or contain consecutive hyphens.")
            if len(name) > MAX_SKILL_NAME_LENGTH:
                errors.append(f"Name is too long ({len(name)} characters). Maximum is {MAX_SKILL_NAME_LENGTH} characters.")
            if name != skill_path.resolve().name:
                errors.append(f"Name '{name}' does not match the skill folder name '{skill_path.resolve().name}'.")

    if 'description' not in data:
        errors.append("Missing required field: 'description'")
    else:
        desc = data['description']
        if not isinstance(desc, str):
            errors.append(f"Description must be a string, got {type(desc).__name__}")
        else:
            desc = desc.strip()
            if "<" in desc or ">" in desc:
                errors.append("Description cannot contain angle brackets (< or >).")
            if len(desc) > 1024:
                errors.append(f"Description is too long ({len(desc)} characters). Maximum is 1024 characters.")

    body = content[match.end():]
    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        errors.append(f"SKILL.md body is {body_lines} lines. Maximum is {MAX_BODY_LINES}; move detail into references/.")

    # Every relative markdown link must resolve to a file inside the skill.
    # Links inside fenced code blocks are illustrative examples, so skip them.
    prose = re.sub(r'^(```|~~~).*?^\1', '', body, flags=re.DOTALL | re.MULTILINE)
    for target in re.findall(r'\]\(([^)\s#]+)(?:#[^)]*)?\)', prose):
        if re.match(r'^[a-z]+:', target):
            continue
        if not (skill_path / target).exists():
            errors.append(f"SKILL.md links to '{target}', which does not exist.")

    # Every bundled script/reference must be mentioned so the agent can discover it.
    for resource in DISCOVERABLE_RESOURCES:
        resource_dir = skill_path / resource
        if not resource_dir.is_dir():
            continue
        for f in sorted(p for p in resource_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            if f.name not in body:
                errors.append(f"{f.relative_to(skill_path)} is never mentioned in SKILL.md, so the agent cannot discover it.")

    return errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py <skill-folder>")
        sys.exit(1)

    errors = validate_skill(sys.argv[1])
    if errors:
        for err in errors:
            print(f"❌ {err}")
        sys.exit(1)
    print("✅ Skill is valid.")
