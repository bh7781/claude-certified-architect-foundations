# Build a Hub-and-Spoke Research Coordinator
What you'll learn
- How hub-and-spoke architecture centralises all communication through a coordinator
- Why subagent isolation means every piece of context must be explicitly passed
- How to implement broad task decomposition that avoids the narrow decomposition failure
- How iterative refinement loops detect and fill coverage gaps
- Why tracing failures to the coordinator decomposition is the correct diagnostic approach


1. Create a coordinator agent that accepts a broad research topic as input
Why: The coordinator is the central hub in hub-and-spoke architecture. The exam tests whether you understand that the coordinator owns task decomposition, subagent selection, and result aggregation — not the subagents.

You should see: A coordinator function that accepts a topic string and returns a structured research report. It should have a system prompt defining its role as the orchestrating hub.


Think about what responsibilities the coordinator has: decomposition, delegation, aggregation, and refinement. What does the initial setup need?


The coordinator needs a system prompt, a list of available subagent definitions, and logic to process a topic through decomposition, delegation, and aggregation phases.

Starter Code
const coordinator = {
  systemPrompt: "You are a research coordinator. Decompose topics into comprehensive subtopics, delegate to specialist subagents, aggregate results, and identify coverage gaps.",
  subagents: [webSearchAgent, docAnalysisAgent],
  async research(topic: string) {
    const subtopics = await this.decompose(topic);
    // delegation and aggregation follow
  }
};

2. Implement task decomposition logic that breaks the topic into at least 5 distinct subtopics covering the full breadth of the subject
Why: Narrow decomposition is a specific exam failure pattern. The coordinator that only assigns solar and wind for renewable energy misses entire categories. The exam expects you to recognise that incomplete output traces back to the coordinator decomposition.

You should see: A decomposition function that produces 5 or more subtopics for any broad topic. For renewable energy, it should cover solar, wind, geothermal, tidal, biomass, and fusion at minimum.


How would you ensure breadth? Consider prompting the coordinator to explicitly enumerate categories before narrowing down.


Use a two-phase approach: first generate broad categories, then validate that no major area is missing. The coordinator prompt should instruct the model to consider all major subcategories of the topic.

Starter Code
async decompose(topic: string): Promise<string[]> {
  const response = await client.messages.create({
    model: "claude-sonnet-5",
    max_tokens: 1024,
    messages: [{
      role: "user",
      content: `List ALL major subtopics for: ${topic}. Ensure comprehensive breadth — missing an entire category is a critical failure. Return as JSON array.`
    }]
  });
  return JSON.parse(response.content.find(b => b.type === "text").text);
}

3. Spawn two subagents (web search and document analysis) with explicit context passing — include all relevant information in each subagent prompt
Why: Subagent isolation means no shared memory and no inherited context. The exam heavily tests this: if a subagent produces poor results, check whether the coordinator gave it sufficient context, not whether the subagent itself is flawed.

You should see: Two subagent invocations where each receives the full assigned subtopic, the research goal, and any relevant context from prior agents — all explicitly included in the prompt.


Remember: subagents start with a blank slate. What information do they need to do their job effectively?


Each subagent prompt must include: the specific subtopic assigned, the broader research goal for context, the expected output format, and any prior findings relevant to its task. Do not assume the subagent knows anything.

Starter Code
async delegateToSubagent(agent: AgentDefinition, subtopic: string, context: string) {
  return await client.messages.create({
    model: "claude-sonnet-5",
    max_tokens: 2048,
    system: agent.systemPrompt,
    messages: [{
      role: "user",
      content: `Research subtopic: ${subtopic}\nBroader goal: ${context}\nReturn structured findings with source URLs and confidence levels.`
    }]
  });
}

4. Aggregate results from both subagents and evaluate coverage completeness
Why: The coordinator must evaluate whether the combined results cover the full breadth of the original topic. This is where iterative refinement starts — gaps detected here trigger re-delegation.

You should see: An aggregation function that combines results from both subagents and produces a coverage assessment listing which subtopics are well-covered, partially covered, or missing.


What does the coordinator need to check? Compare the subtopics assigned against the findings actually returned.


Build a coverage map: for each original subtopic, check whether the aggregated results contain substantive findings. Flag any subtopic with no findings or only superficial coverage.

Starter Code
async evaluateCoverage(subtopics: string[], results: Finding[]): Promise<CoverageReport> {
  const covered = subtopics.filter(st =>
    results.some(r => r.subtopic === st && r.findings.length > 0)
  );
  const gaps = subtopics.filter(st => !covered.includes(st));
  return { covered, gaps, completeness: covered.length / subtopics.length };
}

5. Implement an iterative refinement loop: if the coordinator identifies coverage gaps, re-delegate to subagents with targeted queries and re-invoke until coverage is sufficient
Why: Iterative refinement is a core coordinator responsibility the exam tests. A single-shot delegation is not enough — the coordinator must evaluate output and re-delegate for gaps. This distinguishes a coordinator from a simple dispatcher.

You should see: A loop that checks coverage, identifies gaps, sends targeted follow-up queries to subagents for the missing subtopics, and re-evaluates until a coverage threshold is met or a maximum iteration count is reached.


What triggers another iteration? What stops the loop?


The loop continues while coverage is below a threshold (e.g., 90%). Each iteration targets only the gaps, not the already-covered subtopics. A maximum iteration count prevents infinite loops.

Starter Code
let coverage = await this.evaluateCoverage(subtopics, allResults);
let iterations = 0;
while (coverage.completeness < 0.9 && iterations < 3) {
  for (const gap of coverage.gaps) {
    const newResults = await this.delegateToSubagent(webSearchAgent, gap, topic);
    allResults.push(...newResults);
  }
  coverage = await this.evaluateCoverage(subtopics, allResults);
  iterations++;
}

6. Test with the topic renewable energy technologies and verify that the final output covers solar, wind, geothermal, tidal, biomass, and fusion
Why: This specific test case maps to the exam narrow decomposition failure pattern. If your output only covers solar and wind, the root cause is the coordinator decomposition — the exact diagnostic the exam expects you to make.

You should see: A final research report with substantive sections on all six energy types: solar, wind, geothermal, tidal, biomass, and fusion. The coverage evaluation should show 100% completeness.


Run your coordinator and check the output. If categories are missing, where in the pipeline did it go wrong?


If the output is missing categories, trace back: did the decomposition include them? If not, fix the decomposition. If it did, did the subagents receive the assignment? Check the context passing.

Starter Code
const report = await coordinator.research("renewable energy technologies");
const required = ["solar", "wind", "geothermal", "tidal", "biomass", "fusion"];
const missing = required.filter(cat =>
  !report.sections.some(s => s.topic.toLowerCase().includes(cat))
);
console.log(missing.length === 0 ? "Full coverage" : `Missing: ${missing.join(", ")}`);