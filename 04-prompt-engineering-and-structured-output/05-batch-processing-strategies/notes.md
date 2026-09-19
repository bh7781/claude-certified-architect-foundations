# Batch Processing Strategies

## What You Need to Know

The Message Batches API is a cost optimisation tool with hard constraints that the exam tests directly. Understanding when to use it — and when not to — is the core of this task statement.

## Message Batches API: The Facts

The constraints are fixed, and you have to design around them:

- 50% cost savings compared to synchronous API calls
- Up to 24-hour processing window — results may arrive in minutes or take up to 24 hours
- No guaranteed latency SLA — you cannot rely on results arriving within any specific timeframe
- No multi-turn tool calling within a single batch request — the model cannot execute tools mid-request and use the results to continue processing
- custom_id fields for correlating request/response pairs — each request in a batch gets a unique identifier used to match it with its response

## The Matching Rule

This is the single most tested concept from this task statement:

**Synchronous API:** For blocking workflows where someone or something is waiting for the result. Pre-merge checks in CI/CD, real-time code review feedback, any workflow where developers are blocked pending completion.

**Batch API:** For latency-tolerant workflows where results are consumed later. Overnight technical debt reports, weekly code audit summaries, nightly test generation runs, batch document extraction.

The exam specifically presents a scenario (Question 11 in the sample questions) where a manager proposes switching everything to batch processing for the cost savings. The correct answer keeps blocking workflows synchronous and only moves latency-tolerant workflows to batch.

```typescript
// Synchronous — developer is waiting for this
const preMergeReview = await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 4096,
  messages: [{ role: "user", content: prDiffContent }]
});

// Batch — results consumed tomorrow morning
const batchRequest = await client.messages.batches.create({
  requests: technicalDebtDocuments.map((doc, i) => ({
    custom_id: `debt-report-${i}`,
    params: {
      model: "claude-sonnet-5",
      max_tokens: 4096,
      messages: [{ role: "user", content: doc }]
    }
  }))
});
```

## SLA Calculation

When designing batch processing schedules, you must account for the 24-hour maximum processing window. If your organisation requires a 30-hour SLA for a report:

- The 24 hours is a maximum window, not a delivery guarantee. A batch that does not finish inside it comes back expired, so size the schedule against that worst case and treat an expired batch as a resubmission
- 30 hours total SLA minus the 24-hour worst case = 6 hours of buffer for collecting requests, validating inputs, or absorbing operational delays
- Submit batches every 4 hours within that buffer window so a fresh batch is always in flight. A 6-hour cadence leaves no margin at all

The exam may present a scheduling question where you need to work backwards from the SLA to determine submission frequency.

## Batch Failure Handling

Not all documents in a batch succeed. The correct failure handling pattern has three steps:

**1. Identify failures by custom_id.** Each request has a unique identifier. Parse the batch results to find which custom_id values failed.

**2. Resubmit only failures with modifications.** Do not resubmit the entire batch. Common modifications include:

- Chunking oversized documents that exceeded context limits
- Simplifying extraction prompts for documents with unusual structures
- Adding format-specific few-shot examples for documents that failed due to structural variety

**3. Refine prompts on a sample set BEFORE batch processing.** This is the proactive step that maximises first-pass success and reduces resubmission costs. Test your prompts against a representative sample (5-10 documents covering the range of formats and edge cases) before processing the full batch.

```typescript
// Poll until the batch has finished before reading results
let batch = await client.messages.batches.retrieve(batchId);
while (batch.processing_status !== "ended") {
  await new Promise(r => setTimeout(r, 60_000));
  batch = await client.messages.batches.retrieve(batchId);
}

// results() returns a JSONL async iterable, not an array — accumulate it.
// Treat `expired` as a failure too: that is what an overrun batch returns.
const failedIds: string[] = [];
for await (const result of client.messages.batches.results(batchId)) {
  if (result.result.type === "errored" || result.result.type === "expired") {
    failedIds.push(result.custom_id);
  }
}

// Resubmit only failures with modifications
const retryRequests = failedIds.map(id => {
  const originalDoc = documentsById[id];
  return {
    custom_id: `${id}-retry-1`,
    params: {
      model: "claude-sonnet-5",
      max_tokens: 8192,  // increased for oversized docs
      messages: [{
        role: "user",
        content: chunkIfNeeded(originalDoc)
      }]
    }
  };
});
```

## Multi-Turn Tool Calling Limitation

The batch API doesn't support multi-turn tool calling within a single request. This means you cannot:

- Define tools and have the model call them mid-request
- Process tool results and continue the conversation within the same batch item
- Run agentic loops within a single batch request

If your workflow requires tool execution mid-processing, you must use the synchronous API. This limitation is a direct exam test point — if a scenario describes a batch workflow that needs to call external tools during processing, the correct answer is to use the synchronous API for that step.

## Current state

Exam guide v1.0 states the limitation exactly as above, and that is the keyed answer. Anthropic's batch processing docs (checked September 2026) now split it by tool type. Server tools (web search, web fetch, code execution, MCP connectors, tool search) run the same server-side agentic loop inside a batch request as they do synchronously, and a batch result can come back with stop_reason: "pause_turn" for you to continue in a follow-up request. Client tools, the ones your own code executes, still cannot complete a loop inside a batch item: the request ends at tool_use, you run the tool after retrieving the result, then submit a follow-up request. When a question names a tool your own code runs (an internal lookup, a database query), the guide's rule and the current docs give the same answer. On the exam, answer per the guide: no multi-turn tool calling in a batch request, so a step that needs tool execution mid-processing runs on the synchronous API.

## Key Concept

The Message Batches API provides 50% cost savings with an up to 24-hour processing window and no latency SLA. Use it only for latency-tolerant workflows (overnight reports, weekly audits). Blocking workflows (pre-merge checks) must remain synchronous. Always refine prompts on a sample set before submitting large batches.

## Prompt Optimisation Before Batch Submission

The most cost-effective batch processing strategy is to invest time in prompt refinement before submitting large volumes:

- Sample set testing: Take 5-10 representative documents covering the range of formats, edge cases, and document types in your batch
- Iterate on the sample: Refine your extraction prompts, add few-shot examples, adjust schema design until the sample set achieves high accuracy
- Submit the full batch: With refined prompts, your first-pass success rate will be significantly higher
- Handle failures: Resubmit only the failed documents with targeted modifications

This workflow slashes total cost. A 90% first-pass success rate on 1,000 documents means only 100 retries. A 60% first-pass rate means 400 retries, four times the resubmission cost, plus the batch processing cost for those retries.

## Exam Traps

**Exam Trap:** Switching all workflows to batch processing for cost savings

Blocking workflows where developers wait for results (pre-merge checks, real-time reviews) must remain synchronous. The batch API has no guaranteed latency SLA and can take up to 24 hours. Only latency-tolerant workflows should use batch.

**Exam Trap:** Assuming batch results arrive quickly because they often do

The batch API has no latency SLA. Results often arrive faster than 24 hours, but you cannot design blocking workflows around best-case timing. Design around the 24-hour maximum.

**Exam Trap:** Using batch API for workflows requiring multi-turn tool calling

The batch API does not support multi-turn tool calling within a single request. If your workflow needs to execute tools and use results mid-processing, you must use the synchronous API.
