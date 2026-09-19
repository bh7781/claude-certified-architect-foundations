# Few-Shot Prompting

## What You Need to Know

Few-shot examples are the most effective technique for achieving consistent, well-formatted output from Claude. Not more instructions. Not confidence thresholds. Not temperature adjustments. When your output is inconsistent, few-shot examples are the first tool to reach for.

This is a direct exam principle. The exam presents scenarios where detailed instructions produce inconsistent results and tests whether you choose "add more instructions" or "add few-shot examples." The correct answer is almost always the latter.

## When to Deploy Few-Shot Examples

Three specific triggers tell you few-shot examples are needed:

**1. Detailed instructions alone produce inconsistent formatting.** You have written a thorough prompt specifying the output format, but the model produces different structures across invocations — sometimes a bulleted list, sometimes a table, sometimes prose. More instructions will not fix this. A few examples showing the exact format you want will.

**2. The model makes inconsistent judgement calls on ambiguous cases.** For a code review tool, the model flags variable shadowing as "critical" in one file and "minor" in another. For a tool selection agent, it routes "check my order" to different tools depending on phrasing. These ambiguous cases need examples demonstrating the correct judgement, with reasoning.

**3. Extraction tasks produce empty/null fields for information that exists in the document.** The information is present but in an unexpected format — embedded in narrative text rather than a structured table, or split across multiple paragraphs. Few-shot examples showing extraction from varied document structures resolve this.

## How to Construct Effective Examples

The rules are tight:

**Use 2-4 targeted examples.** Fewer than 2 doesn't establish a pattern. More than 4 wastes tokens without proportional benefit. Point your examples at the specific ambiguous scenarios causing problems.

**Each example must show reasoning.** Don't just show input-output pairs. Show why one action was chosen over plausible alternatives. That teaches the model to generalise its judgement to novel patterns, not just match the specific cases in your examples.

```text
Example: Tool selection for "check my order #12345"
Input: "check my order #12345"
Selected tool: lookup_order
Reasoning: The user provides an order number (#12345), indicating
they want order-specific information. Even though this could be
interpreted as a general customer query, the specific order
identifier makes lookup_order the correct choice over get_customer.
```

Without the reasoning, the model learns only "queries mentioning order numbers go to lookup_order." With the reasoning, the model learns the general principle: specific identifiers route to specific lookup tools.

**Cover the failing scenarios.** If your extraction works on tables but fails on narrative text, your examples should show correct extraction from narrative text. If your code review is inconsistent on variable shadowing, your examples should classify variable shadowing scenarios at different severity levels with reasoning.

## The Hallucination Reduction Effect

Few-shot examples have a useful side effect: they cut hallucination in extraction tasks. When the model sees examples of correct extraction from varied document structures — inline citations vs bibliographies, narrative descriptions vs structured tables, headers vs embedded text — it learns to handle structural variety without inventing data.

This matters most for documents with inconsistent formatting. A financial report might list expenses in a table on one page and bury them in a paragraph on the next. Without examples, the model often nails the table but returns empty fields for the narrative section, or worse, fabricates values. Show it both structures and extraction quality climbs.

## Few-Shot for Reducing False Positives

In code review and analysis, few-shot examples pull double duty: they show both what to flag and what to ignore. Examples that separate acceptable code patterns from genuine issues cut false positives while still catching the real problems.

```text
Example: Variable shadowing assessment
Code: function process(items) {
  const result = items.map(item => {
    const result = transform(item);  // shadows outer 'result'
    return result;
  });
  return result;
}
Severity: minor
Reasoning: The inner 'result' shadows the outer variable but
within a limited scope (arrow function). The code is still readable
and the shadow does not cause a bug. This is a style preference,
not a defect. Flag as minor only if style consistency is in scope.
```

This example teaches the model to distinguish genuine bugs from benign patterns, reducing false positives while preserving the ability to generalise to genuinely problematic shadowing cases.

## Key Concept

Few-shot examples are the most effective technique for consistency. Use 2-4 targeted examples that include reasoning for decisions, not just input-output pairs. Deploy them when instructions alone produce inconsistent results, ambiguous judgements, or empty extraction fields for data that exists.

## Few-Shot vs Other Techniques

The exam tests whether you can distinguish when few-shot examples are the right solution versus when another technique applies:

| Problem | Correct Technique |
| --- | --- |
| Inconsistent output formatting | Few-shot examples |
| Malformed JSON output | tool_use with JSON schemas |
| Fabricated values for missing fields | Optional/nullable schema fields |
| Wrong tool selection | Better tool descriptions (first), then few-shot |
| Model misses information in narrative text | Few-shot examples showing narrative extraction |
| Extraction sum does not match total | Validation-retry loop |

## Exam Traps

**Exam Trap:** Choosing 'add more detailed instructions' when output formatting is inconsistent

If detailed instructions already exist and output is still inconsistent, adding more instructions will not fix the problem. Few-shot examples demonstrating the exact desired format are more effective for consistency.

**Exam Trap:** Thinking few-shot examples only teach literal pattern-matching

When examples include reasoning for why decisions were made, they teach the model to generalise to novel patterns. The model learns the decision principle, not just the specific case.

**Exam Trap:** Using confidence thresholds to fix inconsistent judgement calls

Confidence thresholds are poorly calibrated and do not address the root cause. Few-shot examples showing the correct judgement for ambiguous cases directly teach consistent decision-making.
