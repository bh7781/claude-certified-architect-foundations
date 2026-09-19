# Path-Specific Rules for Conditional Convention Loading

## What You Need to Know

Path-specific rules apply conventions conditionally, based on which files you're editing. They solve something neither root CLAUDE.md nor directory-level CLAUDE.md handles well: conventions that must apply to one file type scattered across many directories.

## How Path-Specific Rules Work

Rule files live in the .claude/rules/ directory. Each file carries YAML frontmatter with a paths field specifying glob patterns. The rules inside load only when you're editing files that match those patterns.

```yaml
---
paths: ["terraform/**/*"]
---
# Terraform Conventions

- Use snake_case for all resource names
- Tag every resource with environment and team labels
- Never hardcode AMI IDs — use data sources
- All modules must have a variables.tf, outputs.tf, and README.md
```

Edit a file matching terraform/**/* and these rules load automatically. Edit a React component or an API handler and they don't. The rules stay invisible until they're relevant.

## Glob Patterns Match Across the Entire Codebase

This is where they earn their keep. A glob like **/*.test.tsx catches every test file in the codebase, wherever it sits. Take a typical project structure:

```
src/
  components/
    Button.tsx
    Button.test.tsx
  api/
    auth.ts
    auth.test.ts
  utils/
    format.ts
    format.test.ts
  pages/
    dashboard/
      Dashboard.tsx
      Dashboard.test.tsx
```

Test files sit next to their source files across four directories. A path-specific rule with paths: ["**/*.test.tsx", "**/*.test.ts"] applies the same test conventions to every one of them, automatically.

## Why Not Directory-Level CLAUDE.md?

A directory-level CLAUDE.md applies to files in that one directory. To cover test files spread across 50+ directories, you'd have to drop a CLAUDE.md into every single directory that holds tests. That means:

- 50+ copies of the same conventions
- Every new directory with tests needs a new copy
- Any convention change requires updating all 50+ files
- Inevitable drift as some copies fall behind

Path-specific rules with glob patterns eliminate this entirely. One file, one pattern, universal coverage.

## Why Not Root CLAUDE.md?

Root CLAUDE.md loads for every session, regardless of which files you edit. Put your Terraform conventions in the root CLAUDE.md and they burn tokens even while you're editing React components. Put your test conventions there and they load while you're writing API handlers.

**Key Concept**

Path-scoped rules are more token-efficient than root CLAUDE.md because they load ONLY when editing matching files. This reduces irrelevant context and keeps the model focused on conventions that actually apply to the current work. In large projects with many convention categories, this efficiency gain is substantial.

## Practical Rule File Examples

Test conventions across the entire codebase:

```yaml
---
paths: ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx"]
---
# Test Conventions

- Use describe/it blocks with descriptive names that read as sentences
- Each test file must have at least one happy path and one error case
- Use factory functions for test data, not inline object literals
- Mock external services at the module boundary, not individual functions
- Assert behaviour, not implementation details
```

API conventions for any route handler:

```yaml
---
paths: ["src/api/**/*", "**/routes/**/*", "**/*.controller.ts"]
---
# API Conventions

- All endpoints return { data, error, metadata } response shape
- Use Zod schemas for request validation at the handler boundary
- Log request ID on every error response
- Rate limiting configuration must be explicit, not inherited from defaults
```

Infrastructure-as-code conventions:

```yaml
---
paths: ["terraform/**/*", "**/*.tf", "infrastructure/**/*"]
---
# Infrastructure Conventions

- State files must reference remote backends, never local
- Use workspaces for environment separation
- Every module must be versioned with a CHANGELOG
```

## When to Use Each Approach

| Scenario | Best approach |
| --- | --- |
| Universal team standards that apply to all code | Root CLAUDE.md |
| Conventions for one specific package directory | Directory-level CLAUDE.md |
| Conventions for a file type spread across many directories | Path-specific rules with glob patterns |
| Task-specific workflows invoked on demand | Skills in .claude/skills/ |

The exam frequently presents the scenario of test files co-located with source files across many directories. The answer is always path-specific rules with glob patterns.

## Exam Traps

**Exam Trap**

Choosing directory-level CLAUDE.md over path-specific rules for cross-directory conventions

When conventions must apply to files spread across 50+ directories (like co-located test files), path-specific rules with glob patterns are correct. Directory-level CLAUDE.md would require placing a file in every directory — a massive maintenance burden.

**Exam Trap**

Placing file-type-specific conventions in root CLAUDE.md

Root CLAUDE.md loads for every session regardless of which files you edit. Terraform conventions consume tokens when editing React components. Path-specific rules load only when editing matching files, preserving token budget.

**Exam Trap**

Confusing skills with path-specific rules for automatic convention application

Both skills and .claude/rules/ can auto-activate via a paths frontmatter, but they serve different purposes. Rules stay in context as background guidance — loaded when Claude reads a matching file — so they shape every edit. Skills load on-demand as task-style workflows, triggered either by the model's intent match or by explicit invocation. When the question asks about automatic, always-on convention loading for a file type, path-specific rules are the right answer.
