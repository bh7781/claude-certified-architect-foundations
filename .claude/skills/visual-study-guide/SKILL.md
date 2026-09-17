---
name: visual-study-guide
description: Build the one-page interactive HTML study guide (visual-guide.html) for a CCAR-F exercise submodule in this repo, fusing its notes.md, task.md, code and run log into a TL;DR, drawn SVG figures, a real run trace, annotated key code and exam-trap cards, then publish it as an Artifact. Use this whenever the user asks for a visual guide, visual representation, study page, diagram page, "the same HTML as for agentic loops", or wants to "visualise" a submodule or module folder in this workspace, even if they do not say HTML.
---

# Visual study guide for a CCAR-F submodule

## What this produces

One self-contained file, `visual-guide.html`, saved inside the submodule folder next to its `notes.md`, then published as a private Artifact. The reader is the user preparing for the exam. They have written the code with Claude Code and have not read it line by line, and they already own the long-form notes and video courses. The page is not a second copy of the notes. It is the thing they open to see the whole concept at once, remember what the exam tests, and find where each idea lives in the code.

The first guide, `01-agentic-architecture-and-orchestration/01-agentic-loops/visual-guide.html`, is the reference for quality. Open it before starting any new one. Everything below was learned while making it.

## Procedure

Work through these in order. Each step has a reason; skipping one is what produced the problems the checker now catches.

### 1. Gather the four sources

Read all of them fully before writing anything. The page is only trustworthy because every sentence traces to one of these.

- `notes.md` in the submodule: the concept, the "Key Concept" callouts, "Current State" notes, and the "Exam Trap" list. This is where the TL;DR and the trap cards come from.
- `task.md`: the numbered build steps, each with a Why and a "You should see". This is the build map, and it tells you what the exam thinks the concept's moving parts are.
- The code (`*.py` in the folder, plus `utils/` helpers if used): find the lines that implement each task step. Only the lines that implement an exam concept go on the page; env loading, logging and timing are plumbing.
- The run log under `logs/` (gitignored, so it may only exist locally): a real execution trace beats any invented one. Find it with:

```bash
grep -n "Execution started\|iteration\|stop_reason:\|Loop finished\|Result:" logs/ccarf-practise-YYYYMMDD.log | grep "<script name>.py"
```

  Then print the surrounding lines to get the actual response objects, tool inputs, token counts and timings. If no log exists, run the script once with the workspace `venv` to produce one.

Read `references/content-map.md` now. It says exactly which part of each source feeds which section, and how to write the TL;DR.

### 2. Write a content worksheet before touching HTML

In the scratchpad, write a short outline with these headings and fill each with plain text pulled from the sources: thesis (one sentence), TL;DR points (5 to 8), the mechanism figure 1 should show, the data or state figure 2 should show, the trace steps, the two anatomy objects, the reference table rows, the concept comparison, the code excerpts with line numbers, the traps. Doing this first means the HTML step is transcription, not composition, which is what keeps a smaller model from drifting.

### 3. Copy the template and fill it top to bottom

Copy `assets/template.html` to `<submodule>/visual-guide.html`. Do not restyle it. The CSS tokens, fonts, layout, sidebar, theme handling and component classes are settled and match the reference guide; changing them makes the guides inconsistent with each other and reintroduces layout bugs. Replace every `{{PLACEHOLDER}}` and every `<!-- FILL: ... -->` block. The template carries one example of each component (a build-map row, a trace card, a trap card, a snippet) with a comment saying "repeat this block"; duplicate those, never invent new markup.

The section order is fixed and each section id must stay, because the sidebar index links to them:

| id | Section | What it must contain |
|---|---|---|
| `tldr` | TL;DR | The one rule in large type, the mechanism in one line of chips, 5 to 8 numbered points. Must give the complete picture alone. |
| `build` | The build in N steps | One row per task.md step: step, file and line range, which figure covers it. |
| `lifecycle` | Figure 1 | The topic's core mechanism as an SVG: what flows where, the decision points, what loops back. |
| `history` | Figure 2 | The topic's state or data as an SVG: what accumulates, what is isolated, what is passed. Rename the heading to fit the topic; keep the id. |
| `trace` | A real run | Cards reconstructed from the log with actual values. Plus a contrast strip when the log holds a failure or edge case. |
| `anatomy` | Anatomy | The two or three objects that carry the exam vocabulary, shown as real JSON or code with a definition list. |
| `reasons` | Reference | One table of the enumerable facts (values, modes, options) with an "exam" versus "production" scope chip. |
| `decisions` | Concept | The one comparison the exam tests (two cards), with the exception worth memorising. |
| `code` | Key code | Three to five annotated excerpts, each with file and lines and the trap it avoids. |
| `traps` | Exam traps | One `<details class="trap">` per trap in notes.md, plus the distractor, each with Wrong, Why, Right. |

If a topic genuinely has no content for a section, remove the section and its index link together. Never leave an empty section.

### 4. Draw the figures with the recipes

Read `references/svg-recipes.md` before drawing. It gives the marker definitions, the class names, the exact width formula for boxes, and ready-made patterns: linear flow with a decision diamond and return loop, stacked snapshots with brackets, hub-and-spoke, swimlane sequence, side-by-side comparison. Choose the pattern that shows the mechanism, not the name of the thing. Every box is sized from its longest label using the formula; that is the rule that stops text escaping boxes.

### 5. Run the checker until it passes

```bash
./venv/Scripts/python.exe .claude/skills/visual-study-guide/scripts/check_guide.py <submodule>/visual-guide.html
```

It checks tag balance, the required sections and sidebar, that every index link resolves, that no `{{PLACEHOLDER}}` remains, that no prose is width-capped, and that every SVG label fits its box and the viewBox. Fix every FAIL line. A warning is worth reading but does not block.

### 6. Publish and report

Publish the file with the Artifact tool. Pass a `favicon` (one emoji fitting the topic; keep it on republishes by omitting it), a one-sentence `description`, and let the file's `<title>` name the artifact. Do not commit; the user reviews and commits themselves.

Reply with: the artifact link and the file path, a bulleted list of what each section contains, what the checker verified and what it could not (it cannot render, so the browser look is the user's), and a one-line suggested commit message without any attribution footer.

## Writing rules for the page

These come from the user's review of the first guide. Each one fixed a specific complaint.

- **Prose uses the whole column.** No `max-width` on paragraphs, callouts or captions, no manual `<br>`, no strings broken across lines inside `<pre>` to look tidy. The user found abrupt line breaks with empty space to the right "weird"; a long string in a code block scrolls horizontally inside its `<pre>` instead.
- **The index lives in the sticky left sidebar**, never as links in the header. The user wants to jump to any section from anywhere without scrolling up. The template already does this and highlights the current section; keep the `href="#id"` list in sync with the section ids.
- **The TL;DR is the page in miniature.** Someone who reads only that panel should be able to answer an exam question on the topic. Each point starts with a bold claim in five words or fewer, then one or two sentences that make it testable. Write it last, after the rest of the page exists, then place it first.
- **Every number comes from a source.** Token counts, timings, ids, iteration counts and line ranges are copied from the log or the file. Shorten long ids with an ellipsis but keep the real tail so they are recognisable.
- **Label what a figure shows, not what it is called.** Arrows carry verbs ("appends", "returns", "never sees"). A caption states the claim the picture makes. The aria-label repeats that claim in words.
- **Structure encodes truth.** Number things only when order is real (task steps, iterations). Use the amber, green, blue and red tokens only for their meanings: continue, finished, the decision or signal, and traps or failures.
- **Comments in code excerpts stay.** Copy excerpts verbatim from the file including the author's comments, with `<span class="k">`, `<span class="s">` and `<span class="c">` for keywords, strings and comments. Trim to the lines that carry the concept and note the line range.
- **Names, not captions, for the title.** `<title>` is a two to four word name of the concept ("Agentic Loop Lifecycle"), never "Topic: study guide".

## Where things are

- `assets/template.html`: the page skeleton with CSS and one example of each component. Copy it; do not edit it in place.
- `references/content-map.md`: source to section mapping, TL;DR method, trap card format, trace reconstruction.
- `references/svg-recipes.md`: classes, markers, the width formula, and five figure patterns with coordinates.
- `scripts/check_guide.py`: the checker. Run it after every edit.
- `01-agentic-architecture-and-orchestration/01-agentic-loops/visual-guide.html`: the finished reference guide.
