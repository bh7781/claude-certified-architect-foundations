# Content map: which source feeds which section

Read this after gathering the four sources and before writing the worksheet. It is the answer to "what goes where", so the page never has to be composed from scratch.

## 1. From `notes.md`

The notes follow the guide website's shape. Each heading type maps to a fixed place on the page.

| Heading in notes.md | Goes to | How |
|---|---|---|
| "What You Need to Know" (opening paragraph) | Header thesis, TL;DR rule | Reduce to one sentence that names the mechanism and the one thing that controls it. |
| Numbered lifecycle / architecture steps | Figure 1 | Each step is a node; the transitions between them are the labelled arrows. |
| "Key Concept" callouts | TL;DR points, figure captions | Every Key Concept becomes one TL;DR point, near-verbatim. |
| "Current State" notes | Reference table rows marked `production`, or a muted callout | These are the "beyond the exam" facts; keep them visibly separate from the exam-keyed ones with the scope chip. |
| A named comparison (X versus Y, "the exception") | `decisions` section, two cards | The exception worth memorising goes in bold in the second card. |
| "Practical Example" / worked bug | The Worked row inside the matching trap card | Keep the story: symptom, cause, fix. |
| "Anti-Patterns" and "Exam Trap N" | One `<details class="trap">` each | Wrong / Why / Right rows. Where notes list the same idea under both headings, merge into one card. |
| "Common Exam Distractor" | The final trap card titled "Distractor" | It is the answer the exam offers that sounds right; say why to reject it. |

## 2. From `task.md`

| Part of task.md | Goes to |
|---|---|
| Step titles, in order | The `build` map rows, one per step |
| Each step's "Why" | The TL;DR, if it states a concept the exam tests |
| Each step's "You should see" | The trace section: it tells you what evidence to look for in the log |
| Starter code | Nothing directly. The page shows the Python that was actually written, not the JS starter. |

Each build-map row needs the file and line range where that step lives. Find it by the `# --- Step N` header comments in the exercise script, then note the range of the real implementation (the header may be far from the code, as in agent_loop.py where the step 3 header sits above the function and the code is inside the loop).

## 3. From the code

Pick three to five excerpts. An excerpt earns its place if it implements something a trap or a TL;DR point talks about. Typical picks:

- the branch or dispatch that embodies the core decision
- the state handoff (what gets appended, passed, or isolated)
- the guard or safety mechanism, showing where it sits relative to the main path
- the fall-through or error path

Copy verbatim, including the author's comments. Trim leading plumbing. Record `file.py first–last` and the task step number in the `.where` line. In the note, say what the excerpt does in one bold phrase, then the trap or concept it connects to using a chip.

Also pull the objects for the `anatomy` section from the code and the log: a definition the code registers (tool, agent, schema, hook config) and the object the API returns (the `Message`, a subagent result, a hook payload). Show real values from the log, not illustrative ones.

## 4. From the log

The log format is `timestamp | level | file:line | function() | memory | message`, and `format_message()` prints each API response as pretty JSON between `---` lines. Reconstruct the trace like this:

1. `grep -n "<script>.py" logs/<file>.log | grep "Execution started"` to find each run's start line.
2. Print from a start line to the next "Execution finished" and read it top to bottom.
3. For each iteration or stage, record: the stop_reason or status, what was requested (tool name and input, subagent and prompt), what came back, `input_tokens` / `output_tokens`, and the wall time from consecutive timestamps.
4. If the log also holds a failing or edge run (a cap that fired, a retry, an empty result), keep it: it becomes the contrast strip, which is often the most memorable part of the page.

Cite the log file name and the time window in the section eyebrow and the footer, so the trace is auditable.

## 5. Writing the TL;DR

Write it after everything else exists, then place it first. Method:

1. List every Key Concept, every trap's "Right" row, and every bold claim in the decisions cards.
2. Merge duplicates. You should have 5 to 8 statements.
3. Order them: the one rule first, then the mechanism, then the failure modes, then the reference facts.
4. Each point: a bold claim of five words or fewer, then one or two sentences that make it concrete enough to answer a scenario question. Name the field, the value, the exception.
5. Put the single most important rule in the large `.rule` line above the list, and draw the mechanism as one line of `.flow` chips (nodes joined by arrows, with branches under a left border).

Test: cover the rest of the page and read only the panel. If a trap card's answer cannot be derived from the panel, the panel is missing a point.

## 6. Trap card format

```html
<details class="trap">
  <summary>Trap N · <one-line statement of the wrong approach></summary>
  <div class="body">
    <div class="row wrong"><b>Wrong</b><span>What the wrong code or answer does.</span></div>
    <div class="row why"><b>Why</b><span>The mechanism that makes it fail, ideally pointing at the figure or trace where it is visible.</span></div>
    <div class="row right"><b>Right</b><span>The correct approach in one or two sentences.</span></div>
    <!-- optional --> <div class="row why"><b>Worked</b><span>The notes' practical example: symptom, cause, fix.</span></div>
  </div>
</details>
```

## 7. Choosing the two figures

Figure 1 is always the mechanism: how control or information moves. Figure 2 is always the state: what accumulates, what is isolated, what is copied. Examples by topic:

| Submodule | Figure 1 | Figure 2 |
|---|---|---|
| Agentic loops | API call, stop_reason diamond, tool_use return path, end_turn exit | The messages list at three snapshots with tool_use to tool_result brackets |
| Multi-agent orchestration | Hub-and-spoke: coordinator centre, subagents around, every edge through the hub | Context isolation: what each subagent's prompt contains versus what the coordinator holds |
| Subagent invocation and context passing | Swimlane sequence: coordinator, subagent A, subagent B with labelled hand-offs | The prompt payload assembled for a subagent, field by field |
| Workflow enforcement and hand-off | Flow with programmatic gates drawn as guards on edges | Side-by-side: model-driven path versus enforced path on the same task |
| Hooks | Event timeline with hook points as guards before and after tool calls | Hook input and output objects |
| Task decomposition | Tree or fan-out/fan-in of subtasks with aggregation | Coverage matrix or the aggregated result shape |
| Session state and resumption | State machine of a session with save and resume edges | The persisted state object at two points in time |

Pick the pattern from `svg-recipes.md` that matches, then rename the `history` section heading to describe the state being shown while keeping the id.
