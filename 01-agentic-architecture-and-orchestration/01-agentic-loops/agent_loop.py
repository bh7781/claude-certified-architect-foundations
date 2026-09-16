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


# --- Step 2: the agentic loop skeleton ---
#
# Goal: call client.messages.create() in a loop and use response.stop_reason
# to decide what to do next — NOT response.content[0].type. stop_reason is
# the field the API guarantees will tell us definitively whether Claude is
# done ("end_turn") or wants to call a tool ("tool_use"). Checking content
# types instead is unreliable, because a single response can mix content
# blocks (e.g. some text AND a tool_use block together).
#
# We're not executing tools yet (that's the next step) — for now we just
# detect that Claude asked for one and stop, so we don't loop forever
# re-sending the same request without ever giving Claude a tool result.


def run_agent_loop(user_prompt: str):
    # `messages` is the running conversation history we send on every call.
    messages = [{"role": "user", "content": user_prompt}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        print(f"stop_reason: {response.stop_reason}")

        if response.stop_reason == "end_turn":
            # Claude finished its answer without needing any tool. Done.
            break

        if response.stop_reason == "tool_use":
            # Claude wants to call one of our tools. Actually running the
            # tool and sending the result back is what the next step adds.
            print("Claude requested a tool call - handling this is the next step, stopping here for now.")
            break

        # Anything else (e.g. max_tokens, stop_sequence) — stop and surface it.
        print(f"Unhandled stop_reason: {response.stop_reason}")
        break

    return response


if __name__ == "__main__":
    print("=== Step 1: Register tools so Claude knows they're available ===")
    print_registered_tools()

    print("=== Step 2: Run the agentic loop and branch on stop_reason ===")

    print("--- Prompt that should end in a plain answer (end_turn) ---")
    plain_response = run_agent_loop("what is the capital of France?")
    print(plain_response.content)

    print()
    print("--- Prompt that should trigger a tool call (tool_use) ---")
    tool_response = run_agent_loop("47 * 12")
    print(tool_response.content)
