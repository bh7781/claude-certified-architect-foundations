# Structured Output with Tool Use

## What You Need to Know

When you need guaranteed schema-compliant structured output from Claude, there is a clear reliability hierarchy:

- tool_use with JSON schemas — eliminates JSON syntax errors entirely
- Prompt-based JSON — model can produce malformed JSON

Commit this hierarchy to memory. The exam builds on it. With tool use, the tool's JSON schema constrains the shape of what Claude returns, eliminating syntax issues like missing brackets, trailing commas, or unquoted keys. The separate tool_choice parameter is what forces the model to call the tool at all. Prompt-based extraction (asking the model to output JSON in a text response) gives you no structural guarantees and will periodically produce unparseable output in production.

## Current state

Exam guide v1.0 frames the hierarchy as the two tiers above, and that is the expected exam answer. As of 14 August 2026 the API adds two controls the guide predates. strict: true on a tool definition is one; the guide's appendix names it as "strict mode for syntax error elimination". output_config.format is the other, and it constrains the response itself rather than a tool call. The current docs also list a fourth tool_choice mode, {"type": "none"}, which blocks tool calls and is the default when you pass no tools; the guide names three, so answer three. On the exam, answer with the tool_use-over-prompt-based hierarchy.

## tool_choice: The Three Modes

The tool_choice parameter controls whether and how the model calls tools. Understanding the three modes is critical for the exam:

**"auto"** (default): The model decides whether to call a tool or return text. It may choose to respond with a text message instead of calling the extraction tool. Use this when the model legitimately needs the option to respond conversationally.

**"any"**: The model MUST call a tool but chooses which one. Use this when you have multiple extraction schemas (e.g., extract_invoice, extract_receipt, extract_contract) and the document type is unknown. The model selects the appropriate tool and returns structured output. Guaranteed structured output, flexible tool selection.

**{"type": "tool", "name": "extract_metadata"}**: The model MUST call the specific named tool. Use this to force a mandatory first step — for example, ensuring metadata extraction runs before enrichment steps. No flexibility, maximum control.

extract_metadata here is a tool you defined yourself; the name is arbitrary. tool_choice also applies per request, not per conversation. Once the forced call returns, send the next request with auto (or leave the parameter out), otherwise the model is obliged to call the same tool again and you loop.

```typescript
// Force guaranteed structured output with unknown document type
const response = await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 4096,
  tool_choice: { type: "any" },
  tools: [extractInvoiceTool, extractReceiptTool, extractContractTool],
  messages: [{ role: "user", content: documentText }]
});

// Force a specific extraction step
const response = await client.messages.create({
  model: "claude-sonnet-5",
  max_tokens: 4096,
  tool_choice: { type: "tool", name: "extract_metadata" },
  tools: [extractMetadataTool],
  messages: [{ role: "user", content: documentText }]
});
```

## What tool_use Does NOT Prevent

This is where the exam gets sneaky. tool_use with JSON schemas eliminates syntax errors but does NOT prevent semantic errors:

- Sum discrepancies: Line items that do not sum to the stated total
- Field placement errors: Values placed in the wrong fields (e.g., a date in an amount field when both are strings)
- Fabrication: The model invents values for required fields when the source document lacks the information

The schema guarantees structure. It doesn't guarantee correctness. Semantic validation needs additional logic (covered in Task Statement 4.4).

## Schema Design for Production

Effective schema design prevents entire classes of errors at the structural level:

**Optional/nullable fields** — When source documents may not contain certain information, make those fields optional or nullable. This is the primary defence against fabrication. If a field is required, the model is pressured to produce a value even when the source has none. If the field is nullable, the model can honestly return null.

```json
{
  "type": "object",
  "properties": {
    "invoice_number": { "type": "string" },
    "vendor_name": { "type": "string" },
    "payment_terms": { "type": ["string", "null"] },
    "purchase_order": { "type": ["string", "null"] }
  },
  "required": ["invoice_number", "vendor_name"]
}
```

**"unclear" enum value** — For ambiguous cases where the source is genuinely unclear, add an explicit "unclear" option to enum fields. This prevents the model from forcing a classification when the evidence is ambiguous.

**"other" + detail string** — For extensible categorisation, include an "other" enum value paired with a freeform detail string field. This captures edge cases that your predefined categories do not cover.

```json
{
  "category": {
    "type": "string",
    "enum": ["invoice", "receipt", "contract", "unclear", "other"]
  },
  "category_detail": {
    "type": ["string", "null"],
    "description": "Freeform detail when category is 'other'"
  }
}
```

**Format normalisation rules** — Include format normalisation instructions in the prompt alongside the schema. The schema enforces structure. The prompt enforces formatting consistency (e.g., "All dates in ISO 8601 format," "All currency amounts as decimal numbers without currency symbols").

## Key Concept

tool_use with JSON schemas eliminates syntax errors but not semantic errors. Make fields optional/nullable when source documents may lack information — this prevents the model from fabricating values. Use tool_choice "any" for guaranteed structured output when the document type is unknown.

## Exam Traps

**Exam Trap:** Believing tool_use with JSON schemas prevents all extraction errors

tool_use eliminates JSON syntax errors only. Semantic errors — values that do not sum correctly, data placed in wrong fields, fabricated values for missing information — still occur and require separate validation.

**Exam Trap:** Confusing tool_choice 'auto' with 'any'

'auto' allows the model to return text instead of calling a tool — no guarantee of structured output. 'any' guarantees a tool call but lets the model choose which tool. For guaranteed structured output with unknown document types, use 'any'.

**Exam Trap:** Making all schema fields required to ensure data completeness

Required fields pressure the model to fabricate values when information is absent from the source. Optional/nullable fields allow honest null responses, which is always preferable to plausible-looking fabricated data.
