#!/usr/bin/env python3
"""
CSO (Claude Search Optimization) Analyzer for Agent Skills.

Checks skill descriptions for common CSO violations that prevent auto-triggering.
"""

import sys
import re
from pathlib import Path

from frontmatter import parse_frontmatter


# Workflow hint patterns that should NOT be in descriptions
WORKFLOW_HINTS = [
    (r'\bruns?\b.*\bcommands?\b', 'Mentions running commands (workflow hint)'),
    (r'\bexecutes?\b', 'Uses "execute" (workflow hint)'),
    (r'\bdiscover\w*\s+\w*\s*dynamically', 'Mentions dynamic discovery (workflow hint)'),
    (r'\bstep\s*\d', 'References steps (workflow hint)'),
    # "reusable workflow" is a trigger phrase, not a workflow summary
    (r'(?<!reusable )\bworkflow\b', 'Uses "workflow" in description'),
    (r'\bprocess\b.*\b(files?|data)\b', 'Describes processing (workflow hint)'),
    (r'\bparses?\b', 'Uses "parse" (workflow hint)'),
    (r'\banalyzes?\s+and\s+', 'Describes analysis process (workflow hint)'),
    (r'\bfirst\b.*\bthen\b', 'Sequential process description (workflow hint)'),
    (r'\bby\s+(running|executing|calling)', 'Describes how it works'),
]

# First person patterns
FIRST_PERSON = [
    (r'\bI\s+(can|will|am|help)\b', 'Uses first person "I"'),
    (r'\bmy\b', 'Uses first person "my"'),
    (r"\bI'm\b", 'Uses first person "I\'m"'),
    (r'\bI\'ll\b', 'Uses first person "I\'ll"'),
]

# Good patterns to look for
GOOD_PATTERNS = [
    (r'^[A-Z][^.]+\.', 'Starts with capability statement'),
    (r'\buse\s+when\b', 'Includes "Use when" triggers'),
    (r'\buser\s+(says?|asks?|provides?|mentions?)\b', 'References user actions'),
    (r"'[^']+'\s*,?\s*'[^']+'", 'Includes example phrases'),
]


def parse_skill_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from SKILL.md content."""
    data, _ = parse_frontmatter(content)
    return data


def analyze_description(description: str) -> dict:
    """Analyze a skill description for CSO issues."""
    issues = []
    warnings = []
    good = []

    desc_lower = description.lower()

    # Check for workflow hints
    for pattern, message in WORKFLOW_HINTS:
        if re.search(pattern, desc_lower):
            issues.append(f"CSO Violation: {message}")

    # Check for first person
    for pattern, message in FIRST_PERSON:
        if re.search(pattern, description, re.IGNORECASE):
            issues.append(f"Style Issue: {message}")

    # Check for good patterns
    for pattern, message in GOOD_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            good.append(message)

    # Check length
    if len(description) > 1024:
        issues.append(f"Description is {len(description)} chars (max 1024)")
    elif len(description) > 500:
        warnings.append(f"Description is {len(description)} chars (recommend <500)")

    # Check if it's too vague
    if len(description) < 50:
        warnings.append("Description may be too short/vague")

    # Check if it includes trigger examples
    if not re.search(r"'[^']+'\s*,?\s*'[^']+'", description):
        warnings.append("Consider adding example trigger phrases in quotes")

    return {
        'issues': issues,
        'warnings': warnings,
        'good': good,
        'length': len(description),
    }


def analyze_skill_file(filepath: str) -> dict:
    """Analyze a SKILL.md file for CSO compliance."""
    path = Path(filepath)

    if not path.exists():
        return {'error': f"File not found: {filepath}"}

    content = path.read_text(encoding='utf-8')
    frontmatter = parse_skill_frontmatter(content)

    if not frontmatter:
        return {'error': "Could not parse YAML frontmatter"}

    name = frontmatter.get('name', '')
    description = frontmatter.get('description', '')

    if not description:
        return {'error': "No description field found"}

    analysis = analyze_description(description)
    analysis['name'] = name
    analysis['description'] = description

    return analysis


def print_analysis(analysis: dict):
    """Print analysis results."""
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return 1

    name = analysis.get('name', 'Unknown')
    print(f"\n=== CSO Analysis: {name} ===\n")

    # Good patterns found
    if analysis['good']:
        for item in analysis['good']:
            print(f"✅ {item}")

    # Issues
    if analysis['issues']:
        print()
        for issue in analysis['issues']:
            print(f"❌ {issue}")

    # Warnings
    if analysis['warnings']:
        print()
        for warning in analysis['warnings']:
            print(f"⚠️  {warning}")

    # Summary
    print(f"\n📊 Description length: {analysis['length']} characters")

    if not analysis['issues'] and not analysis['warnings']:
        print("\n✅ No CSO issues found!")
        return 0

    return 1 if analysis['issues'] else 0


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze-cso.py <path/to/SKILL.md>")
        print("\nAnalyzes skill description for CSO (Claude Search Optimization) issues.")
        sys.exit(1)

    filepath = sys.argv[1]
    analysis = analyze_skill_file(filepath)
    exit_code = print_analysis(analysis)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
