# Claude Certified Architect Foundations (CCAR-F) — Practice Workspace

## Purpose
This workspace is used to build hands-on exercises from the CCAR-F certification
guide at https://claudecertificationguide.com/, as practice for the upcoming
CCAR-F exam.

## Workflow
- The user shares a problem statement from the website for a given topic/build exercise.
- Claude acts as coding partner: help design and implement the exercise.
- After implementation, the user reads the code, runs it, and clears their concepts.
- The user may ask follow-up questions before moving to the next exercise.
- Exercises span multiple certification topics/domains — expect a new subfolder
  per topic (see structure below).

## Structure
- Each certification topic/domain gets its own top-level folder, numbered in
  build order and named to match the guide (e.g.
  `01-agentic-architecture-and-orchestration/`).
- Within a topic folder, individual build exercises get their own
  numbered subfolder (e.g. `01-agentic-loops/`).
- `.env` at the workspace root holds shared secrets (e.g. `ANTHROPIC_API_KEY`)
  available to all exercises — do not duplicate API keys per-exercise unless
  an exercise specifically needs isolation.
- A single Python virtual environment named `venv/` lives at the workspace root
  and is shared across all exercises, built against **Python 3.12** (installed
  via winget as `Python.Python.3.12`; the system also has 3.14 as default,
  but 3.12 avoids Windows Application Control blocking newly-published native
  wheels — see Notes). Use `py -3.12 -m venv venv` to recreate it if needed.
- A single `requirements.txt` at the workspace root tracks dependencies for
  all exercises — add to it rather than creating per-exercise manifests,
  unless an exercise specifically needs isolation.
- A submodule may also carry a `visual-guide.html`: a one-page interactive
  study guide built from its notes, task, code and run log. Build or
  rebuild one with the project skill `.claude/skills/visual-study-guide/`
  (`/visual-study-guide`), which carries the template, figure recipes and
  a checker script so every guide looks and behaves the same.
- Each exercise gets one script named after the exercise itself (not per-step,
  e.g. `agent_loop.py`, not `step1_x.py`), since exercises are built up
  incrementally across multiple steps. Mark each step's code with a
  `# --- Step N: ... ---` comment header so the progression stays legible in
  one file.

## Task workflow (when the user pastes a numbered step from the guide)
The user shares individual numbered tasks/steps from an exercise one at a time
(e.g. "3. Handle the tool_use stop_reason...", often with a Why, a "You should
see" expectation, a hint question, and JS starter code). They may refer to the
same step inconsistently as "step N" or "task-N" across messages — treat these
as the same thing, matching the guide's own numbering for that exercise.

For each one:
1. Implement the change directly in the exercise's existing script (see
   Structure above — one script per exercise, not per step), translating any
   JS starter code into the equivalent Python/Anthropic SDK pattern. Add a
   `# --- Step N: ... ---` header above the new code.
2. Actually run it against the real Claude API (using the workspace `venv`
   and root `.env`) and confirm the output matches what the step says to expect
   — don't just write the code and assume it works.
3. Reply with, in this order: what changed (concise, with file/line
   references), how to run it, what output to expect, and what concept this
   step teaches (tie it back to what the exam is testing).
4. End with a short, one-line suggested commit message — no attribution
   footer/co-author line, the user does not want those in this repo.
5. Do not `git commit` or `git push` unless the user explicitly asks — they
   review the code themselves first and ask for the commit separately.

## Logging (all exercises)
- `utils/logger.py` exposes a shared `logger` (standard `logging.Logger`) —
  call `logger.info(...)`, `logger.debug(...)`, `logger.warning(...)`, etc.
  directly. Do not print() directly and do not reintroduce a `log()` wrapper
  function — use the logger object itself so any level can be used.
- Console output only shows the plain message (INFO and above) — no
  timestamps/metadata clutter on screen.
- The log file (`logs/ccarf-practise-YYYYMMDD.log`, gitignored, rotates at
  10MB) captures everything from DEBUG up, one line per call, formatted as:
  `timestamp | level | file:line | function() | memory | message`.
- `utils/message_parser.py`'s `format_message(obj)` fully pretty-prints an
  Anthropic `Message` response (every field, nothing summarized/dropped),
  wrapped in `---` divider lines so it's easy to spot in the log. It returns
  `None` for anything that isn't a Message, so callers should always do
  `logger.info(format_message(x) or x)` rather than assuming it always
  produces output.
- In any agentic loop, call `logger.info(format_message(response) or response)`
  on **every** iteration (right after checking `stop_reason`), not just on
  the final `end_turn` response. Intermediate `tool_use` responses often
  carry their own text block (Claude's reasoning before/alongside the tool
  call) and usage stats — logging only the final message hides the rest of
  the loop's lifecycle.
- Log tool call inputs/outputs (and any other dict/JSON-shaped debug data)
  with `json.dumps(data, indent=2, default=str)`, not an f-string embedding
  the raw object (e.g. `f"Tool result: {tool_result}"`). A raw dict repr
  prints as one dense, hard-to-scan line; pretty-printed JSON stays legible
  next to `format_message()`'s indented output.
- Exercise scripts use the async Anthropic client (`AsyncAnthropic`) with
  `async`/`await` for API calls, run via `asyncio.run(main())`.

## Conventions
- Keep each exercise self-contained in its own folder so it can be run/reviewed independently.
- Favor minimal, readable implementations that highlight the concept being taught over
  production-grade robustness — these are learning exercises, not shipped products.
- When a build exercise depends on the Claude API/SDK, default to the latest models
  and current SDK patterns (see the `claude-api` skill for reference).
- Since the point is for the user to read and understand the code afterward, keep
  implementations transparent and avoid over-abstracting.
- Unlike the general default, DO write comments in this repo's code — the
  point is for the user to read and understand what each piece does and why,
  so comments explaining the "what" (not just the "why") are welcome here.

## Notes
- This is a git repository (initialized at the workspace root); `.gitignore`
  excludes `venv/`, `.env`, and Python cache files.
- The machine's default Python is 3.14, which is new enough that some native
  (Rust-compiled) dependency wheels — e.g. `jiter`, pulled in by the
  `anthropic` SDK — get blocked by Windows Application Control / Smart App
  Control due to low reputation on `cp314` binaries. Python 3.12 was
  installed specifically to avoid this; keep the project venv on 3.12 rather
  than upgrading to 3.14 unless this is re-verified as fixed.
