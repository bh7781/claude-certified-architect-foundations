# Tool Distribution & Tool Choice

## What You Need to Know

The number of tools you give an agent directly affects how reliably it selects the right one. That sounds like an implementation detail. It isn't — it's an architectural decision that determines whether your multi-agent system works in production.

## The Tool Overload Problem

Giving a single agent 18 tools degrades selection reliability. Every additional tool adds decision complexity, and error rates climb as the toolkit grows. The optimal range is 4-5 tools per agent, scoped to that agent's specific role.

Quantity isn't the whole story, though — relevance matters just as much. A synthesis agent should NOT have web search tools. A web search agent should NOT have document analysis tools. Give an agent tools outside its specialisation and it will tend to misuse them: a synthesis agent with access to web_search might run its own searches instead of using the results already handed to it, duplicating work and wasting context.

The principle: each agent gets only the tools it needs for its defined role. Nothing more.

## Consolidating Near-Duplicate Tools

Splitting by role is the obvious answer to tool overload. It's the wrong one when the tools all do the same kind of work.

Take a data platform server with 22 tools: three query tools, one per data source, and 19 transformations — pivot_table, calculate_percentile, normalise_currency, on down the list. Split that by role and you hand a transformation agent 19 tools, which is the original problem moved one level down. The agent still can't choose reliably.

Those 19 collapse instead, because they share a shape. Data in, an operation, data out:

```json
{
  "name": "transform_data",
  "description": "Apply a transformation to a dataset. Use transform_type to select the operation.",
  "input_schema": {
    "type": "object",
    "properties": {
      "dataset": { "type": "string" },
      "transform_type": {
        "type": "string",
        "enum": ["pivot", "percentile", "normalise_currency", "..."]
      },
      "options": { "type": "object" }
    },
    "required": ["dataset", "transform_type"]
  }
}
```

Twenty-two tools become four. Nothing is lost: every transformation is still reachable, now as an enum value the model picks inside a single call rather than a tool it has to find among nineteen near-identical descriptions. Selection accuracy improves because the hard choice got smaller, not because the capability did.

So which fix applies?

| The tools are... | The fix |
|---|---|
| Few enough to handle, but two of them read alike | Sharpen the descriptions (Task Statement 2.1) |
| Different jobs (query, transform, export) | Split by role, 4-5 tools each |
| Variations on one job, sharing a shape | Consolidate into one parameterised tool |
| Doing more than the agent should be able to do | Constrain them (next section) |

The first row is the one candidates trip on. Task Statement 2.1 teaches descriptions as the fix for misrouting, and it is right when the toolkit is small enough to reason about. An agent choosing get_customer over lookup_order from a set of five is a description problem. The same symptom from a set of 22 is not: the agent is past the point where any description quality rescues selection, and rewriting all 22 leaves the decision complexity exactly where it was. Same symptom, different disease. Count the tools before you pick the remedy.

Watch the third row: it pulls the other way, and the exam likes that tension. Consolidation reduces how many tools an agent chooses between. Constraining reduces what any one tool can reach. Collapsing 19 transformations into transform_data doesn't hand the agent new powers, so it doesn't undo least privilege. Replacing fetch_url with load_document does the opposite job and both can be right in the same system.

One fix that isn't a fix: moving tools onto a second MCP server. Server boundaries are invisible to the model. A client hands it every tool from every connected server as one flat list, so a 22-tool problem split across two servers is still a 22-tool problem.

## The tool_choice Configuration

The tool_choice parameter controls how the model interacts with available tools. Three settings, three distinct jobs.

**"auto" (default)**
The model decides whether to call a tool or return text. Use this for general operation where the model needs flexibility to respond conversationally when no tool call is appropriate.

```json
{
  "tool_choice": { "type": "auto" }
}
```

**"any"**
The model MUST call a tool but chooses which one. Use this when you need guaranteed structured output from one of multiple schemas — the model will always produce a tool call, never plain text.

```json
{
  "tool_choice": { "type": "any" }
}
```

Extraction pipelines are where this earns its keep. If you have multiple extraction schemas (one for invoices, one for receipts, one for contracts) and the document type is unknown, "any" guarantees the model picks one and produces structured output rather than returning a conversational response.

**Forced selection**
The model MUST call a specific named tool. Use this to enforce mandatory first steps — the model cannot skip or reorder the required operation.

```json
{
  "tool_choice": { "type": "tool", "name": "extract_metadata" }
}
```

This is the tool for enforcing workflow ordering. If metadata extraction must happen before any enrichment tools run, forced selection guarantees it. The model can't decide to skip extract_metadata and jump straight to enrichment. After the forced call completes, subsequent turns can use "auto" for the remaining steps.

## Scoped Cross-Role Tools

Sometimes an agent needs occasional access to a capability that belongs to another role. The naive approach is to route every such request through the coordinator. The problem: this adds 2-3 round trips per request and can increase latency by 40% or more.

The solution is a scoped cross-role tool: a constrained version of the capability, given directly to the agent that needs it.

Say a synthesis agent needs to verify simple facts constantly during report generation. The naive design routes every verification back to the coordinator, which delegates to the search agent, waits for results, and returns them. For 85% of verifications — simple lookups that take milliseconds — that round trip is pure waste.

The fix: give the synthesis agent a scoped verify_fact tool that handles simple lookups directly. Complex verifications (requiring multiple sources, cross-referencing, or real judgement) still route through the coordinator. The 85% simple case is handled locally; the 15% complex case uses the full pipeline.

The exam guide's sample Question 9 tests this pattern directly.

## Replacing Generic Tools with Constrained Alternatives

Instead of giving a subagent fetch_url (which can fetch anything from anywhere), give it load_document that validates document URLs only. The constrained tool:

- Prevents misuse (the agent cannot fetch arbitrary URLs)
- Makes the tool's purpose clearer (the description is specific, not generic)
- Reduces the risk of unintended side effects (no fetching of non-document resources)

This is least privilege applied to tool design. Each tool does exactly what the agent needs and nothing more.

## Role-Specific Tool Scoping in Practice

Here is how tool distribution looks in a well-designed multi-agent research system:

| Agent | Tools (4-5 each) |
|---|---|
| Web Search | search_web, fetch_page, extract_links, save_snippet |
| Document Analysis | extract_metadata, extract_data_points, summarize_content, verify_claim |
| Synthesis | compile_report, verify_fact (scoped), format_citation, assess_coverage |
| Coordinator | Agent (formerly Task, used to spawn subagents), review_output, request_revision |

Each agent has exactly the tools it needs. The synthesis agent has a scoped verify_fact for simple lookups. The coordinator runs the workflow without holding any domain-specific tools itself.

**Key Concept**

The optimal range is 4-5 tools per agent, scoped to its role. For high-frequency simple operations, add a scoped cross-role tool directly to the agent that needs it — this avoids coordinator round-trip latency for the common case.

## Exam Traps

**Exam Trap**

Routing all simple verification requests through the coordinator when 85% are simple lookups

Coordinator round-trips add 2-3 extra hops per request. A scoped verify_fact tool on the synthesis agent handles the 85% simple case directly, cutting latency by up to 40%.

**Exam Trap**

Using tool_choice 'auto' when structured output is required

With 'auto', the model may return conversational text instead of calling a tool. Use 'any' to guarantee a tool call, or forced selection to guarantee a specific tool call.

**Exam Trap**

Giving an agent 18 tools and expecting reliable selection

Tool selection reliability degrades as the number of tools increases. The optimal range is 4-5 tools per agent. More tools means more decision complexity and more selection errors.

**Exam Trap**

Giving a subagent a generic fetch_url tool when a constrained load_document would suffice

Generic tools enable misuse. Constrained alternatives (load_document that validates document URLs only) enforce the principle of least privilege and make the tool's purpose clearer.