# System Prompts with Explicit Criteria

## What You Need to Know

The single biggest mistake in production prompt engineering is relying on vague instructions. "Be conservative." "Only report high-confidence findings." "Use your best judgement." None of these give the model an actionable decision boundary. They sound reasonable, which is exactly why the exam uses them as distractors.

The correct approach is explicit categorical criteria that define precisely what the model should flag and what it should skip. Compare these two system prompts for a CI/CD code review pipeline:

**Wrong approach:**

```text
Review this code. Be conservative. Only report high-confidence findings.
```

**Correct approach:**

```text
Flag comments only when claimed behaviour contradicts actual code behaviour.
Report bugs and security vulnerabilities.
Skip minor style preferences and local patterns.
```

The first gives the model no criteria to apply. "Conservative" means different things in different contexts, and "high-confidence" is a subjective threshold the model cannot calibrate. The second provides concrete categories: what to report (bugs, security), what to skip (style, local patterns), and a specific trigger for comment flags (claimed vs actual behaviour contradiction).

## The False Positive Trust Problem

High false positive rates in one category destroy developer trust in all categories. The exam leans on this hard. If your "documentation mismatch" findings are wrong 40% of the time, developers stop reading your "security vulnerability" findings too, even when those run at 98% accuracy. Trust isn't category-specific. It bleeds across the whole output.

The fix feels backwards: temporarily disable the high false-positive categories while you rework their prompts. Trust in the categories that already work comes back straight away. Then you iterate on the broken category with concrete code examples, switching it back on only once precision improves.

You're not abandoning the category. You're putting system-wide trust ahead of category completeness.

## Severity Calibration with Code Examples

Defining severity levels requires concrete code examples, not prose descriptions. Compare:

**Prose description (insufficient):**

```text
Critical: Issues that could cause system failures or data loss
Minor: Issues that affect code readability but not functionality
```

**Code example approach (correct):**

```text
Critical — Unsanitised user input in SQL query:
  query = f"SELECT * FROM users WHERE id = {user_input}"

Minor — Inconsistent variable naming:
  userName vs user_name in the same module
```

The prose description forces the model to interpret what "could cause system failures" means. The code example removes ambiguity entirely. When the model sees actual code patterns classified at each severity level, it produces consistent classification across invocations.

## Key Concept

Explicit categorical criteria always outperform vague instructions. Define what to flag (bugs, security vulnerabilities) and what to skip (style preferences, local patterns) using concrete code examples for each severity level. Never rely on "be conservative" or confidence-based filtering.

## Why Confidence-Based Filtering Fails

The exam frequently presents "only report high-confidence findings" as a tempting answer. It sounds like good engineering: filter by confidence, keep only the strong signals. But LLM self-reported confidence is poorly calibrated. The model is often sure about wrong findings and hesitant about right ones. Confidence scores earn their keep in routing (sending low-confidence findings to human review, as covered in Task Statement 4.6), but they're no substitute for explicit criteria that define what counts as a valid finding in the first place.

The hierarchy is: explicit criteria first, confidence-based routing second. Never skip the first step.

## Exam Traps

**Exam Trap:** Choosing 'be conservative' or 'only report high-confidence findings' as valid prompt improvements

Vague instructions do not improve precision. The model has no actionable interpretation of 'conservative.' Specific categorical criteria defining exactly what to flag and what to skip are the correct approach.

**Exam Trap:** Assuming confidence thresholds fix false positive problems

LLM self-reported confidence is poorly calibrated. Explicit criteria with concrete code examples produce better results than confidence-based filtering. Confidence routing is useful but only after criteria are defined.

**Exam Trap:** Keeping all review categories active while iterating on high false-positive categories

High false positive rates in one category destroy trust in ALL categories. Temporarily disabling problematic categories while improving their prompts restores system-wide trust.
