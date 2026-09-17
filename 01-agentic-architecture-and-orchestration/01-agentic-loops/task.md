# Build a Multi-Tool Agent Loop

**Difficulty:** 45 minutes

## What You'll Learn

- How the agentic loop lifecycle works with the Messages API
- Why `stop_reason` is the authoritative signal for loop control
- How to handle `tool_use` and `end_turn` stop_reason values correctly
- How to append tool results to conversation history for multi-turn execution
- When safety iteration caps are appropriate versus inappropriate as stopping mechanisms

---

## Step 1: Set Up a Claude API Client with Two Tools

Set up a Claude API client with two tools: a calculator tool (accepts `expression`, returns `result`) and a web search stub (accepts `query`, returns mock results).

**Why:** Multi-tool setups expose model-driven decision-making — Claude must select the right tool based on context, which is core to agentic architecture.

**You should see:** Two tool definitions registered with proper JSON Schema `input_schema`, each with `name`, `description`, and `parameters`.

### Nudge

Think about what the Anthropic SDK requires for a tool definition — name, description, and what kind of schema format?

### Guidance

Each tool needs a `name` (string), `description` (string), and `input_schema` (JSON Schema object with `type`, `properties`, and `required`). The calculator takes an `expression` string; the web search takes a `query` string.

### Starter Code

```javascript
const tools = [
  {
    name: "calculator",
    description: "Evaluates a mathematical expression",
    input_schema: {
      type: "object",
      properties: { expression: { type: "string" } },
      required: ["expression"]
    }
  }
];
```

---

## Step 2: Implement the Agentic Loop

Implement the agentic loop that sends requests to Claude and inspects `stop_reason` after each response.

**Why:** The agentic loop is the core execution pattern — the exam tests whether you use `stop_reason` (deterministic) versus content-type checks or natural language parsing (unreliable).

**You should see:** A `while` loop that calls `client.messages.create()` and checks `response.stop_reason` after each iteration.

### Nudge

What field in the API response tells you definitively whether Claude wants to keep going or is done?

### Guidance

Use a `while(true)` loop. After each `messages.create()` call, check `response.stop_reason`. If it is `tool_use`, continue. If it is `end_turn`, break. Never check `content[0].type`.

### Starter Code

```javascript
let messages = [{ role: "user", content: userPrompt }];
while (true) {
  const response = await client.messages.create({
    model: "claude-sonnet-5",
    max_tokens: 1024,
    tools,
    messages
  });
  if (response.stop_reason === "end_turn") break;
  // Handle tool_use next
}
```

---

## Step 3: Handle the `tool_use` Stop Reason

Handle the `tool_use` stop_reason by executing the requested tool, creating a tool result message, and appending it to conversation history.

**Why:** This is the critical handoff in the loop — the exam specifically tests whether you correctly extract tool calls, execute them, and return results in the right message format.

**You should see:** When Claude requests a tool, your code extracts the `tool_use` block, runs the corresponding function, and appends both the assistant response and a user message with `tool_result` to the conversation.

### Nudge

Claude's response contains content blocks. Which block type tells you what tool to call and with what input?

### Guidance

Find content blocks where `type === "tool_use"`. Each has an `id`, `name`, and `input`. Execute the matching function, then create a user message with a `tool_result` content block containing the `tool_use_id` and the result string.

### Starter Code

```javascript
const toolUse = response.content.find(b => b.type === "tool_use");
const result = executeTool(toolUse.name, toolUse.input);
messages.push({ role: "assistant", content: response.content });
messages.push({
  role: "user",
  content: [{ type: "tool_result", tool_use_id: toolUse.id, content: result }]
});
```

---

## Step 4: Handle the `end_turn` Stop Reason

Handle the `end_turn` stop_reason by extracting and returning the final response.

**Why:** `end_turn` is Claude's signal that it has completed the task — extracting the final text response correctly closes the loop and returns the result to the user.

**You should see:** When `stop_reason` is `end_turn`, your loop exits and returns the text content from the final response.

### Nudge

Where in the response object is the final text that Claude wants to show the user?

### Guidance

Filter `response.content` for blocks where `type === "text"`. The `text` property of those blocks contains Claude's final answer.

### Starter Code

```javascript
if (response.stop_reason === "end_turn") {
  const textBlock = response.content.find(b => b.type === "text");
  return textBlock?.text ?? "";
}
```

---

## Step 5: Test with Sequential Tool Calls

Test with a prompt that requires multiple sequential tool calls (e.g., search for a value then calculate something with it) and verify the loop continues correctly through all iterations.

**Why:** Sequential tool calls test the full loop lifecycle — the agent must complete one tool call, receive the result, reason about it, and decide to call another tool before finally returning.

**You should see:** At least two tool call iterations before `end_turn`. The agent searches first, uses the search result in a calculation, then returns the combined answer.

### Nudge

Design a prompt where the answer to the first tool call is needed as input for the second. What kind of query would force this chain?

### Guidance

Try a prompt like: *"Search for the population of France and calculate what 15% of that number is."* This forces a search call followed by a calculator call using the search result.

### Starter Code

```javascript
const result = await runAgentLoop(
  "Search for the current price of Bitcoin and calculate what 3.5 coins would cost"
);
console.log("Iterations:", iterationCount);
console.log("Result:", result);
```

---

## Step 6: Add a Safety Iteration Cap

Add a safety iteration cap of 20 as a maximum bound (not the primary stopping mechanism) and log a warning if it triggers.

**Why:** The exam distinguishes safety caps (acceptable as a fallback) from using caps as the primary stopping mechanism (an anti-pattern). Your cap should never trigger in normal operation.

**You should see:** A `MAX_ITERATIONS` constant, a counter that increments each loop, and a warning log if the cap is hit. Normal queries should terminate via `stop_reason` well before reaching 20.

### Nudge

Where in your loop should you check the counter? What should happen if it triggers — error or warning?

### Guidance

Add a counter variable before the loop. Increment at the start of each iteration. If `counter >= MAX_ITERATIONS`, log a warning and break. This is a safety net, not the primary control.

### Starter Code

```javascript
const MAX_ITERATIONS = 20;
let iterations = 0;
while (true) {
  if (iterations >= MAX_ITERATIONS) {
    console.warn("Safety cap reached");
    break;
  }
  iterations++;
  // ... rest of loop
}
```