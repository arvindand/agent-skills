#!/usr/bin/env python3
"""Dependency-free parser for the YAML subset used in skill frontmatter.

Supports string scalars (plain, single/double quoted, literal and folded), block
mappings and block sequences, including nested metadata and hooks. Scalar values
remain strings, as in the original analyzer. This is not a general YAML loader:
flow collections, anchors, aliases, tags, multiline quotes and explicit block
indentation indicators raise ValueError instead of producing incomplete data.
"""

import re
from typing import Any, Dict, Optional


def parse_frontmatter(content: str) -> tuple:
    """Return (frontmatter, body), or ({}, content) when no header is present.

    Delimiters must occupy their own, unindented lines. An opened but unclosed
    header, unsupported syntax, and non-string name/description fields are errors.
    """
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != '---':
        return {}, content
    for end in range(1, len(lines)):
        if lines[end].rstrip() == '---':
            frontmatter = parse_simple_yaml(''.join(lines[1:end]))
            for field in ('name', 'description', 'when_to_use'):
                if field in frontmatter and not isinstance(frontmatter[field], str):
                    raise ValueError(f"{field} must be a string scalar")
            return frontmatter, ''.join(lines[end + 1:]).strip()
    raise ValueError("Missing closing --- for frontmatter")


def parse_simple_yaml(yaml_text: str) -> Dict[str, Any]:
    """Parse the supported YAML subset; reject syntax we cannot interpret."""
    return _Parser(yaml_text).parse()


class _Parser:
    def __init__(self, text: str):
        self.lines = text.splitlines(keepends=True)
        self.index = 0

    def error(self, message: str):
        raise ValueError(f"Line {self.index + 1}: {message}")

    def indent(self, line: str) -> int:
        prefix = re.match(r'^[ \t]*', line).group()
        if '\t' in prefix:
            self.error("Use spaces for YAML indentation, not tabs")
        return len(prefix)

    def skip_comments(self):
        while self.index < len(self.lines):
            text = self.lines[self.index].strip()
            if text and not text.startswith('#'):
                break
            self.index += 1

    def parse(self) -> dict:
        self.skip_comments()
        if self.index == len(self.lines):
            return {}
        if self.indent(self.lines[self.index]) != 0:
            self.error("Frontmatter must start with an unindented mapping")
        result = self.mapping(0)
        self.skip_comments()
        if self.index != len(self.lines):
            self.error("Unexpected YAML content")
        return result

    def entry(self, text: str) -> tuple:
        match = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*):(?:[ \t]+(.*)|$)', text)
        if not match:
            self.error("Expected a simple key: value mapping (complex keys are unsupported)")
        return match.group(1), match.group(2) or ''

    def mapping(self, indent: int, first: Optional[str] = None) -> dict:
        result = {}
        while True:
            if first is not None:
                text, first = first, None
            else:
                self.skip_comments()
                if self.index == len(self.lines):
                    break
                line = self.lines[self.index].rstrip('\r\n')
                level = self.indent(line)
                if level < indent:
                    break
                if level != indent:
                    self.error("Unexpected indentation in mapping")
                text = line[indent:]
                self.index += 1
            key, raw = self.entry(text)
            if key in result:
                self.error(f"Duplicate key: {key}")
            result[key] = self.value(raw, indent)
        return result

    def sequence(self, indent: int) -> list:
        result = []
        while True:
            self.skip_comments()
            if self.index == len(self.lines):
                break
            line = self.lines[self.index].rstrip('\r\n')
            level = self.indent(line)
            if level < indent:
                break
            if level != indent or not re.match(r'^-(?:\s|$)', line[indent:]):
                self.error("Expected a block sequence item at the same indentation")
            item = line[indent + 1:].lstrip()
            # In '- key: value', mapping keys start after the '- ' prefix.
            key_indent = len(line) - len(item) if item else indent + 2
            self.index += 1
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*:(?:\s|$)', item):
                result.append(self.mapping(key_indent, first=item))
            else:
                result.append(self.value(item, indent))
        return result

    def value(self, raw: str, parent_indent: int) -> Any:
        raw = raw.strip()
        if not raw or raw.startswith('#'):
            self.skip_comments()
            if self.index < len(self.lines):
                line = self.lines[self.index]
                indent = self.indent(line)
                if indent > parent_indent:
                    if re.match(r'^-(?:\s|$)', line[indent:]):
                        return self.sequence(indent)
                    return self.mapping(indent)
            return ''
        if raw.startswith(('|', '>')):
            return self.block(raw, parent_indent)
        if raw.startswith(('"', "'")):
            return self.quoted(raw)
        text = self.plain(raw)
        # Plain multiline scalars fold line breaks into spaces; blank lines
        # between text lines become newlines. Comments terminate continuation.
        pending = 0
        has_comment = bool(re.search(r'\s+#', raw))
        while self.index < len(self.lines) and not has_comment:
            line = self.lines[self.index].rstrip('\r\n')
            if not line.strip():
                pending += 1
                self.index += 1
                continue
            if line.lstrip().startswith('#'):
                break
            if self.indent(line) <= parent_indent:
                break
            text += ('\n' * pending if pending else ' ') + self.plain(line.strip())
            has_comment = bool(re.search(r'\s+#', line.strip()))
            pending = 0
            self.index += 1
        return text

    def plain(self, text: str) -> str:
        # A hash begins a comment only when preceded by whitespace.
        text = re.split(r'\s+#', text, maxsplit=1)[0].rstrip()
        if (text.startswith(('[', ']', '{', '}', '&', '*', '!', '%', '@', '`'))
                or re.match(r'^[-?:](?:\s|$)', text)):
            self.error("Unsupported YAML syntax; use a quoted scalar or block collection")
        if re.search(r':(?:\s|$)', text):
            self.error("Colon followed by whitespace in a plain scalar; quote the value")
        return text

    def quoted(self, raw: str) -> str:
        quote = raw[0]
        result = []
        index = 1
        escapes = {'0': '\0', 'a': '\a', 'b': '\b', 't': '\t', 'n': '\n',
                   'v': '\v', 'f': '\f', 'r': '\r', 'e': '\x1b', ' ': ' ',
                   '"': '"', '/': '/', '\\': '\\', 'N': '\x85',
                   '_': '\xa0', 'L': '\u2028', 'P': '\u2029'}
        while index < len(raw):
            char = raw[index]
            if char == quote:
                if quote == "'" and raw[index:index + 2] == "''":
                    result.append("'")
                    index += 2
                    continue
                tail = raw[index + 1:]
                if tail.strip() and not re.match(r'^\s+#', tail):
                    self.error("Unexpected content after quoted scalar")
                return ''.join(result)
            if char == '\\' and quote == '"':
                index += 1
                if index == len(raw):
                    self.error("Multiline quoted scalars are unsupported; use | or >")
                code = raw[index]
                if code in escapes:
                    result.append(escapes[code])
                elif code in ('x', 'u', 'U'):
                    size = {'x': 2, 'u': 4, 'U': 8}[code]
                    digits = raw[index + 1:index + size + 1]
                    if len(digits) != size or not re.fullmatch(r'[0-9a-fA-F]+', digits):
                        self.error("Invalid Unicode escape in quoted scalar")
                    try:
                        point = int(digits, 16)
                        if 0xD800 <= point <= 0xDFFF:
                            self.error("Unicode surrogate code points are unsupported")
                        result.append(chr(point))
                    except ValueError:
                        self.error("Invalid Unicode code point")
                    index += size
                else:
                    self.error(f"Unsupported quoted escape: \\{code}")
            else:
                result.append(char)
            index += 1
        self.error("Unclosed quote (multiline quoted scalars are unsupported; use | or >)")

    def block(self, header: str, parent_indent: int) -> str:
        header = re.split(r'\s+#', header, maxsplit=1)[0].rstrip()
        if not re.fullmatch(r'[|>][+-]?', header):
            self.error("Unsupported block header; use |, >, |-, >-, |+ or >+")
        parts = []
        block_indent = None
        leading_blank_indent = 0
        while self.index < len(self.lines):
            line = self.lines[self.index].rstrip('\r\n')
            if line.strip():
                indent = self.indent(line)
                if indent <= parent_indent:
                    break
                if block_indent is None:
                    block_indent = indent
                    if leading_blank_indent > block_indent:
                        self.error("Leading blank line exceeds block scalar indentation")
                if indent < block_indent:
                    self.error("Inconsistent block scalar indentation")
                parts.append(line[block_indent:])
            else:
                if block_indent is None:
                    leading_blank_indent = max(leading_blank_indent, self.indent(line))
                parts.append('')
            self.index += 1
        # The last physical line may end at EOF without a line break.
        ending = '\n' if parts and self.lines[self.index - 1].endswith(('\n', '\r')) else ''
        if header[0] == '|':
            value = '\n'.join(parts) + ending
        else:
            value = ''
            for index, part in enumerate(parts):
                value += part
                if index + 1 < len(parts):
                    following = parts[index + 1]
                    if part and following and not part.startswith(' ') and not following.startswith(' '):
                        value += ' '
                    elif (part and not following and not part.startswith(' ')
                          and any(parts[index + 2:])
                          and not next(item for item in parts[index + 2:] if item).startswith(' ')):
                        # The blank line itself supplies the paragraph break.
                        pass
                    else:
                        value += '\n'
            value += ending
        if header.endswith('-'):
            return value.rstrip('\n')
        if header.endswith('+'):
            return value
        return value.rstrip('\n') + ('\n' if value.strip('\n') and value.endswith('\n') else '')


def get_frontmatter_field(content: str, field: str) -> Optional[str]:
    """Get a specific field from frontmatter."""
    frontmatter, _ = parse_frontmatter(content)
    return frontmatter.get(field)
