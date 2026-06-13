---
name: maven-tools
description: "JVM dependency intelligence via Maven Tools MCP server. Use when the user asks about Maven or Gradle dependencies, safe upgrades, CVEs, license risks, release history, or project dependency health. Use when reviewing `pom.xml`, `build.gradle`, `build.gradle.kts`, or Maven coordinates. Use when the user says 'check my dependencies', 'should I upgrade X', 'what can I safely bump', or 'is this version safe'. Use even when the user just pastes a `groupId:artifactId` coordinate without a verb."
allowed-tools: mcp__maven-tools__* mcp__context7__* WebSearch WebFetch
license: MIT
compatibility: "Requires the Maven Tools MCP server (arvindand/maven-tools-mcp) and network access."
---

# Maven Tools

Use this skill to ground JVM dependency decisions in live Maven Central data.

This is an execution skill. Use Maven Tools MCP first for dependency facts, then do the reasoning in-model. Assume Maven Tools MCP is already configured; only discuss setup if the tools are unavailable.

## When to Use

Activate when the user asks about:

- Java, Kotlin, Scala, or JVM dependencies
- Maven, Gradle, `pom.xml`, `build.gradle`, or `build.gradle.kts`
- latest versions, upgrades, CVEs, licenses, dependency age, or release history
- whether a dependency is safe, current, stale, or worth upgrading

## Core Boundary

Use Maven Tools MCP for version, security, license, freshness, and release-pattern facts from Maven Central.

- Do the reasoning in-model: recommend next steps, call out risk, and separate safe-now actions from manual-review items.
- Normalize dependency inputs to `groupId:artifactId` or `groupId:artifactId:version` as needed.
- For recommendation questions, evaluate concrete candidates with Maven Tools first, then add documentation context before making a strong call.
- Do not use Maven metadata alone to decide library popularity, framework fit, migration effort, or performance tradeoffs.

## Tool Selection

Choose the narrowest tool that matches the request:

| Intent | Tool | Default Parameters |
|--------|------|--------------------|
| latest version lookup | `get_latest_version` | `stabilityFilter: PREFER_STABLE` |
| check exact version | `check_version_exists` | none |
| bulk candidate check (no current versions) | `check_multiple_dependencies` | `stabilityFilter: PREFER_STABLE` |
| upgrade analysis (single coordinate, with current version) | `compare_dependency_versions` | `includeSecurityScan: true`, `stabilityFilter: STABLE_ONLY` |
| whole-POM upgrade plan (raw `pom.xml`) | `recommend_pom_upgrades` | `mode: MINOR_PATCH` |
| resolve effective POM versions (raw `pom.xml`) | `analyze_pom_dependencies` | none |
| age/freshness | `analyze_dependency_age` | use project-appropriate threshold |
| maintenance signal / release history | `analyze_release_patterns` | `monthsToAnalyze: 24` |
| full project audit | `analyze_project_health` | `includeSecurityScan: true`, `includeLicenseScan: true`, `stabilityFilter: PREFER_STABLE` |

Default to `analyze_project_health` when the user says "check my dependencies" or pastes a project dependency set.

When the user provides raw `pom.xml` content, prefer the POM-aware tools: `analyze_pom_dependencies` resolves and classifies effective versions (`EXPLICIT` / `MANAGED` / `EXPLICIT_OVERRIDE`) and surfaces multi-BOM conflicts; `recommend_pom_upgrades` returns an actionable upgrade plan. Both walk the parent chain, apply `<dependencyManagement>`, and resolve `<scope>import</scope>` BOMs; pass `sideloadedPoms` for monorepo siblings or unreleased parents.

Use `check_multiple_dependencies` for candidate sets without current versions. Use `compare_dependency_versions` for single-coordinate upgrade decisions. Use `analyze_project_health` for broad audits, not every single dependency question.

## Workflow

1. Extract dependencies from user input or the build file
2. Pick the narrowest tool that answers the request
3. Report the result in decision-oriented language:
   - what is current
   - what changed
   - what is safe to do now
   - what needs manual review

### Whole-POM upgrades and bot-like maintenance

When the user hands you a raw `pom.xml` and wants to know what to upgrade ("what can I safely bump?", scheduled maintenance, dependency-bot replacement), lead with `recommend_pom_upgrades`:

- `mode: MINOR_PATCH` (default) keeps major upgrades out of the safe path
- apply `deterministic_actions[]` directly — these are mechanical `<version>` edits (`explicit_bump` for declared deps, `bom_bump` for user-controllable BOMs)
- route `needs_attention[]` (majors, multi-BOM conflicts, explicit overrides) to human or LLM review; each entry carries the Maven Central latest for context

One call returns everything mechanical plus the review queue — no per-coordinate fan-out for whole-POM flows. Reach for `analyze_pom_dependencies` first when the user wants the raw resolution ("what does my POM actually resolve to?") without recommendations.

### Single-coordinate upgrade decisions

For a specific dependency ("should I upgrade X from 2.7 to 3.2?"), prefer `compare_dependency_versions` with:

- `includeSecurityScan: true`
- `stabilityFilter: STABLE_ONLY`

Then interpret the result conservatively:

- patch and minor updates are the default safe path
- major updates should be treated as manual review unless the user explicitly wants a breaking upgrade

When `compare_dependency_versions` returns `same_major_stable_fallback`:

- treat the top-level major upgrade as the long-term path
- treat the fallback as the safest immediate upgrade target
- surface both, but recommend the fallback first for conservative maintenance workflows

If the user asks whether a dependency is safe:

1. use `compare_dependency_versions` when remediation guidance matters
2. use `analyze_release_patterns` when maintenance risk matters
3. combine the two instead of relying only on "latest version" checks

## Documentation Handoff

When the answer needs migration guides, API details, or library usage patterns, add documentation context before giving a strong recommendation.

Use this order:

1. use Maven Tools MCP first for dependency facts
2. if raw Context7 tools are available in the current tool list, use them directly
3. otherwise, if standalone Context7 tools are available, use them
4. otherwise, use `WebSearch` and `WebFetch` for official docs, release notes, and migration guides
5. if no documentation path is available, say dependency facts are available but deeper doc lookup is not

Use this especially for:

- major upgrades
- migration planning
- recommendation-style comparisons between candidate libraries

## Less Helpful / Out of Scope

- private artifact repositories that are not mirrored through Maven Central
- non-JVM ecosystems that do not use Maven coordinates
- trivial one-off lookups where the exact dependency and decision are already obvious
- recommendation questions driven mostly by ecosystem adoption or benchmarks unless you also add docs and broader research

## Setup Assumption

Assume the user already has Maven Tools MCP configured.

- `arvindand/maven-tools-mcp:latest` is the default when raw Context7 tools should be exposed through the same server
- `arvindand/maven-tools-mcp:latest-noc7` is the clean option when documentation is handled separately

Only discuss installation when the tools are unavailable.

## Recovery

| Issue | Action |
|-------|--------|
| MCP tools unavailable | Tell the user Maven Tools MCP is not configured and point them to <https://github.com/arvindand/maven-tools-mcp>. Mention `:latest` when they want raw Context7 in the same server, or `:latest-noc7` when docs are handled separately. |
| Dependency not found | Verify `groupId:artifactId` format and check whether the artifact is on Maven Central. |
| Raw Context7 tools unavailable | Use standalone Context7 tools if available; otherwise fall back to `WebSearch` and `WebFetch`. |
| No documentation path is available | Say dependency facts are available but deeper migration or API docs are not available in the current environment. |
| Security scan is incomplete or slow | Use the partial result, say CVE data may be incomplete, and continue with version/maintenance guidance. |
| Version type is unclear | Treat it as unstable and prefer a known stable release. |

---

> **License:** MIT
> **Requires:** [Maven Tools MCP server](https://github.com/arvindand/maven-tools-mcp)
> **Pairs with:** [context7 skill](../context7/) or standalone Context7 tools for documentation-heavy follow-up
