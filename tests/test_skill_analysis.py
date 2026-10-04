"""Run with: python3 -m unittest discover -s tests -v (standard library only)."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / 'skill-crafting' / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from frontmatter import parse_frontmatter, parse_simple_yaml


def load_script(filename):
    spec = importlib.util.spec_from_file_location(filename, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


budget = load_script('check-char-budget.py')
compatibility = load_script('analyze-compatibility.py')
all_checks = load_script('analyze-all.py')
tokens = load_script('analyze-tokens.py')


class FrontmatterTests(unittest.TestCase):
    def test_literal_description_preserves_newlines_and_next_field(self):
        data, body = parse_frontmatter(
            '---\nname: example\ndescription: |\n'
            '    Use when checking a skill.\n    Include its metadata.\n'
            'license: MIT\n---\n\n# Example\n')
        self.assertEqual(data['description'], 'Use when checking a skill.\nInclude its metadata.\n')
        self.assertEqual(data['license'], 'MIT')
        self.assertEqual(body, '# Example')

    def test_last_field_block_description_is_not_dropped(self):
        data, _ = parse_frontmatter('---\nname: example\ndescription: |\n  Last field.\n---\n')
        self.assertEqual(data['description'], 'Last field.\n')

    def test_folded_description_preserves_paragraphs_and_indented_lines(self):
        data = parse_simple_yaml('description: >-\n  First line\n  second line\n\n'
                                 '  Next paragraph\n    indented line\n  Final line\n')
        self.assertEqual(data['description'],
                         'First line second line\nNext paragraph\n  indented line\nFinal line')

    def test_block_chomping(self):
        for style in ('|', '>'):
            for indicator, expected in (('', 'text\n'), ('-', 'text'), ('+', 'text\n\n\n')):
                with self.subTest(style=style, indicator=indicator):
                    data = parse_simple_yaml(f'description: {style}{indicator}\n  text\n\n\nlicense: MIT\n')
                    self.assertEqual(data['description'], expected)

    def test_empty_and_leading_blank_blocks(self):
        self.assertEqual(parse_simple_yaml('description: |\n')['description'], '')
        self.assertEqual(parse_simple_yaml('description: |+\n\n')['description'], '\n')
        self.assertEqual(parse_simple_yaml('description: >\n\n  first\n  second\n')['description'],
                         '\nfirst second\n')

    def test_block_hashes_are_content(self):
        self.assertEqual(parse_simple_yaml('description: |- # style comment\n  # heading\n  text\n'),
                         {'description': '# heading\ntext'})

    def test_plain_multiline_description_folds(self):
        data = parse_simple_yaml('description: Use when checking skills\n  and inspecting metadata.\n\n'
                                 '  Then ask about triggers.\nlicense: MIT # license comment\n')
        self.assertEqual(data['description'],
                         'Use when checking skills and inspecting metadata.\nThen ask about triggers.')
        self.assertEqual(data['license'], 'MIT')

    def test_quotes_and_comments(self):
        data = parse_simple_yaml('description: "Use \\"quoted\\" paths \\u00e9 and \\n lines # text" # comment\n'
                                 "license: 'It''s literal \\n # text' # comment\n")
        self.assertEqual(data['description'], 'Use "quoted" paths é and \n lines # text')
        self.assertEqual(data['license'], "It's literal \\n # text")

    def test_nested_metadata_and_hook_sequences(self):
        data = parse_simple_yaml('metadata:\n  author: "Arvind"\n  details:\n    topic: skills\n'
                                 'hooks:\n  Stop:\n    - hooks:\n        - type: prompt\n'
                                 '          prompt: "Respond {\\"ok\\": true}"\n'
                                 '    - matcher: Bash\n      hooks:\n        - type: command\n'
                                 '          command: "python3 check.py"\n          timeout: 500\n'
                                 'allowed-tools:\n  - Read\n  - Bash(python3:*)\n')
        self.assertEqual(data['metadata'], {'author': 'Arvind', 'details': {'topic': 'skills'}})
        self.assertEqual(data['hooks']['Stop'][0]['hooks'][0],
                         {'type': 'prompt', 'prompt': 'Respond {"ok": true}'})
        self.assertEqual(data['hooks']['Stop'][1]['hooks'][0]['timeout'], '500')
        self.assertEqual(data['allowed-tools'], ['Read', 'Bash(python3:*)'])

    def test_delimiters_are_complete_lines(self):
        data, body = parse_frontmatter('---\nname: example\ndescription: "Use --- as text"\n---\nBody')
        self.assertEqual(data['description'], 'Use --- as text')
        self.assertEqual(body, 'Body')
        data, _ = parse_frontmatter('---\ndescription: |-\n  ---\n  Still content\n---\nBody')
        self.assertEqual(data['description'], '---\nStill content')

    def test_missing_and_unclosed_frontmatter(self):
        self.assertEqual(parse_frontmatter('# Body'), ({}, '# Body'))
        with self.assertRaisesRegex(ValueError, 'Missing closing'):
            parse_frontmatter('---\nname: example\n')

    def test_rejected_syntax_is_explicit(self):
        cases = ['description: [one, two]', 'description: &anchor text',
                 'description: *anchor', 'description: !!str text',
                 'description: |2\n  text', 'description: "first\n  second"',
                 'description: "bad\\q"', 'name: first\nname: second',
                 'metadata:\n\tauthor: example', 'description: plain: mapping',
                 'description: |\n    first\n  inconsistent',
                 'description: |\n    \n  invalid blank indentation',
                 'description: plain # comment\n  invalid continuation',
                 'description: "bad\\uD800"',
                 'metadata: {author: example}', '- a root sequence']
        for content in cases:
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse_simple_yaml(content)

    def test_structured_description_fails_instead_of_crashing_analyzers(self):
        with self.assertRaisesRegex(ValueError, 'description must be a string'):
            parse_frontmatter('---\nname: example\ndescription:\n  - text\n---\n')

    def test_bundled_skills_and_nested_hooks(self):
        paths = list((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(paths), 5)
        for path in paths:
            with self.subTest(skill=path.parent.name):
                data, body = parse_frontmatter(path.read_text())
                self.assertEqual(data['name'], path.parent.name)
                self.assertIn('Use when', data['description'])
                self.assertTrue(body.startswith('# '))
                if 'hooks' in data:
                    hook = data['hooks']['Stop'][0]['hooks'][0]
                    self.assertEqual(hook['type'], 'prompt')
                    self.assertIn('{"ok": true}', hook['prompt'])


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / 'LICENSE').write_text('MIT')

    def write_skill(self, fields):
        (self.path / 'SKILL.md').write_text(f'---\nname: example\n{fields}\n---\n# Example\n')

    def run_script(self, filename, path=None):
        return subprocess.run([sys.executable, str(SCRIPTS / filename), str(path or self.path)],
                              capture_output=True, text=True)

    def test_block_description_counts_toward_budget(self):
        self.write_skill('description: |-\n  ' + 'x' * (budget.PER_SKILL_DESC_CAP + 1))
        skill = budget.parse_skill_description(self.path)
        report = budget.analyze_budget([skill])
        self.assertEqual(report['total'], budget.PER_SKILL_DESC_CAP + 1)
        self.assertEqual(len(report['over_cap']), 1)
        self.assertEqual(self.run_script('check-char-budget.py').returncode, 1)

    def test_unparsed_skill_prevents_false_budget_success(self):
        good = self.path / 'good'
        good.mkdir()
        (good / 'SKILL.md').write_text('---\nname: good\ndescription: Valid text\n---\n')
        bad = self.path / 'bad'
        bad.mkdir()
        (bad / 'SKILL.md').write_text('---\nname: bad\ndescription: [invalid]\n---\n')
        result = self.run_script('check-char-budget.py')
        self.assertEqual(result.returncode, 1)
        self.assertIn('bad/SKILL.md', result.stdout)
        self.assertIn('not calculated', result.stdout)
        self.assertNotIn('All descriptions within', result.stdout)
        with self.assertRaisesRegex(ValueError, 'unparsed skills'):
            budget.analyze_budget(budget.scan_skills_directory(str(self.path)))

    def test_unknown_fields_remain_advisory_but_never_claim_compatibility(self):
        self.write_skill('description: Use when checking skills and validating skill metadata.\nfuture-field: value')
        self.assertFalse(compatibility.analyze_compatibility({'name': 'example', 'future-field': 'value'})
                         ['is_cross_platform'])
        for filename in ('analyze-compatibility.py', 'analyze-all.py'):
            with self.subTest(filename=filename):
                result = self.run_script(filename)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('unverified', result.stdout)
                self.assertIn('future-field', result.stdout)
                self.assertNotIn('Fully cross-platform', result.stdout)
                self.assertNotIn('No issues found', result.stdout)
                self.assertNotIn('Claude Code          ✅ Full', result.stdout)

    def test_standard_and_extension_classification(self):
        self.assertTrue(compatibility.analyze_compatibility({'name': 'example'})['is_cross_platform'])
        self.assertFalse(compatibility.analyze_compatibility({'name': 'example', 'hooks': {}})
                         ['is_cross_platform'])

    def test_analyzers_report_parse_errors_without_tracebacks(self):
        for fields in ('description: [one, two]', 'description:\n  - invalid type'):
            self.write_skill(fields)
            for filename in ('analyze-all.py', 'analyze-compatibility.py', 'analyze-cso.py',
                             'analyze-structure.py', 'analyze-triggers.py', 'analyze-tokens.py',
                             'check-char-budget.py'):
                with self.subTest(filename=filename, fields=fields):
                    result = self.run_script(filename)
                    self.assertEqual(result.returncode, 1)
                    self.assertTrue(result.stdout)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertNotIn('Description is efficient', result.stdout)

    def test_token_analyzer_counts_description_with_inline_delimiter(self):
        description = 'Use when converting --- separated notes'
        self.write_skill(f'description: "{description}"')
        result = tokens.analyze_skill_tokens(self.path)
        self.assertEqual(result['description']['chars'], len(description))
        self.assertEqual(result['description']['words'], 6)
        self.assertEqual(result['description']['tokens'], 7)
        self.assertEqual(result['body']['chars'], len('# Example'))
        report = self.run_script('analyze-tokens.py')
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        self.assertIn('6 words | ~7 tokens', report.stdout)
        self.assertNotIn('efficient (~0 tokens)', report.stdout)

    def test_token_analyzer_rejects_missing_or_unclosed_headers(self):
        for content in ('# Missing header', '---\nname: example\ndescription: text\n'):
            with self.subTest(content=content):
                (self.path / 'SKILL.md').write_text(content)
                result = self.run_script('analyze-tokens.py')
                self.assertEqual(result.returncode, 1)
                self.assertIn('Error:', result.stdout)
                self.assertNotIn('Traceback', result.stderr)
                self.assertNotIn('Description is efficient', result.stdout)

    def test_all_checker_rules_come_from_bundled_modules(self):
        self.assertEqual(all_checks.WORKFLOW_HINTS, load_script('analyze-cso.py').WORKFLOW_HINTS)
        # A missing rules module must fail visibly instead of switching rules.
        (self.path / 'analyze-all.py').write_text((SCRIPTS / 'analyze-all.py').read_text())
        (self.path / 'frontmatter.py').write_text((SCRIPTS / 'frontmatter.py').read_text())
        result = subprocess.run([sys.executable, str(self.path / 'analyze-all.py'), str(self.path)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('analyze-cso.py', result.stderr)
        self.assertNotIn('Skill Analysis', result.stdout)


if __name__ == '__main__':
    unittest.main()
