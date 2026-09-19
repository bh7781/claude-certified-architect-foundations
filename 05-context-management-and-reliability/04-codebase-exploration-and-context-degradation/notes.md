# Codebase Exploration & Context Degradation

## What You Need to Know

Large codebase exploration is one of the most context-intensive tasks a Claude-based agent performs. Whether an agent is exploring an unfamiliar repository, tracing dependency chains, or understanding legacy systems, extended sessions create a specific failure mode: context degradation. It has nothing to do with running out of tokens. The model simply loses its grip on earlier findings as the context fills with verbose discovery output.

## Context Degradation

Context degradation manifests as a specific, observable behaviour: the model starts referencing "typical patterns" instead of the specific classes, methods, and dependency chains it discovered earlier in the session. After investigating several modules, the agent might say "this follows the typical repository pattern" instead of "the OrderRepository class at src/repos/order.ts implements the base Repository<T> interface with custom caching in the findById method."

This happens because:

- Each exploration step generates verbose output (file contents, search results, directory listings).
- This output accumulates in the conversation context.
- Earlier, precise discoveries are pushed further into the context while more recent verbose output dominates.
- The model's attention shifts to recent output and it loses specific references to earlier findings.

The critical insight: context degradation is not a token limit problem. Increasing the context window doesn't fix it. The model isn't running out of space. It's losing track of specific details as they get buried under newer, more verbose output.

## Scratchpad Files

The primary mitigation for context degradation is scratchpad files. The agent writes key findings to a file and references it for subsequent questions. This persists knowledge outside the conversation context, making it immune to context degradation.

```markdown
# Exploration Scratchpad — Order Service

## Key Classes
- `OrderRepository` (src/repos/order.ts) — implements Repository<T>, custom findById caching
- `OrderService` (src/services/order.ts) — orchestrates OrderRepository + PaymentGateway
- `RefundProcessor` (src/services/refund.ts) — depends on OrderService.getOrderWithItems()

## Dependency Chain
RefundProcessor → OrderService → OrderRepository → PostgreSQL
RefundProcessor → PaymentGateway → Stripe API

## Critical Findings
- RefundProcessor has no retry logic for Stripe API failures
- OrderRepository caches by orderId but cache invalidation on status change is missing
- Test coverage: OrderService has 87% coverage, RefundProcessor has 12%
```

When the agent needs to reference earlier discoveries, it reads the scratchpad file instead of relying on conversation context. Treat this as a deliberate strategy from the outset, not a rescue move once things degrade — agents should be instructed to maintain scratchpad files from the start of any extended exploration session.

## Subagent Delegation

Spawning subagents for specific investigation tasks is the second major mitigation strategy. Instead of the main agent doing all exploration directly (filling its context with verbose output from every file read and search), delegate specific questions to subagents:

- "Find all test files for the order service and report their coverage status"
- "Trace the refund flow from API endpoint to database and list all intermediate services"
- "Identify all external API integrations and their error handling patterns"

Each subagent operates with its own isolated context. It can explore verbosely without polluting the main agent's context. It returns a structured summary to the coordinator, which keeps only the key findings.

Parallelisation is the obvious read; the real value is context isolation. The main agent's context stays clean for high-level coordination while subagents handle the verbose exploration.

## Summary Injection Between Phases

When exploration happens in phases (Phase 1: understand the architecture, Phase 2: investigate specific components), summarise key findings from Phase 1 before spawning Phase 2 subagents. Inject these summaries into the initial context of Phase 2 subagents.

This prevents the "cold start" problem where Phase 2 subagents duplicate Phase 1 exploration because they were not given the previous findings. It also ensures that Phase 2 agents have the architectural understanding needed to ask the right questions.

```text
Phase 1 Summary (injected into Phase 2 subagent prompts):
- The system follows a layered architecture: Controllers → Services → Repositories → Database
- The refund flow passes through: RefundController → RefundProcessor → OrderService → PaymentGateway
- Key concern: RefundProcessor has no retry logic for external API failures
- Phase 2 objective: Investigate error handling in RefundProcessor and PaymentGateway
```

## The /compact Command

Claude Code provides a /compact command specifically for reducing context usage during extended sessions. When context fills with verbose discovery output — file contents, search results, directory listings — /compact summarises the conversation to free up space while preserving key information.

Use /compact proactively during extended exploration sessions, not just when you hit context limits. It's there to protect context quality, not only quantity.

## Crash Recovery via Structured State Manifests

Extended exploration sessions can fail due to session crashes, network interruptions, or context exhaustion. Without recovery mechanisms, all exploration progress is lost.

The fix is structured state persistence. Each agent exports its current state to a known file location (a manifest). This manifest includes:

- What has been explored (files read, searches performed)
- Key findings discovered so far
- Current phase and next steps
- Any pending questions or unresolved issues

```json
{
  "sessionId": "explore-order-service-001",
  "phase": 2,
  "exploredPaths": [
    "src/repos/order.ts",
    "src/services/order.ts",
    "src/services/refund.ts"
  ],
  "keyFindings": {
    "architecture": "Layered: Controllers → Services → Repositories → DB",
    "criticalIssue": "RefundProcessor has no retry logic for Stripe API failures",
    "testCoverage": {"OrderService": "87%", "RefundProcessor": "12%"}
  },
  "nextSteps": [
    "Investigate PaymentGateway error handling",
    "Review RefundProcessor test files",
    "Check cache invalidation logic in OrderRepository"
  ]
}
```

On resume, the coordinator loads this manifest and injects it into agent prompts. The agent picks up where it left off without repeating earlier exploration.

## Key Concept

Context degradation is not a token limit problem — it is the model losing grip on specific findings as verbose output accumulates. Scratchpad files persist key discoveries outside the context. Subagent delegation isolates verbose exploration. Crash recovery manifests prevent progress loss across sessions.

## Exam Traps

**Exam Trap:** Increasing the context window to solve context degradation

Context degradation is not about running out of tokens. It is about the model losing track of specific details as verbose output accumulates. A larger window still fills with verbose output.

**Exam Trap:** Assuming subagent delegation is only about parallelisation

The primary benefit of subagent delegation for codebase exploration is context isolation — keeping the main agent's context clean while subagents handle verbose exploration.

**Exam Trap:** Restarting a session to fix context degradation without saving state

Restarting loses all accumulated knowledge. Use scratchpad files and state manifests to persist findings before restarting, then inject them into the new session.

**Exam Trap:** Using /compact only when hitting context limits

/compact should be used proactively during extended sessions to maintain context quality, not just as a last resort when context is exhausted.
