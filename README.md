# Claude Certified Architect Foundations (CCAR-F) — Practice

Hands-on build exercises from the [Claude Certification Guide](https://claudecertificationguide.com/), done as practice for the CCAR-F exam.

## Structure

Exercises are organized by certification topic, numbered in the order they were built:

```
01-agentic-architecture-and-orchestration/
  01-agentic-loops/
    tools.py         # tool implementations + tool definitions
    agent_loop.py     # client setup and the agent loop itself
```

Each exercise folder contains one script that's built up step by step, with `# --- Step N: ... ---` comments marking each stage.

## Running an exercise

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Add your `ANTHROPIC_API_KEY` to a `.env` file at the repo root, then run any exercise script directly, e.g.:

```bash
venv\Scripts\python 01-agentic-architecture-and-orchestration\01-agentic-loops\agent_loop.py
```
