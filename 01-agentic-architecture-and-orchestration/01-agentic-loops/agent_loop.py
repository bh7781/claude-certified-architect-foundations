"""
Build a Multi-Tool Agent Loop (CCAR-F practice exercise).

This script is built up incrementally, one step at a time, across this
exercise. Each step is marked with a "--- Step N: ... ---" header below so
it's clear what was added when, without needing separate step1.py, step2.py
files.
"""

from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

from tools import TOOLS

# .env lives at the workspace root (two levels up from this file), and is
# shared across all exercises rather than duplicated per-exercise.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(WORKSPACE_ROOT / ".env")


# --- Step 1: Claude API client + tool definitions ---
#
# Goal: set up a client and register the two tools (calculator, web_search)
# so Claude can be told about them via the Messages API's `tools` parameter.
# No API call happens yet — this step is just about the client and the tool
# definitions being correctly formed.

# Anthropic() automatically reads the ANTHROPIC_API_KEY environment
# variable (loaded above from the root .env), so no key is passed explicitly.
client = Anthropic()


def print_registered_tools():
    """Print each tool's definition so we can visually confirm it's well-formed."""
    print(f"Registered {len(TOOLS)} tool(s):\n")
    for tool in TOOLS:
        print(f"- name: {tool['name']}")
        print(f"  description: {tool['description']}")
        print(f"  input_schema: {tool['input_schema']}")
        print()


if __name__ == "__main__":
    print_registered_tools()
