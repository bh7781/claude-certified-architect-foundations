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

# Coverage threshold (Step 4): a section needs at least this many findings
# to count as "well-covered" rather than merely "partial" - a single thin
# finding technically isn't a gap, but isn't substantive coverage either.
MIN_FINDINGS_FOR_SUBSTANTIVE_COVERAGE = 2

# Iterative refinement (Step 5): keep re-delegating gaps/partial subtopics
# until overall completeness clears this threshold, or until the iteration
# cap is hit - the cap is what stops an unresolvable gap from looping forever.
COMPLETENESS_THRESHOLD = 0.9
MAX_REFINEMENT_ITERATIONS = 3


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

def _parse_json_response(text: str) -> Any:
    """
    Claude sometimes wraps JSON (array or object) in a ```json fence even
    when told "no other text" - strip that before parsing. Shared by
    decomposition (Step 2, arrays) and delegation (Step 3, objects) since
    both just ask for plain JSON back.
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
        return _parse_json_response(text_block.text) if text_block else []

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

    async def delegate_to_subagent(
        self,
        agent: dict[str, str],
        subtopic: str,
        research_goal: str,
        prior_findings: str | None = None,
    ) -> dict[str, Any]:
        """
        Hand one subtopic to one subagent. Subagent isolation means the
        subagent has NO memory of this conversation, the original topic, or
        any other subagent's work - it only knows what's in this one prompt.
        So every piece of context it could possibly need has to be spelled
        out explicitly here, every time:
          - the specific subtopic it's assigned (not just "the topic")
          - the broader research goal, so it knows *why* this subtopic
            matters and can scope its findings accordingly
          - the expected output format, so results can be aggregated later
          - any prior findings relevant to its task - if we skip this, a
            subagent re-delegated to in Step 5 (gap-filling) would silently
            re-do work or contradict earlier findings, because it has no way
            to know they exist otherwise.
        """
        prior_findings_text = (
            prior_findings
            if prior_findings
            else "None yet - this is the first research pass for this subtopic."
        )
        prompt = (
            f"Research subtopic: {subtopic}\n"
            f"Broader research goal: {research_goal}\n"
            f"Prior findings relevant to this subtopic: {prior_findings_text}\n\n"
            f"Return structured findings as a JSON object with this exact "
            f'shape: {{"subtopic": string, "findings": [{{"fact": string, '
            f'"source_url": string, "confidence": "high" | "medium" | "low"}}]}}. '
            f"Return ONLY the JSON object, no other text."
        )
        response = await client.messages.create(
            model=COORDINATOR_MODEL,
            max_tokens=2048,
            system=agent["system_prompt"],
            messages=[{"role": "user", "content": prompt}],
        )
        logger.info(format_message(response) or response)

        text_block = next(
            (block for block in response.content if block.type == "text"), None
        )
        raw_text = text_block.text if text_block else "{}"
        try:
            parsed = _parse_json_response(raw_text)
        except json.JSONDecodeError:
            logger.warning(
                f"Subagent '{agent['name']}' returned non-JSON output for "
                f"subtopic '{subtopic}' - keeping raw text instead."
            )
            parsed = {"findings": [], "raw_text": raw_text}

        # Force "subtopic" to the value WE assigned rather than trusting the
        # subagent's echoed copy - coverage evaluation (Step 4) matches
        # sections back to subtopics by this field, so it needs to be exact.
        parsed["subtopic"] = subtopic
        return {"agent": agent["name"], **parsed}

    def evaluate_coverage(
        self, subtopics: list[str], sections: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Compare what was ASSIGNED (subtopics) against what actually came
        back (sections) - this is the coordinator's job, not something a
        subagent can do for itself, since only the hub sees both sides.
        Three buckets instead of a binary covered/gap: a subtopic with zero
        findings is a full gap, but one with only a single thin finding is
        "partial" - technically not empty, but not enough to trust either,
        so it should still be a candidate for re-delegation in Step 5.
        """
        # Map each subtopic to the BEST finding count across all sections for
        # it. Sections isn't guaranteed to have one entry per subtopic -
        # Step 5's refinement loop appends a new section each time it
        # re-delegates a gap, so a subtopic can have multiple attempts on
        # record. Taking the max (not the first/last) means an earlier good
        # attempt is never lost if a later retry happens to do worse.
        # "subtopic" is a key we force onto every section ourselves (see
        # delegate_to_subagent), so this lookup is exact, not a fuzzy match.
        finding_counts: dict[str, int] = {}
        for section in sections:
            subtopic = section.get("subtopic", "")
            count = len(section.get("findings", []))
            finding_counts[subtopic] = max(finding_counts.get(subtopic, 0), count)

        well_covered, partial, gaps = [], [], []
        for subtopic in subtopics:
            count = finding_counts.get(subtopic, 0)
            if count == 0:
                gaps.append(subtopic)
            elif count < MIN_FINDINGS_FOR_SUBSTANTIVE_COVERAGE:
                partial.append(subtopic)
            else:
                well_covered.append(subtopic)

        completeness = len(well_covered) / len(subtopics) if subtopics else 0.0
        return {
            "well_covered": well_covered,
            "partial": partial,
            "gaps": gaps,
            "completeness": completeness,
        }

    @staticmethod
    def _summarize_existing_section(subtopic: str, sections: list[dict[str, Any]]) -> str:
        """
        Build the "prior findings" context (Step 3) for a re-delegation
        (Step 5). A subagent retrying a gap has no memory of its own earlier
        attempt - without this, it might repeat the exact same shallow
        search, or waste effort re-discovering a fact it already found.
        """
        existing_findings = [
            finding
            for section in sections
            if section.get("subtopic") == subtopic
            for finding in section.get("findings", [])
        ]
        if not existing_findings:
            return (
                "A previous research attempt on this exact subtopic returned "
                "ZERO findings. Try a different angle or more specific query."
            )
        facts = "; ".join(
            finding.get("fact", "") for finding in existing_findings if isinstance(finding, dict)
        )
        return (
            f"A previous attempt found only {len(existing_findings)} finding(s), "
            f"not enough for substantive coverage: {facts}. Find NEW, "
            f"additional, substantive facts beyond these - don't just repeat them."
        )

    async def refine_coverage(
        self, topic: str, subtopics: list[str], sections: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
        """
        The loop that makes this a coordinator rather than a one-shot
        dispatcher: keep checking coverage and re-delegating into whatever
        is missing or thin, until completeness clears the threshold or the
        iteration cap is hit. Each iteration targets ONLY the gaps/partial
        subtopics from the last check - already-well-covered subtopics are
        never re-delegated, so cost scales with what's actually missing.
        """
        coverage = self.evaluate_coverage(subtopics, sections)
        iteration = 0

        while coverage["completeness"] < COMPLETENESS_THRESHOLD and iteration < MAX_REFINEMENT_ITERATIONS:
            iteration += 1
            targets = coverage["gaps"] + coverage["partial"]
            logger.info(
                f"Refinement iteration {iteration}: completeness "
                f"{coverage['completeness']:.0%} < {COMPLETENESS_THRESHOLD:.0%} threshold - "
                f"re-delegating {len(targets)} subtopic(s): {targets}"
            )

            redelegations = [
                self.delegate_to_subagent(
                    self.subagents[i % len(self.subagents)],
                    subtopic,
                    topic,
                    prior_findings=self._summarize_existing_section(subtopic, sections),
                )
                for i, subtopic in enumerate(targets)
            ]
            new_sections = list(await asyncio.gather(*redelegations))
            # Append rather than replace - evaluate_coverage takes the best
            # finding count per subtopic across ALL recorded attempts, so an
            # earlier partial result is never silently discarded.
            sections = sections + new_sections

            coverage = self.evaluate_coverage(subtopics, sections)
            logger.info(f"Coverage after iteration {iteration}:\n{json.dumps(coverage, indent=2)}")

        if coverage["completeness"] < COMPLETENESS_THRESHOLD:
            logger.warning(
                f"Refinement stopped after {iteration} iteration(s) - completeness "
                f"{coverage['completeness']:.0%} still below the "
                f"{COMPLETENESS_THRESHOLD:.0%} threshold. Remaining gaps: {coverage['gaps']}"
            )

        return sections, coverage, iteration

    async def research(self, topic: str) -> dict[str, Any]:
        """
        Run a topic through the coordinator's full pipeline: decompose,
        delegate to a subagent per subtopic, then aggregate, evaluate
        coverage, and iteratively refine any gaps found.
        """
        logger.info(f"=== Coordinator starting research on: '{topic}' ===")

        subtopics = await self.decompose(topic)
        logger.info(f"Decomposed '{topic}' into {len(subtopics)} subtopic(s): {subtopics}")

        # Round-robin each subtopic to one of the two subagent types. Each
        # delegation is fully independent (subagent isolation cuts both
        # ways - no shared state also means no cross-call dependency), so
        # they can run concurrently via asyncio.gather instead of awaiting
        # them one at a time.
        delegations = [
            self.delegate_to_subagent(self.subagents[i % len(self.subagents)], subtopic, topic)
            for i, subtopic in enumerate(subtopics)
        ]
        logger.info(f"Delegating {len(delegations)} subtopic(s) across {len(self.subagents)} subagent(s)")
        sections = list(await asyncio.gather(*delegations))

        # --- Step 5: aggregate, evaluate coverage, and refine any gaps ---
        sections, coverage, refinement_iterations = await self.refine_coverage(topic, subtopics, sections)
        logger.info(f"Refinement used {refinement_iterations} iteration(s)")

        report = {
            "topic": topic,
            "subtopics": subtopics,
            "sections": sections,
            "coverage": coverage,
            "refinement_iterations": refinement_iterations,
        }
        return report


# --- Step 6: final acceptance test + failure-tracing diagnostic ---
#
# Goal: verify the FINAL delegated output (report["sections"], with actual
# findings) covers every required category - not just whether decomposition
# happened to mention the word. Two-stage check, deliberately, so a failure
# can be traced to the right part of the pipeline - this mirrors the exam's
# diagnostic: an incomplete report is a decomposition bug if the category
# was never assigned, or a delegation/context-passing bug if it was assigned
# but the subagent came back empty.


def verify_final_coverage(report: dict[str, Any], required_categories: list[str]) -> bool:
    subtopics_lower = [subtopic.lower() for subtopic in report["subtopics"]]

    # Best finding count per subtopic (case-insensitive) - mirrors how
    # evaluate_coverage aggregates across possibly-multiple attempts.
    finding_counts: dict[str, int] = {}
    for section in report["sections"]:
        subtopic_lower = section.get("subtopic", "").lower()
        count = len(section.get("findings", []))
        finding_counts[subtopic_lower] = max(finding_counts.get(subtopic_lower, 0), count)

    all_covered = True
    for category in required_categories:
        matching_subtopics = [st for st in subtopics_lower if category in st]

        if not matching_subtopics:
            logger.warning(
                f"Missing '{category}': not present in decomposition at all - "
                f"the fix is in decompose(), not delegation."
            )
            all_covered = False
            continue

        has_substantive_findings = any(
            finding_counts.get(st, 0) > 0 for st in matching_subtopics
        )
        if not has_substantive_findings:
            logger.warning(
                f"Missing '{category}': decomposition included "
                f"{matching_subtopics}, but no section for it has any "
                f"findings - the fix is in delegation/context passing, not "
                f"decomposition."
            )
            all_covered = False

    return all_covered


async def main():
    logger.info("=== Execution started ===")
    start_time = time.perf_counter()

    coordinator = Coordinator()

    # --- Step 5 demo: force a coverage gap so the refinement loop actually
    # has something to do. The real pipeline below reached 100% completeness
    # on its first pass in earlier runs, so this proves the loop's mechanics
    # (targeted re-delegation, threshold check, iteration cap) independently
    # of whether the initial delegation happens to need it.
    logger.info("=== Step 5 demo: refine_coverage() against a manufactured gap ===")
    demo_topic = "renewable energy technologies"
    demo_subtopics = ["Nuclear Fusion Energy", "Solar Photovoltaic Technology"]
    demo_sections = [
        {"agent": "web_search_agent", "subtopic": "Nuclear Fusion Energy", "findings": []},
        {
            "agent": "doc_analysis_agent",
            "subtopic": "Solar Photovoltaic Technology",
            "findings": [
                {
                    "fact": "Crystalline silicon panels dominate the current solar market.",
                    "source_url": "https://example.com/solar",
                    "confidence": "high",
                },
                {
                    "fact": "Panel efficiency has climbed steadily over the past decade.",
                    "source_url": "https://example.com/solar-efficiency",
                    "confidence": "medium",
                },
            ],
        },
    ]
    refined_sections, refined_coverage, iterations_used = await coordinator.refine_coverage(
        demo_topic, demo_subtopics, demo_sections
    )
    logger.info(f"Demo refinement used {iterations_used} iteration(s)")
    logger.info(f"Demo final coverage:\n{json.dumps(refined_coverage, indent=2)}")

    logger.info("")
    logger.info("=== Step 6: full pipeline against the required-category acceptance test ===")
    report = await coordinator.research("renewable energy technologies")
    logger.info(f"Report:\n{json.dumps(report, indent=2, default=str)}")

    required_categories = ["solar", "wind", "geothermal", "tidal", "biomass", "fusion"]
    full_coverage = verify_final_coverage(report, required_categories)
    logger.info(
        f"Coverage evaluation completeness: {report['coverage']['completeness']:.0%} "
        f"({len(report['coverage']['gaps'])} gap(s), {len(report['coverage']['partial'])} partial)"
    )
    logger.info(
        "Full coverage - all six required categories present with substantive findings"
        if full_coverage
        else "Coverage check FAILED - see warnings above for the traced failure stage"
    )

    elapsed_seconds = time.perf_counter() - start_time
    logger.info(f"=== Execution finished (total time taken: {elapsed_seconds:.2f}s) ===")


if __name__ == "__main__":
    asyncio.run(main())
