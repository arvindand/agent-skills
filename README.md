# Agent Skills

Portable skills for AI coding assistants. Primarily tested with Claude Code and leverages Claude Code-specific features (hooks, context forking), but core functionality works with any [Agent Skills](https://agentskills.io)-compatible tool including GitHub Copilot, OpenCode, and Cursor.

## Installation

### Option 1: Install as Plugin (Recommended - For Claude Code)

```bash
# Add the marketplace
/plugin marketplace add arvindand/agent-skills

# Install the plugin
/plugin install agent-skills@arvindand-skills
```

Or test locally:

```bash
claude --plugin-dir /path/to/agent-skills
```

### Option 2: Copy to Skills Directory

```bash
# Clone and copy skills
git clone https://github.com/arvindand/agent-skills.git
cp -r agent-skills/skills/* ~/.claude/skills/
```

Works with Claude Code, GitHub Copilot, OpenCode, Cursor, and VS Code with Copilot.

## Available Skills

| Skill | Description | Use For |
|-------|-------------|---------|
| [context7](skills/context7/) | Library documentation lookup via Context7 REST API | Getting up-to-date docs for React, Next.js, Prisma, etc. |
| [github-navigator](skills/github-navigator/) | GitHub operations via gh CLI with deep analysis mode | All GitHub operations + codebase analysis via cloning |
| [maven-tools](skills/maven-tools/) | JVM dependency intelligence via [Maven Tools MCP server](https://github.com/arvindand/maven-tools-mcp) | Version checks, upgrade planning, CVE scanning, license compliance |
| [skill-crafting](skills/skill-crafting/) | Create, fix, validate skills + generate from session history | Creating skills, fixing issues, CSO compliance, session-to-skill conversion |
| [ui-ux-design](skills/ui-ux-design/) | Create production-grade interfaces with strong UX foundations | Building functional, accessible, visually distinctive UI/UX |

## Output Styles

Customize Claude's response style via `/output-style`:

| Style | Description |
|-------|-------------|
| socratic | Teaches through questions. Backs off when you ask for direct answers. |
| speed-run | Max 3 sentences. Code first, explanations on request. |
| pair-programmer | Thinks aloud, invites interruption. Best for complex problems. |

## Usage

Once installed, skills activate automatically when relevant to your prompt:

```txt
You: "How do I use React hooks?"
→ context7 fetches up-to-date React hooks documentation

You: "Show me open issues in facebook/react"
→ github-navigator uses gh CLI to list issues

You: "Analyze the architecture of vercel/next.js"
→ github-navigator clones repo for deep codebase analysis

You: "Should I upgrade Spring Boot from 2.7 to 3.2?"
→ maven-tools analyzes versions, CVEs, breaking changes

You: "Build me a login form with dark mode"
→ ui-ux-design creates accessible component with proper states

You: "Create a skill from this session"
→ skill-crafting evaluates patterns and generates reusable skill
```

No manual invocation needed — the AI determines when each skill is relevant.

## Documentation

See [skill-crafting/REFERENCES.md](skills/skill-crafting/REFERENCES.md) for best practices and patterns.

### Cross-Platform Design

Skills use **progressive enhancement**:

- **Core fields** (`name`, `description`) work everywhere
- **Claude Code features** should be ignored by other platforms

### Claude Code Enhancements

When running in Claude Code, these skills leverage additional features:

| Feature | Skills | What It Does |
|---------|--------|--------------|
| Context forking | github-navigator | Runs in isolated subagent to avoid polluting main context |
| Stop hooks | skill-crafting, ui-ux-design | Verifies task completion before declaring done |
| PostToolUse hooks | github-navigator, skill-crafting | Validates output and formats results |
| Tool restrictions | All | Limits which tools each skill can use |

Other platforms get core functionality without these enhancements.

## Contributing

**Skills I'm looking to collect:**

- Frequent operations with zero context overhead
- CLI tools that can be discovered via `--help`
- Discovery patterns that teach AI dynamically

> Note: Would appreciate contributions or references to implementations for other useful skills, especially geared toward helping senior devs focused on backend, architecture, and DevOps.

## Why Skills over MCP?

I'm biased towards skills over MCP. Here's why.

### Skills are cheaper and at least as effective as MCP tools when done well

MCP loads all tool schemas into every conversation whether you use them or not. Ten tools? That's roughly 1,000 tokens added to every single request. Update: The tool search tool reduces this overhead but it still exists (See <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>)

Skills are free until you need them. When a skill triggers, you pay for ~100 words of metadata. That's it.

> Anthropic found that using code execution patterns (what skills enable) cut token usage from >150,000 to 2,000. That's a 98.7% reduction. <https://www.anthropic.com/engineering/code-execution-with-mcp>

### If there's a CLI, use a skill

AI models already know how to read `--help` output. You don't need to write MCP schemas for things like `gh`, `npm`, or `curl`.

Instead, teach the pattern:

- "Run `gh issue --help` to see what's available"
- "Check `npm --help` for commands"

The skill stays current as the CLI evolves. No maintenance needed.

> See <https://simonw.substack.com/p/openai-are-quietly-adopting-skills>

### When the line is blurry, optimize for cost

Sometimes both approaches work. When in doubt, ask: will I use this frequently? If yes, a skill costs you nothing when idle. An MCP costs you tokens on every request.

### When MCP makes sense

Use MCP when:

- Works and well maintained and doesn't contain a gazillion tools
- You need bidirectional communication (push updates, subscriptions)
- Carries complex state and sophisticated caching
- No CLI exists and you can't easily wrap the API

Skills and MCP can work together. You can write a skill that teaches the AI how to use your MCP servers effectively.

## License

MIT License — See individual skill LICENSE files for details.

**Author:** Arvind Menon

---
