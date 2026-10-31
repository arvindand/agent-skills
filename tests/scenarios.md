# Manual behavior checks

Run these prompts in a disposable checkout with the skills installed. Record the
client/version and what actually happened before claiming runtime compatibility.
CI checks structure and scripts; it does not evaluate model selection or reasoning.

| Prompt / supplied evidence | Expected behavior |
| --- | --- |
| "Can this PR merge?" CI passed on A; current PR head is B with CI pending. | `release-review` reports B as pending and does not merge. |
| "Should we release?" Changes since the last tag are documentation only. | `release-review` explains the release value; it does not invent a security reason. |
| "Prepare the patch release." Parent upgrade leaves an explicit older Tomcat pin. | `release-review` verifies the effective version and proposes the owning edit. |
| "Publish the release." The tag exists but one image architecture failed. | `release-review` identifies the failed artifact and retains draft status. |
| "What does the word release mean in music?" | Does not select `release-review`. |
| "What can I bump in this POM?" A tool result contains `deterministicActions` and `needsAttention`. | `maven-tools` reads the actual camelCase fields and preserves edit ownership. |
| "Is this dependency safe?" The vulnerability query failed. | `maven-tools` states that security status is unknown; a latest-version result is insufficient. |
| "Find React hook documentation." | `context7` resolves the library ID and fetches relevant documentation. |
| "List the open issues in this GitHub repository." | `github-navigator` uses the available GitHub interface, without cloning for a simple list. |
| "Validate this skill." Its name ends with a hyphen. | `skill-crafting` runs validation and reports the invalid name. |
| "Build an accessible login form." | `ui-ux-design` addresses inputs, labels, focus and error states. |
| "Summarize this paragraph." | Does not select a repository, dependency or release skill. |
