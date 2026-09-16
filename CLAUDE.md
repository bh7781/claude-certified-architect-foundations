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
- Each exercise gets one script named after the exercise itself (not per-step,
  e.g. `agent_loop.py`, not `step1_x.py`), since exercises are built up
  incrementally across multiple steps. Mark each step's code with a
  `# --- Step N: ... ---` comment header so the progression stays legible in
  one file.

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
