#!/usr/bin/env python3
"""
Cross-Platform Compatibility Analyzer for Agent Skills.

Checks which fields are part of the Agent Skills standard (cross-platform)
versus Claude Code extensions (platform-specific).
"""

import sys
from pathlib import Path

from frontmatter import parse_simple_yaml


# Agent Skills Standard (agentskills.io) - works everywhere
# Per Anthropic docs, only `name` and `description` are required. Other fields
# below are tolerated by analyzers but not part of the upstream spec.
STANDARD_FIELDS = {
    'name': 'Required - skill identifier',
    'description': 'Required - what it does and when to use',
    'license': 'Optional - license name or file reference',
    'compatibility': 'Legacy convention - prose about cross-platform behavior',
    'metadata': 'Optional - arbitrary key-value pairs',
}

# Claude Code Extensions - gracefully ignored by other platforms
CLAUDE_CODE_FIELDS = {
    'allowed-tools': 'Tool pre-authorization',
    'hooks': 'Event hooks (PreToolUse, PostToolUse, UserPromptSubmit, Stop)',
    'context': 'Execution context (fork for isolated subagent)',
}

# Known hook types
HOOK_TYPES = ['PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop', 'Notification', 'SessionStart', 'SubagentStop']


def parse_frontmatter(skill_path: Path) -> dict:
    """Parse SKILL.md frontmatter."""
    skill_md = skill_path / 'SKILL.md' if skill_path.is_dir() else skill_path

    if not skill_md.exists():
        return {'error': f"File not found: {skill_md}"}

    try:
        content = skill_md.read_text(encoding='utf-8')
        if not content.startswith('---'):
            return {'error': "Missing YAML frontmatter"}

        end = content.index('---', 3)
        yaml_content = content[3:end].strip()
        return parse_simple_yaml(yaml_content)
    except ValueError as e:
        return {'error': f"YAML parse error: {e}"}


def analyze_compatibility(frontmatter: dict) -> dict:
    """Analyze frontmatter for platform compatibility."""
    if 'error' in frontmatter:
        return frontmatter

    result = {
        'standard_fields': [],
        'claude_code_fields': [],
        'unknown_fields': [],
        'hooks_detected': [],
        'is_cross_platform': True,
        'recommendations': [],
    }

    for field, value in frontmatter.items():
        if field in STANDARD_FIELDS:
            result['standard_fields'].append({
                'field': field,
                'value': str(value)[:50] + '...' if len(str(value)) > 50 else str(value),
                'note': STANDARD_FIELDS[field],
            })
        elif field in CLAUDE_CODE_FIELDS:
            result['claude_code_fields'].append({
                'field': field,
                'note': CLAUDE_CODE_FIELDS[field],
            })
            result['is_cross_platform'] = False

            # Analyze hooks
            if field == 'hooks' and isinstance(value, dict):
                for hook_type in value:
                    result['hooks_detected'].append(hook_type)

        else:
            result['unknown_fields'].append(field)

    # Check required fields
    if 'name' not in frontmatter:
        result['recommendations'].append("Add required field: name")
    if 'description' not in frontmatter:
        result['recommendations'].append("Add required field: description")

    return result


def print_analysis(result: dict, name: str = 'Unknown'):
    """Print compatibility analysis."""
    print(f"\n=== Platform Compatibility: {name} ===\n")

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return 1

    # Cross-platform status
    if result['is_cross_platform']:
        print("✅ Fully cross-platform (Agent Skills standard only)")
    else:
        print("⚠️  Uses Claude Code extensions (gracefully degraded elsewhere)")

    # Standard fields
    print("\n--- Agent Skills Standard (cross-platform) ---")
    for item in result['standard_fields']:
        print(f"  ✅ {item['field']}: {item['note']}")

    # Claude Code extensions
    if result['claude_code_fields']:
        print("\n--- Claude Code Extensions ---")
        for item in result['claude_code_fields']:
            print(f"  🔵 {item['field']}: {item['note']}")

        if result['hooks_detected']:
            print(f"\n  Hooks: {', '.join(result['hooks_detected'])}")

    # Unknown fields
    if result['unknown_fields']:
        print("\n--- Unknown Fields ---")
        for field in result['unknown_fields']:
            print(f"  ❓ {field}")

    # Recommendations
    if result['recommendations']:
        print("\n📝 Recommendations:")
        for rec in result['recommendations']:
            print(f"   - {rec}")

    # Platform support summary
    print("\n--- Platform Support ---")
    platforms = [
        ('Claude Code', True),
        ('GitHub Copilot', result['is_cross_platform']),
        ('VS Code Copilot', result['is_cross_platform']),
        ('Cursor', result['is_cross_platform']),
        ('Codex CLI', result['is_cross_platform']),
        ('OpenCode', result['is_cross_platform']),
        ('Gemini CLI', result['is_cross_platform']),
    ]

    for platform, supported in platforms:
        status = "✅ Full" if supported else "⚠️ Core only"
        print(f"  {platform:20} {status}")

    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze-compatibility.py <path/to/skill/>")
        print("\nChecks which fields are cross-platform vs Claude Code specific.")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    frontmatter = parse_frontmatter(skill_path)

    name = frontmatter.get('name', 'Unknown') if 'error' not in frontmatter else 'Unknown'
    result = analyze_compatibility(frontmatter)

    exit_code = print_analysis(result, name)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
