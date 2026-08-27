# Context7 References

Optional quick lookup material for when the main workflow needs concrete examples or extra context.

## Common Library IDs

Starting points only. Library IDs are assigned upstream and get renamed, so treat any ID
here as a guess and fall back to `search` the moment a fetch fails. A renamed ID returns
a redirect rather than a 404.

- React: `/reactjs/react.dev`
- Next.js: `/vercel/next.js`
- Prisma: `/prisma/prisma`
- Supabase: `/supabase/supabase`
- Express: `/expressjs/express`

## Example Commands

```bash
# Search when the library ID is unclear
python3 ${CLAUDE_SKILL_DIR}/scripts/context7.py search "next.js app router"

# Fetch API/code examples
python3 ${CLAUDE_SKILL_DIR}/scripts/context7.py docs /reactjs/react.dev hooks

# Fetch conceptual docs
python3 ${CLAUDE_SKILL_DIR}/scripts/context7.py docs /vercel/next.js "app router" info

# Fetch version-specific docs (full upstream tag, not a bare major)
python3 ${CLAUDE_SKILL_DIR}/scripts/context7.py docs /vercel/next.js/v15.1.8 "server actions"
```

## Usage Notes

- Script path is relative to this skill directory.
- The script uses Python's standard library only.
- `CONTEXT7_API_KEY` is optional and mainly helps with higher rate limits.
- Results are fetched live; there is no local cache layer in this skill.

## Troubleshooting

- Broaden the topic if the result is too narrow or empty.
- Switch modes if `code` gives weak results and the user really needs guides or migration context.
- Re-run search if the library name is ambiguous or the ID looks wrong.
- Use `python3 ${CLAUDE_SKILL_DIR}/scripts/context7.py --help` when the command syntax is unclear.

---

> **License:** MIT
