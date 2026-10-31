---
name: release-review
description: "Assess merge and release readiness for a software repository. Use when the user asks 'can this be merged', 'should we release now', 'what changed since the last release', or requests preparation of a software release."
license: MIT
compatibility: "Requires access to the repository and its hosting service for live CI and release status."
---

# Release Review

Ground the recommendation in the current repository state and its release conventions.

## Establish the release candidate

- Read repository guidance and inspect local changes before editing.
- Identify the intended PR or branch, current remote head, latest stable release and changes since its tag. Local branches and tags may be stale.
- Check CI for the candidate's exact commit, merge conflicts, draft state and unresolved review feedback. A successful run on an older commit does not validate a new head.
- Read what the changes do. Separate user-facing fixes, security maintenance, features and documentation-only changes when choosing whether and how to release.

## Look past direct version bumps

For dependency updates, inspect the effective dependency graph or BOM-managed versions. An explicit override can keep an older dependency even after its parent is upgraded. Verify the resolved version before removing an override.

Use upstream release notes and advisories to explain the benefit and affected configurations. An incomplete security lookup is unknown, not evidence that a version is safe. Patch/minor labels alone do not prove compatibility.

## Give an actionable recommendation

State whether the candidate can merge, whether a release is worthwhile, and any specific remaining blocker. Include the candidate commit and links to relevant checks. Distinguish failed, pending and intentionally skipped jobs. Scale verification to the change and the repository's existing checks.

A review request authorizes inspection and recommendations. Follow the user's actual authorization for edits, merges, tags and publication; do not treat those actions as implied by a request to check readiness.

## When preparation or publication is requested

- Keep versions, changelog, manifests and build fallbacks consistent with the project's conventions. Do not bump unrelated dependencies to fill out a release.
- Run the existing relevant checks and inspect the final diff. Recheck the candidate head before merging.
- Tag the validated commit according to the repository's release flow. If a tag starts artifact publication, keep the release draft until the artifact checks pass.
- Check the artifacts users will install: versions, supported architectures or package contents, and a small real usage smoke test where appropriate. A successful source build does not verify published artifacts.
- Publish within the authorized scope, then confirm any downstream registry publication. Report partial failures precisely; do not conceal them with a successful tag or release page.
- Start the next snapshot cycle only where that is the project's convention, retaining published metadata at the released version.

For a long build, report meaningful phase changes and check for failures. Follow the hosting service's retry limits; investigate a failed run before retrying it.
