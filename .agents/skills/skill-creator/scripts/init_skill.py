#!/usr/bin/env python3
"""
Skill Initializer - Creates a new agnostic Agent Skill from template.

Usage:
    init_skill.py <skill-name> --path <path>
"""

import sys
import re
from pathlib import Path

SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Add a clear description of what this skill does and WHEN the agent should use it. Include specific triggers, file types, or user intents.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining the core capability this skill provides.]

## Instructions

[TODO: Add step-by-step instructions for the agent.
- Use imperative mood ("Do this", "Check that").
- Define clear steps for the workflow.
- Reference bundled scripts or docs where necessary.]

## Capabilities

[TODO: List specific capabilities or workflows.]
1. **Capability A**: Description of how to handle this case.
2. **Capability B**: Description of how to handle that case.

## Resources

This skill uses the following resources:

### Scripts
[TODO: Describe any scripts included in scripts/ and when to run them.]

### References
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

def title_case_skill_name(skill_name):
    return ' '.join(word.capitalize() for word in skill_name.split('-'))

def init_skill(skill_name, path):
    if not re.match(r'^[a-z0-9-]+$', skill_name):
        print(f"❌ Error: Skill name '{skill_name}' must be kebab-case (lowercase, numbers, hyphens only).")
        return None

    skill_dir = Path(path).resolve() / skill_name
    
    if skill_dir.exists():
        print(f"❌ Error: Directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        (skill_dir / 'scripts').mkdir()
        (skill_dir / 'references').mkdir()
        (skill_dir / 'assets').mkdir()
        
        # Create SKILL.md
        skill_title = title_case_skill_name(skill_name)
        (skill_dir / 'SKILL.md').write_text(SKILL_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title))
            
        # Create example script
        script_path = skill_dir / 'scripts' / 'example.py'
        script_path.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        script_path.chmod(0o755)

        print(f"✅ Skill '{skill_name}' initialized at {skill_dir}")
        return skill_dir
    except Exception as e:
        print(f"❌ Error initializing skill: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("Usage: init_skill.py <skill-name> --path <path>")
        sys.exit(1)
    init_skill(sys.argv[1], sys.argv[3])