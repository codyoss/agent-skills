#!/usr/bin/env python3
"""
Skill Initializer - Creates a new agnostic Agent Skill from template.

Usage:
    init_skill.py <skill-name> --path <path> [--resources scripts,references,assets] [--examples]
"""

import sys
import re
import argparse
from pathlib import Path

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"scripts", "references", "assets"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Add a clear description of what this skill does and WHEN the agent should use it. Use "Use when..." to define triggers, file types, or user intents. Use "Don't use for..." to establish negative constraints.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining the core capability this skill provides.]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Delete this entire section when done.

Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Structure: ## Overview -> ## Step 1 -> ## Step 2...

**2. Task-Based** (best for tool collections or utilities)
- Structure: ## Overview -> ## Task Category 1 -> ## Task Category 2...

**3. Reference/Guidelines** (best for standards or rules)
- Structure: ## Overview -> ## Guidelines -> ## Specifications...

**4. Capabilities-Based** (best for integrated systems)
- Structure: ## Overview -> ## Core Capabilities -> ### 1. Feature A -> ### 2. Feature B...]

## Instructions

[TODO: Add step-by-step instructions for the agent. Use imperative mood ("Do this", "Check that"). Define clear steps for the workflow. Reference bundled scripts or docs where necessary.]

## Resources (Optional)

[TODO: List and describe resources below, or delete the unused sections.]

### scripts/
[TODO: Describe any scripts included in scripts/ and when to run them.]

### references/
[TODO: Describe any documentation in references/ and when the agent should read them.]
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}.
This script can be executed by the agent to perform deterministic tasks.
"""

def main():
    print("Executing {skill_name} helper script...")
    # TODO: Add logic here (API calls, file processing, calculation, etc.)

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output produced by the agent.
"""

def normalize_skill_name(skill_name):
    """Normalize a skill name to lowercase hyphen-case."""
    normalized = skill_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized

def title_case_skill_name(skill_name):
    return ' '.join(word.capitalize() for word in skill_name.split('-'))

def init_skill(skill_name, path, resources_list, include_examples):
    normalized_name = normalize_skill_name(skill_name)
    if not normalized_name:
        print("❌ Error: Skill name must contain alphanumeric characters.")
        return None

    if len(normalized_name) > MAX_SKILL_NAME_LENGTH:
        print(f"❌ Error: Skill name exceeds maximum length of {MAX_SKILL_NAME_LENGTH} characters.")
        return None

    skill_dir = Path(path).resolve() / normalized_name
    
    if skill_dir.exists():
        print(f"❌ Error: Directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        
        # Determine resources to create
        if resources_list:
            resources = [r.strip() for r in resources_list.split(",") if r.strip()]
            for r in resources:
                if r not in ALLOWED_RESOURCES:
                    print(f"❌ Error: Unknown resource type '{r}'. Allowed: {', '.join(ALLOWED_RESOURCES)}")
                    return None
        else:
            resources = list(ALLOWED_RESOURCES)

        # Create resource directories and example files
        for resource in resources:
            r_dir = skill_dir / resource
            r_dir.mkdir()
            if include_examples:
                if resource == "scripts":
                    script_path = r_dir / "example.py"
                    script_path.write_text(EXAMPLE_SCRIPT.format(skill_name=normalized_name))
                    script_path.chmod(0o755)
                elif resource == "references":
                    skill_title = title_case_skill_name(normalized_name)
                    (r_dir / "api_reference.md").write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
                elif resource == "assets":
                    (r_dir / "example_asset.txt").write_text(EXAMPLE_ASSET)

        # Create SKILL.md
        skill_title = title_case_skill_name(normalized_name)
        (skill_dir / 'SKILL.md').write_text(SKILL_TEMPLATE.format(
            skill_name=normalized_name, skill_title=skill_title))

        print(f"✅ Skill '{normalized_name}' initialized at {skill_dir}")
        return skill_dir
    except Exception as e:
        print(f"❌ Error initializing skill: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new skill directory with a SKILL.md template.")
    parser.add_argument("skill_name", help="Skill name (will be normalized to kebab-case)")
    parser.add_argument("--path", required=True, help="Output directory for the skill")
    parser.add_argument("--resources", help="Comma-separated list of resources to create (scripts,references,assets)")
    parser.add_argument("--examples", action="store_true", help="Create example placeholder files inside the resource directories")
    args = parser.parse_args()

    init_skill(args.skill_name, args.path, args.resources, args.examples)