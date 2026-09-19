# Tool Interface Design

## What You Need to Know

Tool descriptions are the PRIMARY mechanism LLMs use for tool selection. Not supplementary metadata. Not an afterthought. When a model receives a set of tools, it reads the descriptions to decide which one to call — and if those descriptions are minimal, something like "Retrieves customer information", it has no way to tell apart tools that serve overlapping purposes.

## What Makes a Good Tool Description

A production-grade tool description includes five elements:

- What the tool does — its primary purpose, stated unambiguously
- What inputs it expects — data types, formats, constraints, and required versus optional fields
- Example queries it handles well — concrete use cases that anchor the model's understanding
- Edge cases and limitations — what the tool does NOT do, and what happens when inputs fall outside expected ranges
- Explicit boundaries — when to use THIS tool versus similar tools in the same toolkit

Here is the difference between a minimal and a production-grade description:

Minimal (causes misrouting):

```
get_customer: "Retrieves customer information"
lookup_order: "Retrieves order details"
```

Production-grade (reliable selection):

```
get_customer: "Looks up a customer account by email address,
phone number, or customer ID. Returns customer profile
(name, contact details, account status, loyalty tier).
Use this when you need to verify who the customer is.
Do NOT use for order-specific queries — use lookup_order
for those."

lookup_order: "Retrieves order details by order number
(format: #NNNNN) or tracking ID. Returns order status,
items, shipping details, and refund eligibility.
Use this when a customer asks about a specific order.
Do NOT use for customer identity verification —
use get_customer for that."
```

The second version gives the model explicit disambiguation. It knows which identifiers each tool accepts, what each returns, and crucially, when NOT to use each tool.

## The Misrouting Problem

Two tools with overlapping or near-identical descriptions cause selection confusion. The exam guide's sample Question 2 presents exactly this scenario: get_customer and lookup_order with minimal descriptions, causing the agent to route "check my order #12345" to the wrong tool.

The exam tests whether you can spot the correct fix. Four plausible options, three of them wrong:

- Expand descriptions — correct. Low effort, high leverage, directly addresses the root cause.
- Few-shot examples — wrong. Adds token overhead without fixing why the model is confused. You're treating symptoms, not the disease.
- Routing classifier — wrong. Over-engineered as a first step. Bypasses the LLM's natural language understanding and adds infrastructure complexity.
- Tool consolidation — wrong as a first step. It's a valid architectural choice long-term, but it costs far more effort than expanding descriptions.

The exam consistently favours low-effort, high-leverage fixes. Better descriptions before routing classifiers. Scoped access before full access. Community servers before custom builds.

## Tool Splitting

Generic tools with broad responsibilities create ambiguity. The fix: split them into purpose-specific tools with defined input/output contracts.

Before splitting:

```
analyze_document: "Analyses a document and returns results"
```

After splitting:

```
extract_data_points: "Extracts structured data fields
(dates, amounts, names) from a document"

summarize_content: "Produces a concise summary of a
document's key arguments and conclusions"

verify_claim_against_source: "Checks whether a specific
claim is supported by the source document, returning
supporting/contradicting evidence"
```

Each resulting tool does one narrow, clearly described job. The model can pick the right one based on what the user actually needs.

## Tool Renaming for Clarity

When two tools have confusingly similar names, renaming fixes the overlap at the interface level. Rename analyze_content to extract_web_results, give it a web-specific description, and the tool's purpose becomes unambiguous — without touching its implementation.

## System Prompt Interactions

Keyword-sensitive instructions in system prompts can create unintended tool associations that override well-written descriptions. If your system prompt says "always check customer details before proceeding", the model may route any customer-related query to get_customer no matter what the descriptions say.

So after updating tool descriptions, reread your system prompt for conflicts. It's a subtle failure mode, and the exam tests it.

**Key Concept**

Tool descriptions are the primary mechanism LLMs use for tool selection. When misrouting is caused by weak descriptions, improving them is the first fix — not few-shot examples, routing classifiers, or tool consolidation.

Read the condition on that, because the exam tests both halves. Descriptions are the fix when the agent has a workable number of tools and simply cannot tell two of them apart. They are not the fix when the toolkit itself is the problem: past roughly 4-5 tools per agent, selection degrades on decision complexity alone, and rewriting 22 descriptions leaves that untouched. Diagnose which one you are looking at before reaching for a remedy. Task Statement 2.3 covers the overload threshold and what to do instead.

## Exam Traps

**Exam Trap**

Choosing few-shot examples to fix tool misrouting caused by minimal descriptions

Few-shot examples add token overhead without addressing the root cause. The model is confused because descriptions do not differentiate the tools — fix the descriptions first.

**Exam Trap**

Implementing a routing classifier as the first step to fix tool selection

A routing classifier is over-engineered as a first response. It bypasses the LLM's natural language understanding and adds infrastructure the exam does not consider proportionate.

**Exam Trap**

Consolidating similar tools into one as the first step

Tool consolidation is a valid long-term architectural choice, but it requires more effort than expanding descriptions. The exam favours low-effort, high-leverage first steps.

**Exam Trap**

Ignoring system prompt wording after updating tool descriptions

Keyword-sensitive instructions in system prompts can silently override well-written tool descriptions, creating unintended tool associations.