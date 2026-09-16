"""
Build a Multi-Tool Agent Loop (CCAR-F practice exercise).

This script is built up incrementally, one step at a time, across this
exercise. Each step is marked with a "--- Step N: ... ---" header below so
it's clear what was added when, without needing separate step1.py, step2.py
files.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from anthropic import AsyncAnthropic

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

# AsyncAnthropic() automatically reads the ANTHROPIC_API_KEY environment
# variable (loaded above from the root .env), so no key is passed explicitly.
# We use the async client (instead of Anthropic()) so that awaiting the API
# call doesn't block the whole thread - while we're waiting on the network,
# Python's event loop is free to do other work instead of just sitting idle.
client = AsyncAnthropic()


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


# --- Step 4: handle stop_reason == "end_turn" by returning the final text ---
#
# Goal: end_turn means Claude is done - no more tool calls needed. The
# content list can hold more than one block, so we specifically look for
# the one with type == "text" (not content[0] - that block isn't always
# first, e.g. right after a tool call Claude sometimes leads with other
# content). Its `.text` field is the actual answer to show the user, so
# that's what the loop returns - not the raw Message object.


async def run_agent_loop(user_prompt: str):
    logger.info(f"User prompt: {user_prompt}")

    # `messages` is the running conversation history we send on every call.
    # Typed as `dict[str, Any]` because "content" can be either a plain
    # string (a normal text turn) or a list of blocks (a tool_use /
    # tool_result turn) - both are valid, so we tell the type checker that
    # up front instead of letting it assume "content" is always a string.
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    # --- Step 5: track iteration count ---
    #
    # Goal: make the loop's lifecycle visible. A prompt that needs sequential
    # tool calls (e.g. search for a value, then calculate with it) should
    # take multiple iterations - one API call per iteration - before Claude
    # finally reaches end_turn. Counting iterations lets us confirm that.
    iteration_count = 0

    while True:
        iteration_count += 1
        logger.info(f"--- Loop iteration {iteration_count} ---")
        # type: ignore below - the SDK expects very specific TypedDict
        # shapes for `tools` and `messages`, but plain dicts in exactly
        # this shape are what the Anthropic API docs themselves use, so
        # this is a type-checker nitpick rather than a real bug.
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=TOOLS,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        logger.info(f"stop_reason: {response.stop_reason}")

        # Log the full response on every iteration (not just the final one) -
        # so the whole loop's lifecycle is visible, including any text Claude
        # sends alongside a tool_use block and the usage/token counts for
        # each individual API call.
        logger.info(format_message(response) or response)

        if response.stop_reason == "end_turn":
            text_block = next(
                (block for block in response.content if block.type == "text"), None
            )
            final_text = text_block.text if text_block else ""
            logger.info(f"Loop finished after {iteration_count} iteration(s)")
            return final_text, iteration_count

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
            # json.dumps(..., indent=2) instead of str(tool_result) - a raw
            # dict repr crams everything onto one dense, hard-to-scan line.
            logger.info(f"Tool result:\n{json.dumps(tool_result, indent=2, default=str)}")

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
        return "", iteration_count


async def main():
    logger.info("=== Execution started ===")
    start_time = time.perf_counter()

    # logger.info("=== Step 1: Register tools so Claude knows they're available ===")
    # print_registered_tools()

    # logger.info("=== Step 2: Run the agentic loop and branch on stop_reason ===")

    # logger.info("--- Prompt that should end in a plain answer (end_turn) ---")
    # plain_answer, plain_iterations = await run_agent_loop("what is the capital of France? (answer in 1 word)")
    # logger.info(f"Final answer: {plain_answer} (iterations: {plain_iterations})")

    # logger.info("")
    # logger.info("--- Prompt that should trigger a tool call (tool_use) and use the result ---")
    # tool_answer, tool_iterations = await run_agent_loop("47 * 12")
    # logger.info(f"Final answer: {tool_answer} (iterations: {tool_iterations})")

    logger.info("")
    logger.info("=== Step 5: sequential tool calls - search result feeds a calculation ===")
    result, iteration_count = await run_agent_loop("Search for the current price of Bitcoin and calculate what 3.5 coins would cost")
    logger.info(f"Iterations: {iteration_count}")
    logger.info(f"Result: {result}")

    elapsed_seconds = time.perf_counter() - start_time
    logger.info(f"=== Execution finished (total time taken: {elapsed_seconds:.2f}s) ===")


if __name__ == "__main__":
    asyncio.run(main())
