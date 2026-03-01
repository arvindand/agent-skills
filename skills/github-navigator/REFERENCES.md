# GitHub Navigator References

Optional examples, installation notes, and troubleshooting for lower-frequency `gh` tasks.

## Complete Examples

### Example 1: "Show me the README from facebook/react"

```bash
# Discover
gh api --help  # Learn about gh api

# Execute
gh api repos/facebook/react/contents/README.md -H "Accept: application/vnd.github.raw"
```

### Example 2: "List open issues in vercel/next.js"

```bash
# Discover
gh issue list --help

# Execute
gh issue list --repo vercel/next.js --state open
```

### Example 3: "What's in the packages directory of vercel/next.js?"

```bash
# Discover
gh api --help

# Execute
gh api repos/vercel/next.js/contents/packages | jq -r '.[].name'
```

### Example 4: "Show latest release for react"

```bash
# Discover
gh release view --help

# Execute
gh release view --repo facebook/react
```

### Example 5: "Check if PR #12345 in cli/cli passed CI"

```bash
# Discover
gh pr checks --help

# Execute
gh pr checks 12345 --repo cli/cli
```

### Example 6: "Clone the react repository"

```bash
# Safe operation, execute directly
gh repo clone facebook/react
```

## Installation

### Install gh CLI

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Linux (Fedora)
sudo dnf install gh

# Windows
winget install GitHub.cli
```

### Authenticate

```bash
gh auth login
```

Follow prompts to authenticate via browser or token.

### Verify Installation

```bash
gh --version
gh auth status
```

## Troubleshooting

**Commands not found:**

- Install gh CLI (see Installation above)

**Permission errors:**

- Authenticate: `gh auth login`
- Refresh with scopes: `gh auth refresh -s repo -s workflow`

**Private repo access:**

- Ensure you're authenticated: `gh auth status`
- Verify you have access to the repo on GitHub

**Rate limit errors:**

- Authenticate for 5000/hr (vs 60/hr unauthenticated)

## Advanced: GraphQL Queries

For complex data fetching:

```bash
gh api graphql -f query='
  query {
    repository(owner: "facebook", name: "react") {
      issues(first: 5, states: OPEN) {
        nodes {
          title
          number
        }
      }
    }
  }'
```

## Rate Limiting Details

| Auth Status | Rate Limit |
|-------------|------------|
| Authenticated | 5,000 requests/hour |
| Unauthenticated | 60 requests/hour |

**gh CLI automatically handles rate limiting** - waits and retries.

---

> **License:** MIT
