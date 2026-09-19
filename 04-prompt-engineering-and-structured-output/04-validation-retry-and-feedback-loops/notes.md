# Validation, Retry, and Feedback Loops

## What You Need to Know

Production extraction systems fail. Documents arrive in unexpected formats, numerical values don't add up, and fields end up in the wrong places. The question isn't whether failures happen but how your system responds. The validation-retry pattern turns those failures into self-correcting workflows.

## Retry-with-Error-Feedback

The correct retry pattern sends three pieces of information back to the model:

- The original document — so the model has the source to re-examine
- The failed extraction — so the model can see what it produced
- The specific validation error — so the model knows exactly what went wrong

```typescript
// Retry with error feedback
const retryMessages = [
  {
    role: "user",
    content: `Original document:\n${originalDocument}\n\n` +
      `Your extraction:\n${JSON.stringify(failedExtraction)}\n\n` +
      `Validation error: Line items sum to £450 but stated_total is £500. ` +
      `Please re-extract, ensuring all line items are captured.`
  }
];
```

This beats a naive retry by a wide margin. Without the specific error, the model has no guidance for what to fix and usually reproduces the same mistake. With it, the model can target its self-correction: re-examining the document for missed line items, checking field placement, recalculating the total.

## The Retry Effectiveness Boundary

This is the concept the exam tests most aggressively in this task statement. Retries have a clear effectiveness boundary:

**Retries ARE effective for:**

- Format mismatches (wrong date format, inconsistent currency notation)
- Structural output errors (values in wrong fields, incorrect nesting)
- Misplaced values (data that exists in the document but was extracted into the wrong field)
- Mathematical errors (the model missed a line item affecting the total)

**Retries are NOT effective for:**

- Information genuinely absent from the source document
- Data that exists only in an external document not provided to the model
- Fields requiring knowledge the model does not have

The exam presents both scenarios and expects you to identify which is fixable. If a document genuinely doesn't contain a department name, no amount of retrying will produce a correct value. Flag the extraction for human review, or return null if the schema allows it.

## Self-Correction Flow Design

Rather than relying solely on external validation logic, you can build self-correction into the extraction schema itself:

**calculated_total vs stated_total:** Extract both the sum the model calculates from individual line items and the total stated in the document. When these differ, you have an automatic discrepancy flag without external logic.

```json
{
  "line_items": [
    { "description": "Widget A", "amount": 150.00 },
    { "description": "Widget B", "amount": 300.00 }
  ],
  "calculated_total": 450.00,
  "stated_total": 500.00,
  "total_discrepancy": true
}
```

**conflict_detected booleans:** Add boolean fields that flag when the source document contains contradictory information. For example, if a document states "payment due: 30 days" in one section but "payment terms: net 60" in another, the model should extract both and set conflict_detected: true rather than silently picking one.

## detected_pattern Fields

For code review and analysis pipelines, add detected_pattern fields to structured findings. This tracks which specific code construct triggered each finding.

```json
{
  "finding": "Potential SQL injection vulnerability",
  "severity": "critical",
  "detected_pattern": "string concatenation in SQL query",
  "file": "user_service.py",
  "line": 42
}
```

When developers dismiss findings, you can analyse dismissal patterns by detected_pattern. If developers consistently dismiss findings triggered by "variable shadowing in nested scope," that pattern likely needs prompt refinement. This creates a systematic improvement loop: extract, validate, collect dismissal data, refine prompts, repeat.

## Schema Syntax Errors vs Semantic Validation Errors

The exam distinguishes between these two error categories:

**Schema syntax errors** — Malformed JSON, missing required fields, wrong data types. Eliminated entirely by tool_use with JSON schemas (covered in Task Statement 4.3).

**Semantic validation errors** — Correct JSON structure but incorrect values. Line items that do not sum, dates that precede each other incorrectly, values in wrong fields. These require validation logic outside the schema and are the focus of retry loops.

The overlap between these task statements is intentional. The exam tests whether you understand that tool_use solves the first category but not the second.

## Pydantic as the Validation Layer

The exam guide names Pydantic alongside JSON Schema in its hands-on exercise for this task statement: "when Pydantic or JSON schema validation fails, send a follow-up request including the document, the failed extraction, and the specific validation error." In a Python pipeline, Pydantic is the layer that turns "validation failed" into the specific, per-field error messages the retry loop needs.

A Pydantic model does two jobs at once. Parsing enforces structure — types, required fields, enums. Validators enforce semantics — the rules a JSON schema cannot express, like cross-field arithmetic or date ordering. Both failure kinds surface through one ValidationError, with machine-readable errors naming the field and the broken rule:

```python
import json
from pydantic import BaseModel, ValidationError, model_validator

class LineItem(BaseModel):
    description: str
    amount: float

class Invoice(BaseModel):
    line_items: list[LineItem]
    stated_total: float

    @model_validator(mode="after")
    def totals_must_match(self):
        calculated = round(sum(i.amount for i in self.line_items), 2)
        if abs(calculated - self.stated_total) > 0.01:
            raise ValueError(
                f"line items sum to {calculated} but stated_total is {self.stated_total}"
            )
        return self

try:
    invoice = Invoice.model_validate(tool_input)  # the tool_use input from the response
except ValidationError as e:
    errors = "\n".join(
        f"{'.'.join(map(str, err['loc'])) or 'invoice'}: {err['msg']}" for err in e.errors()
    )
    retry_message = (
        f"Original document:\n{original_document}\n\n"
        f"Your extraction:\n{json.dumps(tool_input)}\n\n"
        f"Validation errors:\n{errors}\n\n"
        f"Please re-extract, fixing the identified errors."
    )
```

The except branch is the retry-with-error-feedback pattern from the top of this lesson — Pydantic simply supplies the third ingredient (the specific error) in a form you can format straight into the prompt. The retry-effectiveness boundary applies unchanged: a validator that fails because information is absent from the source document still means human review, not a retry.

## Current state: SDK-level parsing and strict tool use

As of July 2026, the Python SDK's client.messages.parse(..., output_format=Invoice) returns validated Pydantic instances via parsed_output, and strict: true on a tool definition guarantees schema-conformant inputs server-side (Structured Outputs). Neither removes the semantic layer: the platform enforces the schema, your validators enforce the business rules, and the retry loop consumes whichever one fails.

## Key Concept

Retry-with-error-feedback works by sending the original document, the failed extraction, and the specific validation error. Retries fix format and structural errors but cannot create information absent from the source document. Always identify whether a failure is fixable before retrying.

## Exam Traps

**Exam Trap:** Assuming retries always work for extraction failures

Retries fix format mismatches, structural errors, and misplaced values. They cannot produce information genuinely absent from the source document. The exam presents both fixable and unfixable scenarios — you must distinguish them.

**Exam Trap:** Implementing retries without including the specific validation error

Naive retries without error feedback produce the same mistakes. The model needs to see exactly what went wrong (e.g., 'line items sum to £450 but stated total is £500') to self-correct effectively.

**Exam Trap:** Relying on schema validation alone without semantic checks

Schema validation (via tool_use) catches syntax errors. Semantic errors — wrong sums, misplaced values, fabricated data — require validation logic and retry loops.

**Exam Trap:** Treating Pydantic as redundant once tool_use enforces a JSON schema

Schemas eliminate syntax errors but cannot express cross-field semantic rules — sums that must match, dates that must be ordered. Pydantic validators encode those rules and produce the specific, per-field error messages the retry loop feeds back to the model.
