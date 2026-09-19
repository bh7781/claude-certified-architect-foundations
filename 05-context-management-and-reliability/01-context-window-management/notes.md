# Context Window Management

## What You Need to Know

Context window management is the foundation of reliable Claude-based systems. Every multi-turn conversation, every multi-agent pipeline, every long-document extraction task depends on what you let into the context window. Get it wrong and the failures are concrete: your support agent forgets refund amounts, your research pipeline drops citations, your extraction system loses precision on the fields that matter most.

## The Progressive Summarisation Trap

When conversations grow long, a common strategy is to summarise earlier turns to free up token budget. This is a trap. Progressive summarisation systematically destroys the most critical information in customer-facing and data-processing systems: numerical values, dates, percentages, and customer-stated expectations.

Here is how it plays out. A customer contacts support about a refund:

```text
Turn 3: "I'd like a refund of $247.83 for order #8891 placed on March 3rd"
```

After summarisation, this becomes:

```text
Summary: "Customer wants a refund for a recent order"
```

The amount, order number, and date — the three facts the agent needs to process the refund — are gone. And that is not a fringe case. It is what summarisation does to transactional data by default.

The fix: persistent case facts blocks. Extract transactional facts (amounts, dates, order numbers, statuses) into a structured block that is included in every prompt, outside the summarised history. This block is never summarised. It persists across every turn regardless of what happens to the conversation history.

```json
{
  "caseFactsBlock": {
    "customerId": "C-4421",
    "issues": [
      {
        "orderId": "#8891",
        "orderDate": "2024-03-03",
        "refundAmount": "$247.83",
        "status": "pending_refund",
        "itemDescription": "Wireless headphones — defective"
      }
    ]
  }
}
```

For multi-issue sessions where a customer raises several problems in one conversation, extract and persist structured issue data into a separate context layer. Each issue gets its own entry with order IDs, amounts, and statuses. This prevents cross-contamination between issues during summarisation.

## The "Lost in the Middle" Effect

Models process information at the beginning and end of long inputs reliably. Findings buried in the middle of a long context may be missed or given less weight. This is a well-documented phenomenon in large language models and it directly affects how you structure aggregated inputs.

The fix is structural, not prompt-based. Place key findings summaries at the beginning of aggregated inputs. Organise detailed results with explicit section headers throughout. If you are feeding a synthesis agent the output of three research subagents, start with a "Key Findings Summary" section, then provide the detailed outputs with clear section boundaries.

```text
## Key Findings Summary
- Source A: 12% market growth in renewable sector (2023)
- Source B: Patent filings increased 34% year-on-year
- Source C: Regulatory framework delayed until Q3 2025

## Detailed Findings

### Source A: Market Analysis Report
[Full details here...]

### Source B: Patent Database Analysis
[Full details here...]

### Source C: Regulatory Review
[Full details here...]
```

## Tool Result Trimming

Tool results are a silent context budget killer. An order lookup might return 40+ fields: internal audit timestamps, warehouse codes, shipping carrier IDs, fulfilment centre identifiers, and dozens of other fields irrelevant to the customer's refund request. You need 5 fields. Those other 35 fields consume tokens in every subsequent turn as the conversation history grows.

Trim verbose tool outputs to only relevant fields before they accumulate in context. Skip it and multi-turn systems slowly drown in stale tool output. It is not a nice-to-have.

```python
def trim_order_result(raw_result, relevant_fields=None):
    if relevant_fields is None:
        relevant_fields = [
            "order_id", "order_date", "total_amount",
            "return_eligible", "item_description"
        ]
    return {k: v for k, v in raw_result.items() if k in relevant_fields}
```

This trimming should happen in a PostToolUse hook or in the tool implementation itself, before the result enters the conversation history. Once verbose data is in the context, it stays there for every subsequent turn.

## Full Conversation History

The Claude API is stateless. Each request must include the complete conversation history. Omit earlier messages and the model loses conversational coherence. There's no session state on the server side, so every turn has to carry everything the model needs to follow the conversation.

This creates a tension with context limits: you need the full history for coherence, but the history grows with every turn. The persistent case facts block resolves this by separating critical facts from summarisable narrative, letting you summarise the conversation flow while preserving every transactional detail.

## Upstream Agent Optimisation

In multi-agent systems, upstream agents often return verbose reasoning chains and raw content that downstream agents do not need. When a research subagent sends its full thought process to a synthesis agent with a limited context budget, the synthesis agent wastes tokens on reasoning it cannot use.

Modify upstream agents to return structured data — key facts, citations, relevance scores — instead of verbose content and reasoning chains. Require subagents to include metadata (dates, source locations, methodological context) in structured outputs to support accurate downstream synthesis.

```json
{
  "findings": [
    {
      "claim": "Renewable energy investment grew 12% in 2023",
      "source": "IEA World Energy Report 2024",
      "sourceUrl": "https://example.com/report",
      "relevanceScore": 0.92,
      "publicationDate": "2024-01-15"
    }
  ]
}
```

Tokens aren't the only win here. Structured outputs from upstream agents let downstream agents process findings without re-parsing verbose prose.

## Key Concept

The persistent case facts block is the single most important pattern in context window management. Extract transactional facts (amounts, dates, order numbers) into a structured block that is included in every prompt and never summarised. This is the fix for progressive summarisation and the foundation for reliable multi-turn systems.

## Prompt Caching

Prompt caching is the other half of context economics. Instead of trimming what the model sees, you avoid paying to reprocess the parts that don't change. Mark a stable prefix with a cache_control breakpoint and the API stores that processed prefix, then reuses it on the next request, charging a fraction of the input cost for the cached tokens.

Caching matches from the start of the prompt, prefix by prefix, so layout decides whether you get a hit. Put the content that stays constant first: system instructions, tool definitions, long reference documents. Place the cache_control breakpoint at the end of that static block. Put the volatile content, the user's latest message and anything that changes per request, after the breakpoint.

The static block belongs in the top-level system parameter, not in messages. There is no "system" role for input messages in the Messages API — messages takes "user" and "assistant" turns only.

```python
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=4096,
    system=[
        {"type": "text", "text": LONG_STATIC_INSTRUCTIONS},
        {"type": "text", "text": REFERENCE_DOC,
         "cache_control": {"type": "ephemeral"}},
    ],
    messages=[
        {"role": "user", "content": dynamic_user_message},
    ],
)
```

Get the order wrong and you lose the benefit entirely. If dynamic content sits before the static block, the prefix changes on every request, nothing matches, and every call pays full price. An ephemeral breakpoint lasts about five minutes since last use; a {"type": "ephemeral", "ttl": "1h"} breakpoint lasts an hour at a higher write cost. A request may carry at most four breakpoints.

## Scope

The guide's out-of-scope list excludes "prompt caching implementation details (beyond knowing it exists)", so nothing beyond the existence and purpose of caching is tested. The mechanics above are here for real work, not for the exam.

## Exam Traps

**Exam Trap:** Thinking progressive summarisation is safe for transactional data

Summarisation systematically destroys numerical values, dates, and specific identifiers. A persistent case facts block must hold these outside summarised history.

**Exam Trap:** Assuming the 'lost in the middle' effect is solved by telling the model to pay attention to everything

The fix is structural: place key findings at the beginning of inputs and use explicit section headers. Prompt-based reminders are unreliable for position effects.

**Exam Trap:** Keeping full tool results in context because 'the model might need them later'

Untrimmed tool results from 40+ field lookups exhaust the token budget across turns. Trim to relevant fields before results enter the conversation history.

**Exam Trap:** Believing conversation history can be selectively truncated without consequences

The API is stateless. Each request needs complete conversation history. Selective truncation breaks conversational coherence. Use case facts blocks and summarisation instead of truncation.
