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

def _parse_json_array(text: str) -> list[str]:
    """
    Claude sometimes wraps a JSON array in a ```json fence even when told
    "no other text" / "return as JSON array" - strip that before parsing.
    Shared by both decomposition phases (Step 2) since they both ask for a
    plain JSON array back.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    return json.loads(text)


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

    async def _ask_for_subtopics(self, prompt: str) -> list[str]:
        """Single API call that asks for a JSON array of subtopic strings back."""
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
        return _parse_json_array(text_block.text) if text_block else []

    async def decompose(self, topic: str) -> list[str]:
        """
        Break a broad topic into subtopics, guarding against the "narrow
        decomposition" exam failure pattern (e.g. only listing solar + wind
        for renewable energy and silently missing geothermal, tidal, biomass,
        fusion). Two phases:

          1. Enumerate: ask broadly for ALL major categories, explicitly
             framing an incomplete category list as a critical failure -
             this is deliberately a *generation* pass, not a narrowing one.
          2. Validate: hand the candidate list back to the model and ask it
             to check its own breadth and add anything missing, before
             committing to a final list. This catches gaps the first pass's
             single generation might have missed.
        """
        # --- Phase 1: broad enumeration ---
        enumerate_prompt = (
            f"List ALL major subtopics for: {topic}. Ensure comprehensive "
            f"breadth across every major subcategory of this subject - "
            f"missing an entire category is a critical failure. Include at "
            f"least 5 distinct subtopics. Return ONLY a JSON array of short "
            f"subtopic strings, no other text."
        )
        candidate_subtopics = await self._ask_for_subtopics(enumerate_prompt)
        logger.info(f"Phase 1 (enumerate) candidates: {candidate_subtopics}")

        # --- Phase 2: validate breadth, fill any gaps ---
        validate_prompt = (
            f"Here is a candidate list of subtopics for the broad topic "
            f"'{topic}':\n{json.dumps(candidate_subtopics)}\n\n"
            f"Check this list for comprehensive breadth - are there any "
            f"major subcategories of '{topic}' that are missing entirely? "
            f"Consider the FULL maturity spectrum, not just mainstream, "
            f"widely-deployed categories: also include experimental, "
            f"research-stage, or not-yet-commercial technologies if they "
            f"are a recognized category of this subject (e.g. for renewable "
            f"energy, fusion is still experimental but is a distinct, "
            f"well-known category that a narrow decomposition would miss). "
            f"Return the FINAL, complete JSON array of subtopic strings: "
            f"the candidates above plus any missing categories added in. "
            f"Return ONLY the JSON array, no other text."
        )
        final_subtopics = await self._ask_for_subtopics(validate_prompt)
        logger.info(f"Phase 2 (validate) final subtopics: {final_subtopics}")

        if len(final_subtopics) < 5:
            logger.warning(
                f"Decomposition produced only {len(final_subtopics)} subtopic(s) "
                f"for '{topic}' - below the 5-subtopic breadth floor, likely "
                f"a narrow decomposition failure."
            )

        return final_subtopics

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

    logger.info("=== Step 2: two-phase decomposition - enumerate then validate breadth ===")
    coordinator = Coordinator()
    report = await coordinator.research("renewable energy technologies")
    logger.info(f"Report:\n{json.dumps(report, indent=2, default=str)}")

    required_categories = ["solar", "wind", "geothermal", "tidal", "biomass", "fusion"]
    subtopics_lower = " ".join(report["subtopics"]).lower()
    missing = [cat for cat in required_categories if cat not in subtopics_lower]
    logger.info(
        "Coverage check: Full coverage" if not missing
        else f"Coverage check: Missing {missing}"
    )

    elapsed_seconds = time.perf_counter() - start_time
    logger.info(f"=== Execution finished (total time taken: {elapsed_seconds:.2f}s) ===")


if __name__ == "__main__":
    asyncio.run(main())
