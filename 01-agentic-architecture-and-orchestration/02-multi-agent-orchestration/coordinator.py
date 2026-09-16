"""
Build a Hub-and-Spoke Research Coordinator (CCAR-F practice exercise).

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

# .env and utils/ both live at the workspace root (two levels up from this
# file), and are shared across all exercises rather than duplicated per-exercise.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(WORKSPACE_ROOT / ".env")
sys.path.insert(0, str(WORKSPACE_ROOT))

from utils.logger import logger
from utils.message_parser import format_message


# AsyncAnthropic() automatically reads the ANTHROPIC_API_KEY environment
# variable (loaded above from the root .env).
client = AsyncAnthropic()

# The model the coordinator itself reasons with (decomposition, aggregation,
# refinement). Subagents get their own model choice in a later step.
COORDINATOR_MODEL = "claude-haiku-4-5-20251001"


# --- Step 1: coordinator hub + subagent definitions ---
#
# Goal: hub-and-spoke architecture means ALL communication flows through the
# coordinator - subagents never talk to each other, and never see the raw
# topic or each other's output unless the coordinator explicitly hands it to
# them. So the coordinator is the only thing that owns: the system prompt
# framing it as the orchestrating hub, the roster of subagents it can
# delegate to, and the pipeline (decompose -> delegate -> aggregate ->
# refine) that turns a topic into a finished report. The subagent
# definitions here are just roles/system-prompts for now (spawned for real
# in Step 3); nothing about "how a subagent works internally" belongs on the
# coordinator - it only needs to know what a subagent is called and what to
# tell it.

WEB_SEARCH_AGENT = {
    "name": "web_search_agent",
    "system_prompt": (
        "You are a web search specialist. Given a research subtopic, find "
        "current, factual information about it and report structured "
        "findings with source URLs and a confidence level for each finding."
    ),
}

DOC_ANALYSIS_AGENT = {
    "name": "doc_analysis_agent",
    "system_prompt": (
        "You are a document analysis specialist. Given a research subtopic, "
        "analyze and synthesize what is known about it from established, "
        "in-depth sources (papers, reports, reference material) and report "
        "structured findings with confidence levels for each finding."
    ),
}


class Coordinator:
    """
    The central hub. Owns task decomposition, subagent selection/delegation,
    result aggregation, and iterative refinement - the subagents themselves
    stay dumb and stateless (see Step 3: subagent isolation).
    """

    def __init__(self):
        self.system_prompt = (
            "You are a research coordinator. Decompose topics into "
            "comprehensive subtopics, delegate to specialist subagents, "
            "aggregate results, and identify coverage gaps."
        )
        self.subagents = [WEB_SEARCH_AGENT, DOC_ANALYSIS_AGENT]

    async def decompose(self, topic: str) -> list[str]:
        """
        Break a broad topic into subtopics. This is a minimal first pass
        (one API call, ask for a JSON array) just so the pipeline below runs
        end-to-end - Step 2 replaces this with the two-phase, breadth-checked
        version that guards against narrow decomposition.
        """
        prompt = (
            f"List the major subtopics for: {topic}. "
            f"Return ONLY a JSON array of short subtopic strings, no other text."
        )
        response = await client.messages.create(
            model=COORDINATOR_MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        logger.info(format_message(response) or response)

        text_block = next(
            (block for block in response.content if block.type == "text"), None
        )
        raw_text = text_block.text.strip() if text_block else "[]"
        # Claude sometimes wraps JSON in a ```json fence despite the
        # "no other text" instruction - strip that before parsing.
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.removeprefix("json").strip()

        return json.loads(raw_text)

    async def research(self, topic: str) -> dict[str, Any]:
        """
        Run a topic through the coordinator's pipeline. Delegation (Step 3),
        aggregation (Step 4), and iterative refinement (Step 5) land in
        later steps - for now this proves the hub skeleton (system prompt,
        subagent roster, decomposition) works end-to-end against the real API.
        """
        logger.info(f"=== Coordinator starting research on: '{topic}' ===")

        subtopics = await self.decompose(topic)
        logger.info(f"Decomposed '{topic}' into {len(subtopics)} subtopic(s): {subtopics}")

        report = {
            "topic": topic,
            "subtopics": subtopics,
            # Populated by delegation (Step 3) and aggregation (Step 4).
            "sections": [],
        }
        return report


async def main():
    logger.info("=== Execution started ===")
    start_time = time.perf_counter()

    logger.info("=== Step 1: coordinator skeleton - decompose a broad topic ===")
    coordinator = Coordinator()
    report = await coordinator.research("renewable energy technologies")
    logger.info(f"Report:\n{json.dumps(report, indent=2, default=str)}")

    elapsed_seconds = time.perf_counter() - start_time
    logger.info(f"=== Execution finished (total time taken: {elapsed_seconds:.2f}s) ===")


if __name__ == "__main__":
    asyncio.run(main())
