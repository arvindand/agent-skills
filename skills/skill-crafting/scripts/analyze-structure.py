#!/usr/bin/env python3
"""
Structure Validator for Agent Skills.

Validates SKILL.md structure, frontmatter, and naming conventions.
"""

import sys
import re
from pathlib import Path

from frontmatter import parse_frontmatter


def validate_name(name: str) -> list:
    """Validate skill name against conventions."""
    issues = []

    if not name:
        issues.append("Missing required field: name")
        return issues

    if len(name) > 64:
        issues.append(f"Name too long: {len(name)} chars (max 64)")

    if name != name.lower():
        issues.append("Name must be lowercase")

    if '_' in name:
        issues.append("Use hyphens, not underscores")

    if ' ' in name:
        issues.append("No spaces allowed in name")

    if not re.match(r'^[a-z][a-z0-9\-]*$', name):
        issues.append("Name must start with letter, contain only lowercase, numbers, hyphens")

    return issues


def validate_frontmatter(content: str) -> dict:
    """Validate YAML frontmatter."""
    result = {
        'valid': False,
        'issues': [],
        'warnings': [],
        'data': {}
    }

    # Check if starts with ---
    if not content.startswith('---'):
        result['issues'].append("File must start with --- (YAML frontmatter)")
        return result

    # Parse YAML
    try:
        data, _ = parse_frontmatter(content)
        if not data:
            result['issues'].append("Frontmatter must be a YAML mapping")
            return result
        result['data'] = data
    except ValueError as e:
        result['issues'].append(f"Invalid YAML: {e}")
        return result

    # Check required fields
    if 'name' not in data:
        result['issues'].append("Missing required field: name")
    if 'description' not in data:
        result['issues'].append("Missing required field: description")

    # Validate name
    if 'name' in data:
        name_issues = validate_name(data['name'])
        result['issues'].extend(name_issues)

    # Check description
    if 'description' in data:
        desc = data['description']
        if len(desc) > 1024:
            result['issues'].append(f"Description too long: {len(desc)} chars (max 1024)")
        elif len(desc) > 500:
            result['warnings'].append(f"Description is {len(desc)} chars (recommend <500)")

    # Check optional fields
    known_fields = {
        'name', 'description', 'license', 'compatibility', 'metadata',
        'allowed-tools', 'hooks', 'context'
    }
    for field in data:
        if field not in known_fields:
            result['warnings'].append(f"Unknown field: {field}")

    if not result['issues']:
        result['valid'] = True

    return result


def validate_skill_directory(dirpath: str) -> dict:
    """Validate a skill directory structure."""
    path = Path(dirpath)
    result = {
        'valid': False,
        'issues': [],
        'warnings': [],
        'structure': {}
    }

    if not path.exists():
        result['issues'].append(f"Directory not found: {dirpath}")
        return result

    if not path.is_dir():
        # It's a file, assume SKILL.md
        skill_path = path
        path = path.parent
    else:
        skill_path = path / 'SKILL.md'

    # Check SKILL.md exists
    if not skill_path.exists():
        result['issues'].append("Missing SKILL.md file")
        return result

    # Check case sensitivity
    actual_files = [f.name for f in path.iterdir() if f.is_file()]
    if 'SKILL.md' not in actual_files and any(f.lower() == 'skill.md' for f in actual_files):
        result['issues'].append("SKILL.md must be uppercase (case-sensitive)")

    # Validate frontmatter
    content = skill_path.read_text(encoding='utf-8')
    fm_result = validate_frontmatter(content)
    result['issues'].extend(fm_result['issues'])
    result['warnings'].extend(fm_result['warnings'])
    result['structure']['frontmatter'] = fm_result['data']

    # Check for common directories
    scripts_dir = path / 'scripts'
    refs_dir = path / 'references'

    if scripts_dir.exists():
        result['structure']['scripts'] = list(scripts_dir.glob('*'))
    if refs_dir.exists():
        result['structure']['references'] = list(refs_dir.glob('*'))

    # Check SKILL.md line count
    lines = content.count('\n') + 1
    if lines > 500:
        result['warnings'].append(f"SKILL.md is {lines} lines (recommend <500, use references)")
    result['structure']['lines'] = lines

    # Check for LICENSE
    if not (path / 'LICENSE').exists():
        result['warnings'].append("No LICENSE file found")

    if not result['issues']:
        result['valid'] = True

    return result


def print_validation(result: dict, name: str = 'Unknown'):
    """Print validation results."""
    print(f"\n=== Structure Validation: {name} ===\n")

    if result['valid']:
        print("✅ Structure is valid")
    else:
        print("❌ Structure has issues")

    if result['issues']:
        print("\nIssues:")
        for issue in result['issues']:
            print(f"  ❌ {issue}")

    if result['warnings']:
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")

    if 'structure' in result:
        struct = result['structure']
        print("\nStructure:")
        if 'lines' in struct:
            print(f"  📄 SKILL.md: {struct['lines']} lines")
        if 'scripts' in struct:
            print(f"  📁 scripts/: {len(struct['scripts'])} files")
        if 'references' in struct:
            print(f"  📁 references/: {len(struct['references'])} files")

    return 0 if result['valid'] else 1


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze-structure.py <path/to/skill/>")
        print("\nValidates skill directory structure and SKILL.md format.")
        sys.exit(1)

    dirpath = sys.argv[1]
    result = validate_skill_directory(dirpath)

    name = result.get('structure', {}).get('frontmatter', {}).get('name', 'Unknown')
    exit_code = print_validation(result, name)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
