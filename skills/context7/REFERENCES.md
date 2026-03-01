# Context7 References

Optional quick lookup material for when the main workflow needs concrete examples or extra context.

## Common Library IDs

These are useful shortcuts when you already know the target library:

- React: `/facebook/react`
- Next.js: `/vercel/next.js`
- Prisma: `/prisma/prisma`
- Supabase: `/supabase/supabase`
- Express: `/expressjs/express`

## Example Commands

```bash
# Search when the library ID is unclear
python3 scripts/context7.py search "next.js app router"

# Fetch API/code examples
python3 scripts/context7.py docs /facebook/react hooks

# Fetch conceptual docs
python3 scripts/context7.py docs /vercel/next.js "app router" info

# Fetch version-specific docs
python3 scripts/context7.py docs /vercel/next.js/14 "server actions"
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
- Use `python3 scripts/context7.py --help` when the command syntax is unclear.

---

> **License:** MIT
