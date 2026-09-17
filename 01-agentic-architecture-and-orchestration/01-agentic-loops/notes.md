# Agentic Loops

## What You Need to Know

An agentic loop is the core execution cycle behind every Claude-based agent. It's deterministic control flow, defined in code. Not a prompt trick, not a retry loop, not a chatbot turn. Get this lifecycle right and most of Domain 1 falls into place; get it wrong and your agent stops halfway through a task in production.

---

## The Agentic Loop Lifecycle

The loop follows four steps, repeated until completion:

### Step 1: Send a Request to Claude

Send a request to Claude via the Messages API. This includes the conversation history (system prompt, prior messages, and any tool results from the previous iteration).

### Step 2: Inspect the stop_reason Field

Inspect the `stop_reason` field in the response. This field is the authoritative signal for what happens next. It has two values relevant to agentic loops:

- `"tool_use"` — Claude wants to call one or more tools. The loop continues.
- `"end_turn"` — Claude has finished its work. The loop terminates.

### Step 3: Execute Tools or Terminate

If `stop_reason` is `"tool_use"`: execute the requested tool(s), append the tool results to the conversation history as a new message, and send the updated conversation back to Claude.

If `stop_reason` is `"end_turn"`: the agent has finished. Present the final response to the user.

Step 3 is where loops break. Tool results must be appended to conversation history. Miss that, and Claude can't reason about the new information on the next iteration — the model never sees what the tool returned, so it has nothing new to act on.

### Key Concept

The `stop_reason` field is the only reliable signal for loop control. It is deterministic and unambiguous. Never use natural language parsing, text content checks, or arbitrary iteration caps as your primary stopping mechanism.

### Current State: Beyond the Two Exam Values

The exam guide (v1.0) keys `tool_use` and `end_turn`, the two values a basic loop branches on. The live Messages API returns others that a production loop must handle: `pause_turn` (continue a long-running server-tool turn), `max_tokens`, `stop_sequence`, `refusal` (current models such as Fable 5 can decline on an otherwise-normal 200 response), and `model_context_window_exceeded` (the response filled the model's context window; handle it like `max_tokens` truncation). Treat any value other than `end_turn` as "not finished, check why" rather than assuming `tool_use`. (Verified against the Messages API docs, July 2026.)

---

## Model-Driven Decision-Making

In an agentic loop, Claude decides which tool to call from the current context. That's model-driven decision-making — the model reads the task, weighs the available tools, and picks one. Compare that to pre-configured decision trees or fixed tool sequences, where the developer hard-codes which tool runs when.

The exam favours model-driven approaches because they flex. Claude adapts to situations the developer never mapped out, handles edge cases, and chains tools in orders nobody planned. There's one exception worth memorising: when business logic demands deterministic compliance — financial operations, security checks, regulatory requirements — programmatic enforcement overrides that flexibility. Task Statement 1.4 covers this in detail.

---

## The Three Anti-Patterns

Three anti-patterns show up again and again for loop termination. Learn to spot all three.

### Anti-Pattern 1: Parsing Natural Language Signals

Checking if Claude said "I'm done" or "task complete" to determine whether the loop should end. This is wrong because natural language is inherently ambiguous. Claude might say "I've finished analysing the first file" while intending to continue with more files. The `stop_reason` field exists precisely to eliminate this ambiguity.

### Anti-Pattern 2: Arbitrary Iteration Caps as Primary Control

Setting "stop after 10 loops" as the main way to terminate the agent. This is wrong because it either cuts off useful work (if the task genuinely needs 12 iterations) or runs unnecessary iterations (if the task finishes in 3). The model signals completion via `stop_reason` — use that signal. Iteration caps are acceptable as a safety net (a maximum bound to prevent runaway agents), but never as the primary control mechanism.

### Anti-Pattern 3: Checking for Assistant Text Content

Using `response.content[0].type == "text"` to decide the loop is finished. This is wrong because Claude can return text alongside tool_use blocks. A response might contain explanatory text ("I'll now search for the customer's order history") immediately followed by a tool call. Checking for text presence does not tell you whether the agent is finished.

### Common Exam Distractor

The exam frequently presents iteration caps as a plausible fix for premature termination. Reject these answers. Caps address runaway loops, not premature exits. The fix for premature termination is always to check `stop_reason` correctly.

---

## Practical Example: The Premature Termination Bug

A developer builds a customer support agent. It works for simple queries but sometimes stops mid-task on complex requests. The code checks if `response.content[0].type == "text"` to determine completion.

The bug: Claude returns a text explanation ("Let me look up your order") alongside a `tool_use` block requesting the `lookup_order` tool. The code sees text in position [0], concludes the agent is finished, and returns the incomplete response to the user.

The fix: replace the content-type check with a `stop_reason` check. Continue the loop when `stop_reason == "tool_use"`, terminate when `stop_reason == "end_turn"`. This works regardless of what content types appear in the response.

---

## Exam Traps

### Exam Trap 1

Using `response.content[0].type == 'text'` to determine loop completion

Claude can return text alongside `tool_use` blocks in the same response. Text presence does not indicate completion. The `stop_reason` field is the authoritative signal.

### Exam Trap 2

Setting arbitrary iteration caps (e.g., 'stop after 10 loops') as the primary stopping mechanism

Iteration caps either cut off useful work or run unnecessary iterations. They are acceptable as a safety net, not as the primary loop control. Use `stop_reason` instead.

### Exam Trap 3

Parsing natural language phrases like 'I'm done' or 'task complete' to decide loop termination

Natural language is ambiguous and unreliable. The `stop_reason` field provides a deterministic, unambiguous signal for loop control.

### Exam Trap 4

Forcing `tool_choice` to 'any' to prevent the agent from returning text

This forces tool use even when the agent is genuinely finished, creating an infinite loop. The correct approach is to let the model signal completion naturally via `stop_reason`.