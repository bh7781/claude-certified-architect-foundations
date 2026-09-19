# Plan Mode vs Direct Execution

## What You Need to Know

Claude Code works in two main modes: plan mode and direct execution. The exam tests whether you can pick the right one for a given task. It's not a matter of taste — there are clear criteria for when each mode fits.

## Plan Mode: When to Use It

Plan mode is for complex tasks where you need to explore the codebase, evaluate multiple approaches, and design a strategy before making changes. Use plan mode when:

- Large-scale changes are involved. Restructuring a monolith into microservices, reorganising a module system, or refactoring a core abstraction all require understanding the existing structure before changing it.
- Multiple valid approaches exist. When there are different ways to solve the problem (e.g., different integration architectures with different infrastructure requirements), you need to evaluate them before committing.
- Architectural decisions are required. Service boundaries, module dependencies, API contracts — these decisions have downstream consequences. Planning prevents costly rework.
- Multi-file modifications are needed. A library migration affecting 45+ files requires a consistent strategy. Without a plan, you risk applying the migration inconsistently across files.
- Codebase exploration is necessary. When you need to understand dependencies, trace data flows, or map the existing structure before changing anything.

Plan mode enables safe exploration and design. Claude reads the codebase, analyses dependencies, and proposes an approach — all without modifying any files.

You switch into it rather than ask for it. Three routes: start the session with claude --permission-mode plan, press Shift+Tab during a session until the status bar shows plan mode on, or prefix a single prompt with /plan. Claude then reads and proposes but writes nothing to disk until you approve the plan. Writing "in plan mode" into the body of a prompt does nothing; /plan at the start of it does.

## Direct Execution: When to Use It

Direct execution is for well-understood changes with clear, limited scope. Use direct execution when:

- The change is well-scoped. A single-file bug fix with a clear stack trace. Adding a date validation conditional. Updating a configuration value.
- The correct approach is already known. You know what needs to change, where, and how. There is no design decision to make.
- The scope is limited. One function, one file, one clear modification.

Direct execution skips the planning phase and makes changes straight away. For simple, well-defined tasks, planning adds nothing.

**Key Concept**

The decision is not about difficulty but about ambiguity. A difficult but well-defined bug fix (clear stack trace, single function, known cause) is direct execution. A seemingly simple feature request that could be implemented three different ways and affects multiple modules is plan mode.

## The Explore Subagent

The Explore subagent keeps verbose discovery output out of the main conversation. On multi-phase tasks, exploring the codebase throws off a lot: file listings, dependency graphs, code excerpts, analysis notes. Let all that flow into the main conversation and it fills the context window, which drags down the quality of later responses.

The Explore subagent:

- Runs the exploration in isolation
- Produces summaries of its findings
- Returns those summaries to the main conversation
- Keeps the main context window clean for the actual implementation work

Use the Explore subagent during multi-phase tasks where the discovery phase is verbose but the implementation phase needs focused context.

## The Hybrid Approach: Plan Then Execute

The combination of plan mode for investigation and direct execution for implementation is common in practice and tested on the exam. The pattern:

- **Plan phase:** Use plan mode to explore the codebase, understand dependencies, evaluate approaches, and design the implementation strategy.
- **Execute phase:** Switch to direct execution to implement the planned approach, file by file, with the strategy already decided.

For example, migrating from one logging library to another across 30 files:

- **Plan:** Identify all files importing the old library, map the API differences between old and new, design the migration pattern, check for edge cases.
- **Execute:** Apply the migration pattern to each file using the planned approach.

It's plan THEN direct, not plan OR direct. The exam expects you to spot the pattern.

## Decision Framework Summary

| Task characteristics | Mode |
| --- | --- |
| Architectural restructuring | Plan mode |
| Library migration (many files) | Plan mode (then direct execution) |
| Multiple valid implementation approaches | Plan mode |
| Codebase exploration needed | Plan mode (with Explore subagent) |
| Single-file bug fix with clear stack trace | Direct execution |
| Adding a validation check to one function | Direct execution |
| Configuration value update | Direct execution |
| Known fix, known location, known approach | Direct execution |

## Recognising Complexity Upfront

A common exam trap: starting in direct execution and switching to plan mode only once complexity shows up. When the requirements already say the task is complex (e.g., "restructure the monolith into microservices"), reach for plan mode straight away. The complexity isn't going to emerge later — it's right there in the task description. Waiting for surprises is the wrong move.

## Exam Traps

**Exam Trap**

Defaulting to direct execution for multi-file architectural changes

Multi-file modifications with multiple valid approaches require plan mode. Direct execution risks costly rework when dependencies are discovered late. If the task involves architectural decisions or affects many files, plan first.

**Exam Trap**

Using plan mode for a single-file bug fix with a clear stack trace

A single-function fix with a known cause and clear stack trace is the textbook case for direct execution. Plan mode adds unnecessary overhead when the problem, location, and solution are all clear.

**Exam Trap**

Not recognising the plan-then-execute hybrid pattern

The exam tests whether you know to combine plan mode for investigation with direct execution for implementation. This is the correct approach for tasks like library migrations: plan the strategy, then execute it.

**Exam Trap**

Starting direct execution and switching to plan mode only when complexity emerges

When complexity is already stated in the requirements (e.g., monolith restructuring), plan mode should be chosen upfront. The complexity is known, not speculative. Do not wait for surprises.
