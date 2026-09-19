# Multi-Instance and Multi-Pass Review

## What You Need to Know

When Claude reviews its own output, it starts at a disadvantage: it still carries the reasoning it used to generate that output. The model remembers why it made each decision and is less likely to question it. That's not a bug. It's just how self-review works inside a single session. The job is to design around it.

## The Self-Review Limitation

A model reviewing its own output in the same conversation session retains its original reasoning chain. It already "knows" why it chose each approach, classified each finding at a particular severity, or selected certain values. When asked to review, it tends to confirm rather than challenge those decisions.

An independent instance — a separate Claude invocation without the prior reasoning context — approaches the output fresh. It judges the code, findings, or extraction on what it sees alone, without the bias of "I chose this because..." That's what makes independent review so much better at catching subtle issues.

The exam tests this directly. When presented with options for improving review quality, the correct answer involves using a separate model instance, not adding "please review carefully" instructions to the same session or relying on extended thinking within the generating session.

```typescript
// Anti-pattern: self-review in the same session
const generation = await client.messages.create({
  messages: [
    { role: "user", content: "Write a function to process orders" },
    { role: "assistant", content: generatedCode },
    { role: "user", content: "Now review your code for bugs" }
    // Model retains its reasoning — less likely to find its own mistakes
  ]
});

// Correct: independent review instance
const review = await client.messages.create({
  messages: [
    {
      role: "user",
      content: `Review this code for bugs, security issues, and edge cases:\n\n${generatedCode}`
    }
    // Fresh instance — no prior reasoning context
  ]
});
```

## Multi-Pass Review Architecture

Large reviews (multi-file PRs, complex extraction pipelines, broad code audits) suffer from attention dilution when processed in a single pass. The symptoms are specific and recognisable:

- Detailed feedback on some files, superficial comments on others
- Obvious bugs missed in the middle of the review
- Contradictory findings — flagging a pattern as problematic in one file while approving identical code elsewhere

The fix is to split the review into focused passes:

**Pass 1: Per-file local analysis.** Analyse each file individually with a focused review prompt. This ensures consistent depth across all files. Each invocation examines only one file, so the model gives it full attention.

**Pass 2: Cross-file integration.** After all per-file analyses are complete, run a separate pass that receives all per-file findings and checks for cross-file issues: data flow between modules, consistent API usage across services, dependency conflicts, and contradictions in the per-file findings themselves.

```typescript
// Pass 1: Per-file analysis
const perFileFindings = await Promise.all(
  files.map(file =>
    client.messages.create({
      messages: [{
        role: "user",
        content: `Review this file for local issues (bugs, security, logic errors):\n\n${file.content}`
      }]
    })
  )
);

// Pass 2: Cross-file integration
const integrationReview = await client.messages.create({
  messages: [{
    role: "user",
    content: `Given these per-file findings, identify cross-file issues:\n` +
      `- Data flow inconsistencies between modules\n` +
      `- Contradictory patterns flagged in different files\n` +
      `- API contract violations across service boundaries\n\n` +
      `Findings:\n${JSON.stringify(perFileFindings)}`
  }]
});
```

This architecture directly addresses the three symptoms of attention dilution. Per-file passes ensure consistent depth. The integration pass catches cross-file issues that no single-file review would identify. And the separation prevents contradictory findings from appearing in the same output.

## Why Larger Context Windows Do Not Fix This

The exam includes a specific distractor: "switch to a higher-tier model with a larger context window." This sounds reasonable — if the model can't handle 14 files at once, give it more capacity. But the problem isn't context size. It's attention quality. A bigger context window won't stop the model from spreading its attention unevenly across files. Only focused, per-file passes ensure consistent depth.

## Confidence-Based Routing

For findings that are uncertain, the model can self-report confidence alongside each finding. This enables a routing strategy:

- High confidence findings: Report directly to developers
- Low confidence findings: Route to human review for validation
- Threshold calibration: Use labelled validation sets to calibrate what confidence score correlates with actual accuracy

```json
{
  "finding": "Potential race condition in order processing",
  "severity": "major",
  "confidence": 0.65,
  "reasoning": "The lock acquisition pattern appears correct but the unlock timing depends on an async callback whose ordering I cannot fully verify.",
  "route": "human_review"
}
```

The confidence score isn't self-reported accuracy. It's the model's read on its own certainty. Calibrate it by running labelled examples (where you already know the answer) through the system and measuring how reported confidence tracks actual accuracy. Then adjust routing thresholds from that data.

The exam distinguishes between raw confidence scores (uncalibrated, unreliable for automated decisions) and calibrated confidence thresholds (validated against labelled sets, suitable for routing). Using uncalibrated confidence for automated decisions is an anti-pattern.

## Key Concept

A model reviewing its own output in the same session retains reasoning context and is less likely to question its decisions. Use independent instances for review. Split large reviews into per-file local passes plus a cross-file integration pass to prevent attention dilution. Calibrate confidence thresholds using labelled validation sets before using them for routing.

## Putting It All Together

A production review architecture combines all three concepts:

- Generation: First instance generates code, extraction, or analysis
- Per-file review: Independent instances review each output unit individually
- Integration review: Separate instance checks cross-unit consistency
- Confidence routing: Low-confidence findings go to human review
- Calibration loop: Labelled validation sets continuously calibrate confidence thresholds

This architecture is more expensive than single-pass review. The trade-off is worth it when review quality directly affects production reliability — CI/CD pipelines, financial extraction, compliance analysis, and any system where missed issues have downstream consequences.

## Exam Traps

**Exam Trap:** Choosing self-review in the same session as a viable review strategy

The model retains its reasoning context from generation and is less likely to question its own decisions. An independent instance without prior context is significantly more effective at catching subtle issues.

**Exam Trap:** Using a single pass for large multi-file reviews

Single-pass multi-file reviews produce inconsistent depth, miss bugs, and generate contradictory findings due to attention dilution. Split into per-file local passes plus a cross-file integration pass.

**Exam Trap:** Switching to a larger context window model to fix attention dilution

Larger context windows do not solve attention quality issues. The model can hold more text but still gives uneven attention across files. Focused per-file passes are the correct fix.

**Exam Trap:** Using uncalibrated confidence scores for automated review routing

Raw self-reported confidence is poorly calibrated. Calibrate thresholds using labelled validation sets before relying on confidence for routing decisions.
