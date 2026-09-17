# Implement Agent SDK Hooks for Normalisation and Policy Enforcement

## What You'll Learn

- The distinction between PostToolUse hooks (after execution, data normalisation) and PreToolUse hooks (before execution, policy enforcement)
- Why hooks provide deterministic guarantees that prompts cannot match
- How to normalise heterogeneous data formats from multiple MCP tools into a consistent schema
- How to implement threshold-based and prerequisite-based policy enforcement using pre-execution hooks
- The decision framework: hooks for 100% requirements, prompts for preferences

---

## Step 1: Create Tools with Heterogeneous Data Formats

Create an agent with three MCP tools that return data in different formats: Tool A returns Unix timestamps and numeric status codes, Tool B returns ISO 8601 dates and string statuses, Tool C returns DD/MM/YYYY dates and single-character status codes.

**Why:** This recreates the data format chaos example from the exam. Without normalisation, the model must interpret three different date formats and three different status representations, leading to inconsistent parsing across iterations.

**You should see:** Three tool implementations that each return data with distinct date and status formats. Tool A uses epoch seconds and numeric codes, Tool B uses ISO strings and English statuses, Tool C uses DD/MM/YYYY and single-character status codes.

### Nudge

Each tool should return a structured object with at least a date field and a status field, but in its own format.

### Guidance

Define three mock tool handlers that return objects with `created_at` and `status` fields, each using a different format convention for both fields.

### Starter Code

```javascript
function toolAHandler(): Record<string, unknown> {
  return { customer_id: "C-001", created_at: 1710489600, status: 200 };
}
function toolBHandler(): Record<string, unknown> {
  return { order_id: "ORD-42", created_at: "2024-03-15T12:00:00Z", status: "active" };
}
function toolCHandler(): Record<string, unknown> {
  return { shipment_id: "SHP-7", created_at: "15/03/2024", status: "S" };
}
```

---

## Step 2: Implement a PostToolUse Hook for Data Normalisation

Implement a PostToolUse hook that intercepts all tool results and normalises dates to ISO 8601 format and status codes to human-readable English strings.

**Why:** PostToolUse hooks run after execution but before the model processes the result. This is the correct hook direction for data normalisation — the exam tests whether you know that PostToolUse transforms data after execution, not before.

**You should see:** A HookCallback registered under PostToolUse that reads `tool_response` and rewrites it: Unix timestamps and DD/MM/YYYY dates to ISO 8601, numeric and single-character status codes to English strings. The rewritten object comes back as `updatedToolOutput` inside `hookSpecificOutput`.

### Nudge

A PostToolUse hook receives the result on the input object and replaces it by returning a new value. Which field carries the result, and which field replaces it?

### Guidance

The callback argument is a `PostToolUseHookInput`, so the result arrives as `tool_response`. To replace what the model sees, return `hookSpecificOutput` with `hookEventName` `PostToolUse` and `updatedToolOutput` set to your rewritten object. An empty object leaves the result alone. Register the callback under `PostToolUse` with a matcher for your MCP tools.

### Starter Code

```javascript
import { query, HookCallback, PostToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

const normaliseToolOutput: HookCallback = async (input) => {
  const post = input as PostToolUseHookInput;
  const result = post.tool_response as Record<string, unknown>;
  const normalised = { ...result };

  // Normalise dates
  if (typeof result.created_at === "number") {
    normalised.created_at = new Date(result.created_at * 1000).toISOString();
  } else if (typeof result.created_at === "string" && /^\d{2}\/\d{2}\/\d{4}$/.test(result.created_at)) {
    const [day, month, year] = result.created_at.split("/");
    normalised.created_at = new Date(`${year}-${month}-${day}`).toISOString();
  }

  // Normalise status
  const statusMap: Record<string, string> = { "200": "active", "404": "not_found", "S": "shipped", "P": "pending" };
  if (statusMap[String(result.status)]) {
    normalised.status = statusMap[String(result.status)];
  }

  return {
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      updatedToolOutput: normalised
    }
  };
};

// Register it. The matcher decides which tools the callback sees;
// MCP tool names follow the pattern mcp__<server>__<action>.
const options = {
  hooks: {
    PostToolUse: [{ matcher: "mcp__orders__.*", hooks: [normaliseToolOutput] }]
  }
};
```

---

## Step 3: Verify Consistent Data Normalisation

Verify the model receives consistent data by testing with queries that require results from all three tools.

**Why:** Consistent data eliminates interpretation errors. Without normalisation, the model might confuse day/month order in DD/MM/YYYY or misinterpret status code P as processed instead of pending. Verification proves the hook works across all tool outputs.

**You should see:** Three tool results that all use ISO 8601 dates and English status strings, whichever tool produced them. The model response should reference dates and statuses consistently.

### Nudge

Run a query that forces all three tools to be called, then check what the hook handed back.

### Guidance

Record the normalised object inside the normalising hook itself. Sibling PostToolUse hooks all receive the original `tool_response`, so a separate observer hook would log the raw value and tell you nothing.

### Starter Code

```javascript
const seen: Record<string, unknown>[] = [];

// Inside normaliseToolOutput, just before the return:
//   seen.push(normalised);

const testPrompt = "Look up customer C-001, find their order ORD-42, and check shipment SHP-7 status.";

for await (const message of query({ prompt: testPrompt, options })) {
  if (message.type === "result") break;
}

// Tool A: created_at should be "2024-03-15T12:00:00.000Z", not 1710489600
// Tool C: status should be "shipped", not "S"
console.log("All dates ISO 8601:", seen.every((o) => String(o.created_at).includes("T")));
console.log("All statuses readable:", seen.every((o) => typeof o.status === "string" && (o.status as string).length > 1));
```

---

## Step 4: Add a PreToolUse Hook for High-Value Refund Blocking

Add a PreToolUse hook that blocks `process_refund` when the amount exceeds $500 and redirects to a human escalation workflow.

**Why:** A PreToolUse hook runs before execution — the refund never processes. The exam specifically warns against using PostToolUse for blocking, because by that point the action has already occurred. Pre-execution interception is the only correct hook direction for policy enforcement.

**You should see:** A PreToolUse callback that inspects the refund amount and denies anything above $500, returning `permissionDecision` `deny` with a `permissionDecisionReason`. The refund tool never executes for denied calls.

### Nudge

Which hook direction blocks actions before they happen? What does the callback return to stop the call?

### Guidance

Use a PreToolUse hook. The arguments arrive as `tool_input` on a `PreToolUseHookInput`. To stop the call, return `hookSpecificOutput` with `hookEventName` `PreToolUse` and `permissionDecision` `deny`, plus a `permissionDecisionReason` so the model knows why and does not simply retry. Return an empty object to let the call through. Give the matcher the tool name so the callback does not have to check it.

### Starter Code

```javascript
import { HookCallback, PreToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

const blockLargeRefunds: HookCallback = async (input) => {
  const pre = input as PreToolUseHookInput;
  const toolInput = pre.tool_input as Record<string, unknown>;

  if ((toolInput.amount as number) > 500) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          "Refund exceeds the $500 threshold. Redirecting to the human escalation queue. Reference: ESC-" + Date.now()
      }
    };
  }

  // Empty object: no opinion, normal permission evaluation continues.
  return {};
};

// The matcher restricts the callback to the refund tool.
const hooks = {
  PreToolUse: [{ matcher: "mcp__payments__process_refund", hooks: [blockLargeRefunds] }]
};
```

---

## Step 5: Add a PreToolUse Hook for AML Compliance

Add a second PreToolUse hook that blocks `transfer_funds` until `aml_check` has returned a pass result in the current session.

**Why:** This is the AML compliance scenario from the exam. Prompt instructions achieve 95% compliance, but regulatory requirements demand 100%. The hook provides deterministic enforcement that no prompt can match — a single missed AML check can result in legal penalties.

**You should see:** Two callbacks: a PreToolUse hook on `transfer_funds` that denies until session state records a passing AML check, and a PostToolUse hook on `aml_check` that sets that state.

### Nudge

How do you track whether `aml_check` has passed? You need session-scoped state, and something has to write it.

### Guidance

Keep a module-scoped flag. A PostToolUse hook on `aml_check` reads `tool_response` and sets it on a pass; a PreToolUse hook on `transfer_funds` denies while it is false. Two matchers, two callbacks, one flag.

### Starter Code

```javascript
const amlState = { passed: false };

const requireAmlCheck: HookCallback = async () => {
  if (!amlState.passed) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          "COMPLIANCE BLOCK: International transfer requires AML verification. Run aml_check first."
      }
    };
  }
  return {};
};

const recordAmlResult: HookCallback = async (input) => {
  const post = input as PostToolUseHookInput;
  const result = post.tool_response as Record<string, unknown>;
  if (result.status === "pass") {
    amlState.passed = true;
  }
  return {};
};

// The matchers, not the callbacks, decide which tool each hook sees.
const hooks = {
  PreToolUse: [{ matcher: "mcp__banking__transfer_funds", hooks: [requireAmlCheck] }],
  PostToolUse: [{ matcher: "mcp__banking__aml_check", hooks: [recordAmlResult] }]
};
```

---

## Step 6: Test Both Hooks with Blocked and Allowed Operations

Test both hooks by attempting to trigger the blocked operations and verify they are prevented before execution.

**Why:** Testing confirms that the hooks provide deterministic enforcement. The key verification is that blocked tools never execute — the hook prevents the call, not just logs a warning after the fact.

**You should see:** Both denied operations leave their tool handlers untouched, and the model receives the `permissionDecisionReason`. Once the prerequisites are met, the same operations run.

### Nudge

Test the denied case and the allowed case for each hook. A deny stops the call, so there is no hook return value to assert on. What can you observe instead?

### Guidance

Count executions in the tool handlers themselves. If the PreToolUse hook did its job, the counter never moves. That is the whole point of blocking before execution rather than after.

### Starter Code

```javascript
// Increment these inside the process_refund and transfer_funds handlers.
let refundHandlerCalls = 0;
let transferHandlerCalls = 0;

// Test the refund threshold
await runAgent("Refund customer C-001 the sum of $750.");
console.log("Blocked high refund:", refundHandlerCalls === 0);

await runAgent("Refund customer C-001 the sum of $200.");
console.log("Allowed low refund:", refundHandlerCalls === 1);

// Test the AML prerequisite
await runAgent("Transfer $10000 to IBAN-123.");
console.log("Blocked without AML:", transferHandlerCalls === 0);

await runAgent("Run the AML check for C-001, then transfer $10000 to IBAN-123.");
console.log("Allowed after AML:", transferHandlerCalls === 1);
```