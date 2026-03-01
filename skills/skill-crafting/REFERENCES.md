# References

Best practices, patterns, and links for building skills.

## Table of Contents

- [Discovery Over Documentation](#discovery-over-documentation)
- [Progressive Disclosure](#progressive-disclosure)
- [Description Optimization](#description-optimization)
- [Token Efficiency](#token-efficiency)
- [Naming Conventions](#naming-conventions)
- [Content Patterns](#content-patterns)
- [Testing Patterns](#testing-patterns)
- [Anti-Patterns](#anti-patterns)
- [Example Transformations](#example-transformations)
- [Session-to-Skill Extraction](#session-to-skill-extraction)
- [Links](#links)

---

## Discovery Over Documentation

Don't hardcode 500 lines of examples. Teach the pattern instead.

**Bad:**

```markdown
gh issue list --repo owner/repo
gh issue view 123 --repo owner/repo
gh pr list --repo owner/repo
# ... 50 more examples
```

**Good:**

```markdown
1. Identify command domain (files/issues/PRs)
2. Run `gh <command> --help` to discover usage
3. Apply to request
```

This stays current as commands change. Zero maintenance.

---

## Progressive Disclosure

Keep SKILL.md under 500 lines. Move details to separate files.

```
skill/
├── SKILL.md              # Overview (<500 lines)
├── references/
│   ├── api.md            # Detailed API docs
│   └── examples.md       # Usage examples
└── scripts/
    └── helper.py         # Executes without loading into context
```

**Loading levels:**

1. **Metadata** — Always in context (~100 words)
2. **SKILL.md** — Loaded when skill triggers
3. **References** — Loaded only when needed

**Keep references one level deep:**

- ✅ SKILL.md → reference.md
- ❌ SKILL.md → advanced.md → details.md

---

## Execution Context

By default, skills run in the main conversation context. Use `context: fork` to run a skill in an isolated subagent:

```yaml
---
name: deep-analysis
description: "Perform deep code analysis..."
context: fork
---
```

**When to use `context: fork`:**

| Use fork | Stay in main context |
|----------|---------------------|
| Multi-step operations that would clutter conversation | Simple guidance or standards |
| Long-running analysis tasks | Quick lookups or checks |
| When you need separate conversation history | When skill needs conversation context |
| Exploratory work with many tool calls | Direct responses to user |

**Trade-offs:**

- Fork: Clean separation, own history, but loses main conversation context
- Main: Has full conversation context, but all tool calls visible to user

**Note:** Built-in agents (Explore, Plan, general-purpose) do not have access to skills. Only custom subagents in `.claude/agents/` with explicit `skills` field can use skills.

---

## Description Optimization

The description field is critical for skill discovery.

### Structure

```yaml
description: "[What it does]. Use when [triggers]. Use when [more triggers]."
```

### Rules

| Rule | Why |
|------|-----|
| Include "Use when..." clauses | Focuses on triggers |
| Include exact user phrases | Matches natural language |
| Write in third person | Injected into system prompt |
| Never summarize workflow | Causes Claude to skip reading skill |
| Keep under 500 chars | Loaded into every conversation |

A short "what it does" prefix before the trigger clauses is fine when it improves clarity.

### Good Examples

```yaml
# GitHub operations
description: "GitHub operations via gh CLI. Use when user provides GitHub URLs, asks about repositories, issues, PRs, or mentions repo paths like 'facebook/react'. Use instead of webfetch for github.com links."

# Documentation lookup
description: "Fetch library documentation via Context7 API. Use when user asks about React, Next.js, Prisma, or any npm/PyPI package. Use when user says 'how do I use X library' or needs official docs."

# UI generation
description: "Create production-grade frontend interfaces. Use when building web components, pages, dashboards, forms, landing pages. Use when user says 'build a form', 'create a dashboard', 'design a component'."
```

### Bad Examples

```yaml
# Too vague
description: "Helps with GitHub"

# First person
description: "I can help you with GitHub operations"

# Summarizes workflow (DANGEROUS)
description: "Runs gh commands to list issues, view PRs, and fetch files"

# Too abstract
description: "For async testing"
```

### Why No Workflow Summary?

Testing revealed that when descriptions summarize workflow, Claude may follow the description instead of reading the full skill body.

Example: A description saying "dispatches subagent per task with code review" caused Claude to do ONE review. The skill's flowchart clearly showed TWO reviews (spec compliance + code quality).

When changed to "Use when executing implementation plans with independent tasks" (no workflow), Claude correctly read the flowchart and followed both reviews.

**The trap:** Descriptions that summarize workflow create a shortcut Claude will take.

---

## Token Efficiency

Context window is shared. Every token competes.

### Target Word Counts

| Skill Type | Target |
|------------|--------|
| Frequently-loaded | <200 words |
| Standard skills | <500 words |
| Reference files | Unlimited (loaded as needed) |

### Techniques

**Move details to tool help:**

```markdown
# Bad: Document all flags
search supports --text, --both, --after DATE, --before DATE, --limit N

# Good: Reference --help
search supports multiple modes. Run --help for details.
```

**Use cross-references:**

```markdown
# Bad: Repeat workflow details
[20 lines of repeated instructions]

# Good: Reference other skill
See [other-skill](../other-skill/SKILL.md) for workflow.
```

**Compress examples:**

```markdown
# Bad: Verbose (42 words)
User: "How did we handle authentication errors in React Router before?"
Assistant: I'll search past conversations for React Router authentication patterns.
[Dispatch subagent with search query: "React Router authentication error handling 401"]

# Good: Minimal (20 words)
User: "How did we handle auth errors in React Router?"
Assistant: Searching... [Dispatch subagent → synthesis]
```

---

## Naming Conventions

### Use Verb-Based Names (Gerunds)

Active verbs describe what you're doing:

| Good | Bad |
|------|-----|
| `skill-crafting` | `skill-manager` |
| `processing-pdfs` | `pdf-helper` |
| `navigating-github` | `github-tools` |
| `debugging-code` | `debugger` |

### Format Rules

- Lowercase only
- Hyphens between words
- Max 64 characters
- No underscores, spaces, or special characters

### Avoid Vague Names

- ❌ `helper`, `utils`, `tools`
- ❌ `misc`, `general`, `common`
- ✅ Specific action: `generating-reports`, `validating-forms`

---

## Content Patterns

### Workflow with Checklist

For complex multi-step tasks:

```markdown
## Workflow

Copy and track:

- [ ] Step 1: Assess context
- [ ] Step 2: Gather requirements
- [ ] Step 3: Generate output
- [ ] Step 4: Verify

**Step 1: Assess context**
[Details]

**Step 2: Gather requirements**
[Details]
```

### Feedback Loop

Pattern: Execute → Validate → Fix → Repeat

```markdown
## Validation Loop

1. Execute operation
2. Run: `python scripts/validate.py`
3. If fails:
   - Review error message
   - Fix issues
   - Validate again
4. Only proceed when passes
```

### Recovery Table

For common failure modes:

```markdown
## Recovery

| Issue | Action |
|-------|--------|
| Skill didn't trigger | Check description includes user's words |
| Command failed | Run `command --help`, update syntax |
| Wrong output | Verify requirements, adjust approach |
```

### Template Pattern

**Strict (low freedom):**

```markdown
ALWAYS use this exact structure:
[template - no flexibility]
```

**Flexible (high freedom):**

```markdown
Default format (adapt as needed):
[template with notes on customization]
```

---

## Testing Patterns

### Pressure Scenario Template

```markdown
IMPORTANT: This is a real scenario. Choose and act.

[Context with multiple pressures: time + sunk cost + exhaustion]

Options:
A) Follow the skill strictly
B) Take a shortcut
C) Compromise

Choose A, B, or C.
```

### Pressure Types

| Pressure | Example |
|----------|---------|
| Time | "Deploy window closes in 5 minutes" |
| Sunk cost | "You spent 3 hours on this already" |
| Authority | "Senior engineer says skip it" |
| Exhaustion | "It's 6pm, dinner at 6:30pm" |
| Social | "You'll look dogmatic if you insist" |

**Best tests combine 3+ pressures.**

### What to Capture

When testing WITHOUT the skill:

- Exact choices agent makes
- Verbatim rationalizations
- Which pressures trigger violations

Use these to write explicit counters in the skill.

---

## Anti-Patterns

### Don't

| Anti-Pattern | Why Bad |
|--------------|---------|
| Explain common knowledge | Wastes tokens |
| Inconsistent terms | Confuses AI |
| Summarize workflow in description | Causes skill body to be skipped |
| Many options without default | Increases decision fatigue |
| Windows paths (`scripts\file.py`) | Breaks cross-platform |
| README, CHANGELOG files | Unnecessary overhead |
| "Why This Works" sections | Wastes tokens |
| Time-sensitive info | Will become stale |

### Do

| Pattern | Why Good |
|---------|----------|
| Trust AI's knowledge | Saves tokens |
| One term consistently | Clarity |
| Triggers only in description | Proper discovery |
| Default with escape hatch | Clear guidance |
| Forward slashes always | Cross-platform |
| Only essential files | Clean structure |

---

## Example Transformations

### github-navigator

**Before:**

- 450 lines of Python wrapper
- Hardcoded examples for every command
- Only covered file operations

**After:**

- Pure gh CLI usage
- Discovery pattern via `--help`
- Covers ALL GitHub operations
- Self-updating as CLI evolves
- Zero maintenance

**Transformation:**

```markdown
# Instead of hardcoding:
gh issue list --repo owner/repo
gh pr list --state merged
# [100+ examples]

# Teach discovery:
1. Identify: gh issue
2. Discover: gh issue --help
3. Apply to request

Works for any gh command, now and future.
```

### skill-manager → skill-crafting

**Before:**

- Noun-based name
- Focused on structure
- No testing methodology

**After:**

- Verb-based name (skill-crafting)
- TDD methodology for skills
- CSO section for discovery
- Pressure testing concepts
- Self-healing patterns

---

## Claude Code Hooks

Hooks enable skills to respond to events during execution. They're Claude Code-specific but gracefully ignored by other platforms.

**Key insight:** Hook stdout is injected into Claude's context. This enables skill chaining and guidance patterns.

### Available Hook Types for Skills

Skills only support these hook types in their frontmatter:

| Hook | Trigger | Use Case |
|------|---------|----------|
| `PreToolUse` | Before tool executes | Validate inputs, block dangerous operations |
| `PostToolUse` | After tool completes | Validate output, inject guidance, trigger skill chaining |
| `Stop` | Skill/agent stops | Cleanup, logging |

**Note:** `UserPromptSubmit` and other global hooks are NOT supported in Skill frontmatter. Use global settings (`~/.claude/settings.json`) for those.

### Hook Configuration

```yaml
---
name: my-skill
description: "..."
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 scripts/validate-input.py"
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 scripts/post-process.py"
---
```

### Hook Environment Variables

Hooks receive context via environment variables:

| Variable | Content |
|----------|---------|
| `TOOL_NAME` | Name of the tool being used |
| `TOOL_INPUT` | JSON input to the tool |
| `TOOL_OUTPUT` | Tool output (PostToolUse only) |
| `TOOL_EXIT_CODE` | Exit code (PostToolUse only) |

### Hook Output and Context Injection

**This is powerful:** Anything printed to stdout is added to Claude's context.

```python
# This text becomes visible to Claude
print("[my-skill] Analysis complete. Found 3 issues.")
print("[my-skill] Recommend: Run tests before committing.")
```

Two output methods:

1. **Plain text stdout** (simple):

   ```python
   print("This text is added to Claude's context")
   ```

2. **JSON with additionalContext** (structured):

   ```python
   import json
   print(json.dumps({
       "decision": "continue",  # or "block"
       "additionalContext": "Context for Claude to see"
   }))
   ```

### Skill Chaining via Hooks

Since skills cannot programmatically invoke other skills, use **guidance-based chaining**: hooks output suggestions that Claude sees and acts on.

**Pattern:**

```python
#!/usr/bin/env python3
# PostToolUse hook that chains to another skill
import os

output = os.environ.get('TOOL_OUTPUT', '')

if 'migration' in output.lower():
    print("\n[maven-tools] Migration detected.")
    print("[maven-tools] → Use context7 skill to fetch migration documentation.")
    print("[maven-tools] Example: 'Get Spring Boot 2.7 to 3.0 migration guide'")
```

**How it works:**

1. Skill A completes its work
2. PostToolUse hook detects a pattern (e.g., "migration needed")
3. Hook prints guidance suggesting Skill B
4. Claude sees the guidance and invokes Skill B

**Real example:** maven-tools → context7

```
User: "Should I upgrade Spring Boot 2.7 to 3.2?"
→ maven-tools: Analyzes versions, finds breaking changes
→ Hook outputs: "[maven-tools] Major upgrade. Use context7 for migration docs."
→ Claude: Invokes context7 to fetch migration guide
```

This is the same pattern used by security tools like [Lasso Defender](https://www.lasso.security/blog/the-hidden-backdoor-in-claude-coding-assistant) - inject warnings/guidance into context that Claude responds to.

### Decision Blocking

PreToolUse hooks can block operations:

```python
import sys
import json

# Block the operation
print(json.dumps({
    "decision": "block",
    "reason": "Operation not allowed: contains sensitive path"
}))
sys.exit(0)  # Exit 0 even when blocking (decision handles it)
```

For simple blocking, exit non-zero:

```python
print("Blocked: dangerous pattern", file=sys.stderr)
sys.exit(1)  # Non-zero blocks the operation
```

### Hook Best Practices

1. **Keep hooks fast** - timeout should be <1000ms
2. **Exit 0 on success** - non-zero blocks the operation
3. **No external dependencies** - use Python standard library only
4. **Graceful degradation** - skill should work without hooks
5. **Clear prefixes** - use `[skill-name]` prefix for output
6. **Actionable guidance** - when chaining, give Claude clear next steps

### Security Considerations

Hooks can inject arbitrary text into Claude's context. This is powerful but requires trust:

- **Only install skills from trusted sources**
- Claude Code requires review in `/hooks` menu for changes
- Enterprise: `allowManagedHooksOnly` blocks user/project hooks
- Validate inputs, sanitize paths, skip sensitive files (.env, .git/)

### Example: Validation Hook

```python
#!/usr/bin/env python3
import sys
import os

tool_input = os.environ.get('TOOL_INPUT', '')

if '.env' in tool_input or 'credentials' in tool_input:
    print("Blocked: Cannot access sensitive files", file=sys.stderr)
    sys.exit(1)

sys.exit(0)
```

### Example: Skill Chaining Hook

```python
#!/usr/bin/env python3
import os

output = os.environ.get('TOOL_OUTPUT', '')

# Detect when another skill would help
if 'upgrade' in output.lower() and 'breaking' in output.lower():
    print("\n[maven-tools] Breaking changes detected in upgrade.")
    print("[maven-tools] Fetching migration documentation...")
    print("→ Use context7: python3 scripts/context7.py docs /spring-projects/spring-boot 'migration'")
```

### References

- [Hooks Reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [How to Configure Hooks - Claude Blog](https://claude.com/blog/how-to-configure-hooks)
- [Lasso Security - Hook-based Prompt Injection Defense](https://www.lasso.security/blog/the-hidden-backdoor-in-claude-coding-assistant)

---

## Quality Tooling

Use the validation scripts included in skill-crafting:

```bash
# Full analysis
python3 scripts/analyze-all.py path/to/skill/

# Check CSO compliance
python3 scripts/analyze-cso.py path/to/SKILL.md

# Check character budget (15K limit)
python3 scripts/check-char-budget.py ~/.claude/skills/

# Check cross-platform compatibility
python3 scripts/analyze-compatibility.py path/to/skill/
```

---

## Session-to-Skill Extraction

For the **current conversation**, you already have full context. No script needed.

1. Reflect on what was done in the session
2. Apply skill-worthiness criteria (see SKILL.md)
3. Generate skill or explain why not

### Tips

- **Focus on distinct segments**: Separate exploration/debugging from actual workflow
- **Short patterns (5-15 steps)** make cleaner skills
- **Filter noise**: Not everything in a session is skill-worthy

---

## Links

### Official Documentation

- [Anthropic Skill Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Agent Skills Standard](https://agentskills.io)

### Research & Articles

- [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) — 98.7% token reduction
- [Simon Willison on Skills](https://simonwillison.net/2025/Oct/16/claude-skills/)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI Adopting Skills](https://simonw.substack.com/p/openai-are-quietly-adopting-skills)

---

> **Author:** Arvind Menon
> **License:** MIT
