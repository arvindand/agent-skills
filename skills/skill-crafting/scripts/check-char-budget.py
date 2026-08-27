#!/usr/bin/env python3
"""
Character Budget Checker for Agent Skills.

Two separate limits apply to the skill listing:

1. Per skill: `description` + `when_to_use` is capped at 1,536 characters
   (configurable via `skillListingMaxDescChars`). This is exact and always checked.

2. Across all skills: the listing budget scales at 1% of the model's context window,
   so it depends on the active model rather than being a fixed number. Override it with
   `skillListingBudgetFraction`, or pin a character count with
   `SLASH_COMMAND_TOOL_CHAR_BUDGET`. This script uses an advisory default; pass a
   second argument to check against your own.

When the listing overflows, Claude Code drops descriptions starting with the skills you
invoke least, so put the key use case first.
"""

import sys
from pathlib import Path

from frontmatter import parse_frontmatter

# Advisory only: the real budget is 1% of the active model's context window.
# Pass an explicit budget to check against a known SLASH_COMMAND_TOOL_CHAR_BUDGET.
DEFAULT_CHAR_BUDGET = 15000

# Exact, and independent of the aggregate budget.
PER_SKILL_DESC_CAP = 1536


def parse_skill_description(skill_path: Path) -> dict:
    """Extract name and description from a SKILL.md file."""
    skill_md = skill_path / 'SKILL.md' if skill_path.is_dir() else skill_path

    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding='utf-8')
        data, _ = parse_frontmatter(content)

        if not data:
            return None

        # when_to_use is appended to description in the listing and counts toward the cap
        description = data.get('description', '') or ''
        when_to_use = data.get('when_to_use', '') or ''
        listing_text = f"{description} {when_to_use}".strip() if when_to_use else description

        return {
            'name': data.get('name', skill_path.name),
            'description': listing_text,
            'path': str(skill_path),
        }
    except (ValueError, OSError):
        return None


def scan_skills_directory(skills_dir: str) -> list:
    """Scan a directory for skills and extract descriptions."""
    path = Path(skills_dir)
    skills = []

    if not path.exists():
        return skills

    # Check if it's a single skill
    if (path / 'SKILL.md').exists():
        skill = parse_skill_description(path)
        if skill:
            skills.append(skill)
        return skills

    # Scan for skills in subdirectories
    for item in path.iterdir():
        if item.is_dir():
            skill = parse_skill_description(item)
            if skill:
                skills.append(skill)

    return skills


def analyze_budget(skills: list, budget: int = DEFAULT_CHAR_BUDGET) -> dict:
    """Analyze character budget usage."""
    total_chars = 0
    breakdown = []

    for skill in sorted(skills, key=lambda x: len(x['description']), reverse=True):
        desc_len = len(skill['description'])
        total_chars += desc_len
        breakdown.append({
            'name': skill['name'],
            'chars': desc_len,
            'path': skill['path'],
            'over_cap': desc_len > PER_SKILL_DESC_CAP,
        })

    return {
        'total': total_chars,
        'budget': budget,
        'remaining': budget - total_chars,
        'percent_used': (total_chars / budget) * 100 if budget > 0 else 0,
        'over_budget': total_chars > budget,
        'breakdown': breakdown,
        'skill_count': len(skills),
        'over_cap': [b for b in breakdown if b['over_cap']],
    }


def print_analysis(analysis: dict):
    """Print budget analysis results."""
    print("\n=== Character Budget Analysis ===\n")

    # Per-skill cap (exact)
    if analysis['over_cap']:
        print(f"❌ Over the {PER_SKILL_DESC_CAP:,}-char per-skill cap:")
        for item in analysis['over_cap']:
            print(f"   {item['name']}: {item['chars']:,} chars — text past the cap is truncated")
    else:
        print(f"✅ All descriptions within the {PER_SKILL_DESC_CAP:,}-char per-skill cap")

    # Summary
    print()
    status = "❌ OVER BUDGET" if analysis['over_budget'] else "✅ Within budget"
    print(f"Listing total: {status} (advisory — real budget is 1% of the model's context window)")
    print(f"Skills found: {analysis['skill_count']}")
    print(f"Total characters: {analysis['total']:,} / {analysis['budget']:,}")
    print(f"Remaining: {analysis['remaining']:,} characters")
    print(f"Usage: {analysis['percent_used']:.1f}%")

    # Warning thresholds
    if analysis['percent_used'] > 80:
        print("\n⚠️  Warning: Above 80% usage - consider shortening descriptions")

    # Breakdown by skill
    print("\n--- Breakdown by Skill ---\n")
    for item in analysis['breakdown']:
        bar_len = min(50, int(item['chars'] / 20))
        bar = '█' * bar_len
        flag = ' ⚠️' if item['over_cap'] else ''
        print(f"{item['name']:30} {item['chars']:5} chars  {bar}{flag}")

    # Recommendations
    if analysis['over_budget']:
        print("\n🔧 Recommendations:")
        print("   1. Shorten descriptions - focus on triggers, not workflow")
        print("   2. Remove less-used skills")
        print("   3. Raise skillListingBudgetFraction, or set SLASH_COMMAND_TOOL_CHAR_BUDGET")
        print("      to a fixed character count, for more headroom")
        top_skill = analysis['breakdown'][0]
        print(f"   4. Biggest skill: {top_skill['name']} ({top_skill['chars']} chars)")

    return 0 if not (analysis['over_budget'] or analysis['over_cap']) else 1


def main():
    if len(sys.argv) < 2:
        print("Usage: check-char-budget.py <path/to/skills/>")
        print("\nChecks the exact 1,536-char per-skill cap, plus an advisory listing total.")
        print("Pass a budget as the second argument to check a known character budget.")
        print("\nExamples:")
        print("  check-char-budget.py ~/.claude/skills/")
        print("  check-char-budget.py ./")
        sys.exit(1)

    skills_dir = sys.argv[1]
    budget = DEFAULT_CHAR_BUDGET

    # Optional: custom budget from env or arg
    if len(sys.argv) > 2:
        try:
            budget = int(sys.argv[2])
        except ValueError:
            pass

    skills = scan_skills_directory(skills_dir)

    if not skills:
        print(f"No skills found in: {skills_dir}")
        sys.exit(1)

    analysis = analyze_budget(skills, budget)
    exit_code = print_analysis(analysis)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
