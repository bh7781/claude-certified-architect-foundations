# Iterative Refinement Techniques

## What You Need to Know

Working with Claude Code is iterative. The first output is rarely the final one. The exam checks that you know the specific techniques for steering Claude Code toward the right result — and which one to reach for first in each situation.

## The Technique Hierarchy

Not all refinement techniques are equal. There's a clear pecking order:

**1. Concrete input/output examples** (most effective for inconsistent interpretation)

When you describe a code transformation in prose and Claude Code interprets it differently each time, the fix is not more prose. The fix is concrete examples.

Provide 2-3 examples showing the exact input and the exact expected output:

```text
Input:
  getUserData(userId: string): Promise<UserData>

Expected output:
  getUserData(userId: string): Promise<Result<UserData, ApiError>>
```

```text
Input:
  fetchOrders(customerId: string): Promise<Order[]>

Expected output:
  fetchOrders(customerId: string): Promise<Result<Order[], ApiError>>
```

The model generalises from these examples more reliably than from any prose description. Two or three concrete examples set the pattern, and the model applies it to new cases. This is the first technique to reach for when interpretation is inconsistent.

**2. Test-driven iteration** (most effective for complex transformations)

Write the tests first. Define the expected behaviour through test cases covering:

- Happy path (the standard expected transformation)
- Edge cases (null values, empty inputs, boundary conditions)
- Performance requirements (if applicable)

Then share the test failures with Claude Code. The failures give concrete, unambiguous feedback about what needs fixing. There's no room for interpretation when the test output says "Expected X, got Y."

```text
FAIL: testMigrationHandlesNullValues
  Expected: null preserved in output JSON
  Actual: null replaced with empty string ""
```

This failure message tells Claude Code exactly what to fix. No prose explanation needed.

**3. Interview pattern** (most effective for unfamiliar domains)

When you're working in a domain where you lack expertise, have Claude ask questions before implementing. This surfaces considerations you'd otherwise miss.

Instead of prescribing a solution:

"Build me a caching layer for the API"

Use the interview pattern:

"I need a caching layer for the API. Before implementing, ask me questions about the requirements, edge cases, and constraints I should consider."

Claude might ask about cache invalidation strategies, TTL policies, consistency requirements, and failure modes — considerations that an expert would know to address but that you might overlook.

## Key Concept

The interview pattern is for unfamiliar domains where the developer might miss important considerations. Concrete examples are for when the developer knows the exact transformation but the model interprets it inconsistently. Do not confuse the two — they solve different problems.

## Batch vs Sequential Feedback

How you deliver feedback matters. The rule:

**Single message (batch)** when fixes interact with each other:

If changing the error handling pattern also affects the logging format and the response structure, provide all three pieces of feedback in one message. The model needs to see all the interacting constraints at once to produce a coherent fix.

```text
Three changes needed (they interact with each other):
1. Error responses must include an error code field
2. Logging must include the error code in structured format
3. The client SDK type definitions must reflect the new error code field
```

**Sequential iteration** when issues are independent:

If the naming convention issue and the indentation issue don't affect each other, fix them one at a time. Batching independent issues can confuse the model about which feedback applies to which part of the code.

```text
First iteration: "Fix the function naming — use camelCase throughout"
[Wait for result]
Second iteration: "Now update the indentation to use 2 spaces"
```

## Example-Based Communication in Practice

When prose descriptions produce inconsistent results, the switch to examples follows a clear pattern:

- Observe inconsistency: You describe a transformation, Claude Code does it differently each time.
- Switch to examples: Provide 2-3 concrete before/after pairs showing the exact transformation.
- Verify generalisation: Test on a new case to confirm the model generalises the pattern correctly.
- Add edge case examples if needed: If the model handles the standard case but misses edge cases, add examples specifically showing edge case handling.

It's not about piling on more examples. Two or three well-chosen ones that cover the standard case and a key edge case are enough. The model generalises the pattern; you don't need to hand it every possible case.

## When Each Technique Applies

| Situation | Technique |
| --- | --- |
| Prose description interpreted differently each time | Concrete input/output examples |
| Complex transformation with many edge cases | Test-driven iteration |
| Working in an unfamiliar domain | Interview pattern |
| Multiple issues that affect each other | Batch feedback (one message) |
| Multiple independent issues | Sequential feedback |

## Exam Traps

**Exam Trap:** Choosing to refine prose descriptions when the model interprets them inconsistently

More precise prose still relies on interpretation. Concrete input/output examples eliminate interpretation ambiguity. The answer to inconsistent interpretation is always examples first, not better prose.

**Exam Trap:** Not recognising when to batch vs sequence feedback

If issues interact (fixing A affects B), provide all in one message so the model sees all constraints. If issues are independent, fix sequentially. The exam tests this distinction directly.

**Exam Trap:** Confusing the interview pattern with the examples technique

The interview pattern is for unfamiliar domains where you might miss considerations. Examples are for when you know the exact transformation but the model misinterprets it. Different problems, different solutions.
