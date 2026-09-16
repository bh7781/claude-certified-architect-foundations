"""
Build a Multi-Tool Agent Loop (CCAR-F practice exercise).

This script is built up incrementally, one step at a time, across this
exercise. Each step is marked with a "--- Step N: ... ---" header below so
it's clear what was added when, without needing separate step1.py, step2.py
files.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

from tools import TOOLS, TOOL_IMPLEMENTATIONS

# .env and utils/ both live at the workspace root (two levels up from this
# file), and are shared across all exercises rather than duplicated per-exercise.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(WORKSPACE_ROOT / ".env")
sys.path.insert(0, str(WORKSPACE_ROOT))

from utils.logger import logger
from utils.message_parser import format_message


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
    logger.info(f"Registered {len(TOOLS)} tool(s):\n")
    for tool in TOOLS:
        logger.info(f"- name: {tool['name']}")
        logger.info(f"  description: {tool['description']}")
        logger.info(f"  input_schema: {tool['input_schema']}")
        logger.info("")


# --- Step 2: the agentic loop skeleton ---
#
# Goal: call client.messages.create() in a loop and use response.stop_reason
# to decide what to do next — NOT response.content[0].type. stop_reason is
# the field the API guarantees will tell us definitively whether Claude is
# done ("end_turn") or wants to call a tool ("tool_use"). Checking content
# types instead is unreliable, because a single response can mix content
# blocks (e.g. some text AND a tool_use block together).


# --- Step 3: handle stop_reason == "tool_use" by actually running the tool ---
#
# Goal: when Claude asks for a tool, find the tool_use content block (it has
# `name` and `input`), run the matching Python function, and send the result
# back so Claude can carry on. The result goes back as a new "user" message
# containing a `tool_result` block, matched to the request via `tool_use_id`.
# Then we loop again so Claude can respond using that result.


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

        logger.info(f"stop_reason: {response.stop_reason}")

        if response.stop_reason == "end_turn":
            # Claude finished its answer without needing any tool. Done.
            break

        if response.stop_reason == "tool_use":
            # Find the tool_use block - it tells us which tool to call
            # (`name`) and with what arguments (`input`).
            tool_use_block = next(
                block for block in response.content if block.type == "tool_use"
            )
            logger.info(f"Claude wants to call tool '{tool_use_block.name}' with input {tool_use_block.input}")

            # Look up and run the matching Python function from tools.py.
            tool_function = TOOL_IMPLEMENTATIONS[tool_use_block.name]
            tool_result = tool_function(**tool_use_block.input)
            logger.info(f"Tool result: {tool_result}")

            # Add Claude's tool_use turn to the conversation history...
            messages.append({"role": "assistant", "content": response.content})

            # ...then add our tool result as the next "user" turn. The
            # tool_use_id ties this result back to the specific tool call
            # Claude made, which matters when there's more than one.
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,
                            "content": str(tool_result),
                        }
                    ],
                }
            )

            continue  # loop again - Claude now responds using the tool result

        # Anything else (e.g. max_tokens, stop_sequence) — stop and surface it.
        logger.warning(f"Unhandled stop_reason: {response.stop_reason}")
        break

    return response


if __name__ == "__main__":
    logger.info("=== Step 1: Register tools so Claude knows they're available ===")
    print_registered_tools()

    logger.info("=== Step 2: Run the agentic loop and branch on stop_reason ===")

    logger.info("--- Prompt that should end in a plain answer (end_turn) ---")
    plain_response = run_agent_loop("what is the capital of France? (answer in 1 word)")
    # format_message() only pretty-prints actual Message responses - it
    # returns None for anything else, so we fall back to logging as-is.
    logger.info(format_message(plain_response) or plain_response)

    logger.info("")
    logger.info("--- Prompt that should trigger a tool call (tool_use) and use the result ---")
    tool_response = run_agent_loop("47 * 12")
    logger.info(format_message(tool_response) or tool_response)
