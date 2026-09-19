# Escalation & Ambiguity Resolution

## What You Need to Know

Escalation calibration is a make-or-break capability for customer support agents. Miscalibrated escalation directly destroys first-contact resolution rates. The exam tests your understanding of when to escalate, when to resolve autonomously, and which commonly proposed escalation triggers are unreliable.

## The Three Valid Escalation Triggers

There are exactly three valid reasons for a support agent to escalate to a human:

**1. Customer explicitly requests a human.** When a customer says "I want to speak to a person" or "Transfer me to a human agent," honour this immediately. Do NOT attempt to resolve the issue first. Do not say "Let me see if I can help you with that first." The customer has made a clear request and the agent must respect it without delay.

This is an absolute rule with no exceptions. The moment the customer explicitly asks for a human, the escalation happens.

**2. Policy exceptions or gaps.** The request falls outside documented policy. For example, a customer asks for competitor price matching when the policy only covers own-site price adjustments. The agent cannot make policy on the fly — this requires human judgement about whether to make an exception.

Policy gaps are distinct from policy violations. A violation (e.g., requesting a refund outside the return window) has a documented answer ("no"). A gap means the policy is silent on the specific situation. Gaps require escalation; violations do not.

**3. Inability to make meaningful progress.** The agent has attempted resolution and cannot advance. Perhaps the tools returned errors that local retry logic cannot resolve, the customer's situation requires system access the agent does not have, or the issue involves a technical bug that needs engineering intervention.

This is the catch-all, but only after a genuine attempt. "I might not be able to handle this" isn't sufficient — the agent has to show it tried and failed.

## The Two Unreliable Triggers

The exam specifically tests whether you can identify these as anti-patterns:

**Sentiment-based escalation.** Using frustration detection or negative sentiment scores to trigger escalation is unreliable because frustration does not correlate with case complexity. A customer furious about a simple late delivery is easy to resolve (apologise, offer compensation, reship). A calm, polite customer asking about competitor price matching requires human judgement on a policy gap. Sentiment measures emotional state, not case difficulty.

**Self-reported confidence scores.** Having the model output a confidence score (1-10) and escalating when it falls below a threshold is unreliable because LLM self-reported confidence is poorly calibrated. The model is often incorrectly confident on hard cases (it does not know what it does not know) and unnecessarily uncertain on straightforward cases (it hedges when the answer is clear). This is the exact failure mode described in the exam scenario: the agent escalates simple cases while attempting complex ones.

## The Frustration Nuance

The exam tests a specific nuance about customer frustration:

- If the issue is straightforward and the customer is frustrated: Acknowledge the frustration, offer the resolution. "I understand this is frustrating. I can process your replacement right now." Do not escalate.
- If the customer reiterates their preference for a human after you offer help: Now escalate. They have been given an opportunity to accept agent resolution and declined.
- If the customer explicitly says "I want a human" from the start: Escalate immediately. No investigation, no offer to help first.

The distinction is between "frustrated customer with a resolvable issue" (resolve it) and "customer who explicitly wants a human" (escalate immediately). Two situations, two responses.

## Ambiguous Customer Matching

When a tool returns multiple customer matches for a search query (say a name search turns up three "John Smith" records), the agent must ask for additional identifiers: email address, phone number, order number, or other disambiguating information.

The agent must NOT:

- Select the most recent customer record
- Select the most active customer record
- Select based on any heuristic

Selecting the wrong customer can lead to privacy violations (exposing one customer's data to another) or incorrect actions (processing a refund on the wrong account). The only safe response to ambiguous matches is to ask for clarification.

## Explicit Escalation Criteria in System Prompts

The most effective way to calibrate escalation is to add explicit escalation criteria with few-shot examples to the system prompt. These examples should demonstrate:

- When to escalate (explicit human request, policy gap, inability to progress)
- When to resolve autonomously (straightforward case, frustrated but resolvable)
- The exact format of escalation (structured handoff with customer ID, root cause, recommended action)

This is the proportionate first response before adding infrastructure like classifier models or sentiment analysis. Prompt optimisation should always precede architectural changes.

## Key Concept

Three valid escalation triggers: explicit human request (honour immediately), policy gaps (not just violations), and inability to progress. Two unreliable triggers: sentiment-based escalation and self-reported confidence scores. Sentiment does not correlate with complexity; confidence scores are poorly calibrated.

## Exam Traps

**Exam Trap:** Sentiment-based escalation seems reasonable but is fundamentally unreliable

Frustration does not correlate with case complexity. A furious customer with a simple late delivery is easy to resolve. A calm customer with a policy gap needs escalation.

**Exam Trap:** Self-reported confidence scores provide a reliable escalation signal

LLM self-confidence is poorly calibrated — the model is often incorrectly confident on hard cases and uncertain on easy ones. This is exactly the failure mode the exam tests.

**Exam Trap:** Attempting to resolve before honouring an explicit human request

When a customer says 'I want a human', escalate immediately. No investigation, no 'let me try first.' This is an absolute rule.

**Exam Trap:** Selecting from ambiguous customer matches using the most recent or most active record

Heuristic selection risks privacy violations and incorrect actions. The only safe response is to ask for additional identifiers to disambiguate.
