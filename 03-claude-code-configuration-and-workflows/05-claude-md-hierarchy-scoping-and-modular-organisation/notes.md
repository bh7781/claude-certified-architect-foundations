# CLAUDE.md Hierarchy, Scoping, and Modular Organisation

## What You Need to Know

Claude Code reads configuration from CLAUDE.md files at three levels. Knowing which one applies where — and spotting when the wrong level was used — comes up again and again on the exam.

## The Three-Level Hierarchy

**User-level: ~/.claude/CLAUDE.md**

This file applies only to you. It lives in your home directory, outside any repository, so it isn't version-controlled and never travels through git. Clone the repo as a new teammate and you won't get these instructions. Keep this level for strictly personal preferences: verbosity settings, a preferred output style, your own shortcuts.

**Project-level: .claude/CLAUDE.md or root CLAUDE.md**

This file applies to everyone on the project. It lives in the repository and is version-controlled, so every developer who clones or pulls the repo gets these instructions automatically. Team-wide standards belong here: naming conventions, error handling patterns, testing requirements, architecture decisions, code review checklists.

Both .claude/CLAUDE.md (inside the .claude directory) and a CLAUDE.md at the repository root are valid project-level locations. The exam may present either path.

**Directory-level: subdirectory CLAUDE.md files**

These apply when you're working in that specific directory. Use them for package-specific conventions that differ from the project root. A /packages/api/CLAUDE.md, say, might hold REST conventions that the frontend package never needs.

## Loading Order and Conflict Handling

CLAUDE.md files aren't a strict-precedence config. The Anthropic memory docs are explicit: "All discovered files are concatenated into context rather than overriding each other." Every applicable file loads into the same context window. None replaces another.

The docs describe a documented load order, not a precedence chain:

- Files are ordered from broadest scope to most specific. A project instruction appears in context after a user instruction. Across the directory tree, "content is ordered from the filesystem root down to your working directory," so "instructions closer to where you launched Claude are read last."
- Within a directory, CLAUDE.local.md is appended after CLAUDE.md, so your personal notes are the last thing Claude reads at that level.

None of this makes it a winner-take-all hierarchy. The docs are blunt about it: "if two rules contradict each other, Claude may pick one arbitrarily." CLAUDE.md is delivered as a user message — not as part of the system prompt — and Anthropic says "there's no guarantee of strict compliance." Treat CLAUDE.md as guidance the model usually follows, not as a configuration layer with deterministic overrides.

The practical consequence: if a rule must hold on every run — a blocked tool, a required formatter, a permission policy — don't lean on CLAUDE.md scoping to enforce it. Encode it in settings.json (which the client enforces regardless of what Claude decides) or in a hook (which fires at a fixed lifecycle event). The Anthropic docs spell this out directly: "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer."

## Don't confuse CLAUDE.md with settings.json

settings.json has a strict precedence chain (managed policy > local > project > user, with managed always winning). CLAUDE.md does not — files are concatenated and conflicts may resolve arbitrarily. If a question asks "which CLAUDE.md wins on a conflict?", the docs-honest answer is "neither is guaranteed to — move the rule to settings.json or a hook." Watch for distractors that claim "more specific scope wins" or "user-level overrides project-level": both are paraphrases the official docs never make.

## Modular Organisation with @ path imports

Past a few hundred lines, one CLAUDE.md becomes a slog to maintain. The @ syntax lets you split it across files and reference them from the main one. The directive is just @ followed by a path. There is no @import keyword, even though half the docs you'll find online write it that way.

The syntax in your CLAUDE.md:

```
# .claude/CLAUDE.md

Coding standards:

@./standards/naming-conventions.md
@./standards/error-handling.md
@./standards/testing-requirements.md
```

Each @<path> line gets that file inlined into the CLAUDE.md at load time. Per-package CLAUDE.md files can import only the standards that apply to them. The API package pulls in API conventions, the frontend pulls in component rules. No duplication.

One thing the docs are quiet about: imports load eagerly. The referenced file gets inlined the moment Claude reads your CLAUDE.md, exactly as if you'd pasted it in. So splitting a 600-line CLAUDE.md into six 100-line imports makes the source nicer to work in, but the context Claude actually sees is the same size. If you want to shrink per-session context, the tool for the job is .claude/rules/ with path-scoped frontmatter (covered in Task Statement 3.3). Those files only load when Claude is working in matching paths.

## CLAUDE.local.md, local-only overrides

CLAUDE.local.md lives next to CLAUDE.md at any level in the hierarchy and loads the same way, with three small differences worth knowing:

- **Loading order.** CLAUDE.local.md is appended after CLAUDE.md at the same level, so your personal notes are the last thing Claude reads there. That's load order, not precedence: reading last doesn't win a contradiction. If two instructions conflict, Claude may still pick either one.
- **Gitignored by convention.** The .local suffix flags files you don't want committed. Most teams add CLAUDE.local.md to .gitignore so personal tweaks stay personal.
- **What it's for.** The shared CLAUDE.md is the team's rules. The CLAUDE.local.md next to it is your own quirks for this repo: a favourite scratchpad path, a verbose explanation you keep needing to re-paste, a temporary debugging note you'll delete next week.

Think of CLAUDE.local.md as a project-scoped version of ~/.claude/CLAUDE.md: same idea, narrower scope. If you find yourself reaching for it to express a team rule, that rule belongs in CLAUDE.md instead.

## The .claude/rules/ Directory

As an alternative to a single CLAUDE.md file, the .claude/rules/ directory holds topic-specific rule files:

- testing.md — test naming, assertion patterns, fixture usage
- api-conventions.md — endpoint naming, request/response schemas
- deployment.md — deployment checklist, environment configuration

Each file can optionally include YAML frontmatter with path scoping (covered in detail in Task Statement 3.3). Without frontmatter, rules files load for all sessions.

## Diagnosing What Loaded: /memory and /context

When behaviour drifts between sessions, or between developers, you need to see which memory files the session actually picked up. If Claude Code follows the team conventions for one teammate and ignores them for another, that answer settles it.

Current Claude Code splits the job across two commands. /memory lists your CLAUDE.md, CLAUDE.local.md and auto-memory locations, and opens any of them in your editor. /context reports what actually loaded into this session, under Memory files — so to confirm a file is live, run /context and read that list. The docs are explicit about it: "check the list under Memory files to verify your CLAUDE.md and CLAUDE.local.md files loaded". (Claude Code memory docs, verified August 2026.)

**Key Concept**

Neither command loads anything. They reveal which files are already loaded — configuration loads automatically based on its level and location. Use them to diagnose, not to activate. That is the part the exam tests, and it holds for /memory and /context alike.

**On the exam, answer /memory**

The exam guide (v1.0) predates the split and treats /memory as the command that shows which files are loaded. Give /memory as the keyed answer. Run /context at your actual keyboard.

## What Survives Compaction

When /compact summarises a long session, project-root CLAUDE.md comes back intact. Not because it sits somewhere privileged. Because Claude re-reads it from disk after compaction and re-injects it, and your instructions were never part of the conversation history to begin with, so there's nothing there for the summariser to compress.

Two things don't come back automatically: nested CLAUDE.md files in subdirectories, and .claude/rules/ files with paths: frontmatter. Both load on demand, so they return the next time Claude reads a matching file rather than the moment compaction ends. When an instruction seems to vanish after /compact, that's usually why. The other candidate is an instruction that only ever existed in conversation, which compaction is free to summarise.

## The Critical Exam Scenario: New Team Member Not Receiving Instructions

This is the exam's favourite trap for Task Statement 3.1. It usually runs like this:

Developer A has been on the team for months. Claude Code follows all the team's conventions perfectly — API naming, test structure, error handling. Developer B joins the team, clones the repository, and Claude Code produces inconsistent results that ignore the conventions.

The root cause is always the same: the conventions are stored in Developer A's user-level config (~/.claude/CLAUDE.md) instead of the project-level config (.claude/CLAUDE.md or root CLAUDE.md). User-level config is not shared via git. Developer B never received the instructions.

The fix: move instructions from user-level to project-level configuration.

You need to diagnose this on sight. See "new team member" paired with "inconsistent behaviour"? Check where the configuration lives.

## Exam Traps

**Exam Trap**

New team member not receiving Claude Code instructions despite working on the same repo and branch

The instructions are in user-level config (~/.claude/CLAUDE.md) instead of project-level. User-level is not version-controlled or shared via git. Move to .claude/CLAUDE.md for team-wide application.

**Exam Trap**

Thinking /memory triggers configuration loading

/memory is a diagnostic command that shows which files are loaded. Configuration files load automatically based on their location in the hierarchy. /memory helps you debug — it does not activate anything.

**Exam Trap**

Assuming directory-level CLAUDE.md is the best solution for cross-directory conventions

Directory-level CLAUDE.md applies to one directory only. For conventions spanning many directories (like test files spread throughout a codebase), use path-specific rules in .claude/rules/ with glob patterns instead.
