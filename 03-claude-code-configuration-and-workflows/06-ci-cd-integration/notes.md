# CI/CD Integration

## What You Need to Know

Drop Claude Code into a CI/CD pipeline and it stops being an interactive developer tool and becomes an automated review and generation engine. The exam tests five concepts in this task statement, and the -p flag is the single most directly tested item (it's Question 10 in the sample question set).

## The -p Flag: Non-Interactive Mode

Claude Code defaults to interactive mode: it expects keyboard input and shows a conversational interface. A CI pipeline has no keyboard. Without the -p flag, the job hangs forever, waiting for input that never comes.

```bash
# WRONG — hangs in CI
claude "Analyse this pull request for security issues"

# CORRECT — runs non-interactively
claude -p "Analyse this pull request for security issues"
```

The -p flag (also --print) switches Claude Code to print mode: it processes the prompt, outputs the result to stdout, and exits. No interactive input required.

This one is pure memorisation. The exam shows a CI job hanging, logs of Claude waiting for input, and asks you to pick the fix. The answer is the -p flag. Not CLAUDE_HEADLESS=true (doesn't exist). Not --batch (doesn't exist). Not stdin redirection from /dev/null (doesn't properly address Claude Code's interactive mode).

**Key Concept**

The -p flag is the single most directly testable fact in Domain 3. It is Question 10 in the official sample questions. When you see a CI pipeline hanging and logs showing Claude waiting for input, the answer is always -p.

## Structured Output for CI

In CI, Claude Code's output has to be machine-parseable. No human is reading it. Automated systems process it to post inline PR comments, update dashboards, or trigger downstream workflows.

Two flags work together:

- `--output-format json` — wraps the run in a JSON envelope (result text, session ID, cost and usage metadata) instead of human-readable text
- `--json-schema` — validates the agent's final output against a JSON Schema (print mode only)

```bash
claude -p \
  --output-format json \
  --json-schema '{"type":"object","properties":{"findings":{"type":"array","items":{"type":"object","properties":{"file":{"type":"string"},"line":{"type":"integer"},"severity":{"type":"string"},"message":{"type":"string"}}}}}}' \
  "Review this PR for security issues"
```

The schema-conforming data lands in the envelope's structured_output field — extract it with jq '.structured_output', not from the top level. That gives automated systems validated findings they can:

- Parse programmatically
- Post as inline PR comments at the exact file and line
- Filter by severity for different notification channels
- Track across review runs

## Session Context Isolation

The same Claude session that generated code is less effective at reviewing its own changes. This isn't a theoretical worry; it's a measurable effect.

Why self-review is weaker:

When Claude generates code in a session, it builds up reasoning context: why it chose this approach, what tradeoffs it considered, what alternatives it rejected. Ask it to review the same code in the same session and it keeps all of that. It's less likely to question decisions it already justified to itself.

The fix: independent review instances

Use a separate Claude Code invocation for review — one that has no access to the generation session's reasoning context. The independent reviewer evaluates the code on its own merits, without the bias of prior justification.

```bash
# Step 1: Generate code (session A)
claude -p "Implement the authentication middleware"

# Step 2: Review code (session B — independent, no shared context)
claude -p "Review the authentication middleware for security issues, error handling gaps, and edge cases"
```

This concept connects to Domain 4 (multi-instance review architectures) and Domain 5 (context management). The exam tests it in CI/CD scenarios specifically.

## Incremental Review Context

Automated reviews run on every push. Without context about previous reviews, each run analyses the entire PR from scratch, so it re-derives the same findings every time. A genuinely fixed issue drops out on its own, because the changed code no longer triggers it. The ones that keep coming back are the issues the developer saw and deliberately chose not to change; a context-free re-scan cannot tell those apart from new problems, so it flags them again on every push.

The fix: include prior review findings in context and instruct Claude to report only new or still-unaddressed issues.

```bash
claude -p \
  --output-format json \
  "Review this PR. Here are the findings from the previous review:
  ${PREVIOUS_FINDINGS}

  Report ONLY:
  1. New issues not in the previous findings
  2. Issues from the previous findings that are still present

  Do NOT re-report previous findings the developer has already reviewed and chosen not to act on."
```

Duplicate comments erode developer trust. If every push generates the same five comments regardless of whether the developer fixed the issues, developers stop reading the comments. Incremental review context preserves the signal-to-noise ratio.

## CLAUDE.md for CI Context

When Claude Code runs in CI, it reads the project's CLAUDE.md files exactly as it does interactively. So CLAUDE.md is how you feed project-specific context to a CI-invoked run:

- Testing standards: what makes a valuable test, what patterns to follow, what to avoid
- Available fixtures: which test fixtures exist, how to use them, what data they contain
- Review criteria: what constitutes a critical finding vs a minor style issue
- Existing test coverage: what is already covered, to avoid suggesting duplicate tests

Without this context in CLAUDE.md, CI-invoked test generation produces low-value boilerplate. With it, generated tests follow the team's patterns and add genuine coverage.

```
# .claude/CLAUDE.md — CI-relevant section
## Testing Standards

- Tests must use the factory pattern from test/factories/ for data creation
- Integration tests connect to the test database via test/setup/db.ts
- Do not test private implementation details — test public API contracts
- Coverage target: 80% branch coverage for new code
- Available fixtures: test/fixtures/users.json, test/fixtures/orders.json
```

## CLI Flags Reference

The -p flag is the most directly tested flag, but the exam also expects familiarity with the flags that shape a headless run: how output is formatted, which system prompt is used, and how permissions and tools are scoped. These flags work with claude -p in CI and with the interactive claude command.

**System prompt flags.** Claude Code provides four flags here, and the exam tests the append-versus-replace distinction:

| Flag | Effect |
| --- | --- |
| `--system-prompt "<text>"` | Replaces the entire default system prompt |
| `--system-prompt-file <path>` | Replaces the default prompt with a file's contents |
| `--append-system-prompt "<text>"` | Appends text to the default prompt |
| `--append-system-prompt-file <path>` | Appends a file's contents to the default prompt |

Append when Claude should stay a coding assistant that also follows your extra rules. Appending keeps the default tool guidance, safety instructions, and coding conventions, so you only supply what differs. Replace when the identity or permission model differs from Claude Code's, like a non-coding agent in a pipeline no human watches. Replacing drops the entire default prompt, so you own everything the task still needs.

**Headless output and limits (print mode).**

| Flag | Effect |
| --- | --- |
| `--output-format text\|json\|stream-json` | Output shape for -p; json and stream-json are machine-parseable |
| `--input-format text\|stream-json` | Input shape for -p |
| `--json-schema '<schema>'` | Schema-validated output for -p; with --output-format json it lands in the envelope's structured_output field |
| `--max-turns <n>` | Cap the number of agentic turns, then exit |

**Permissions, tools, and context.**

| Flag | Effect |
| --- | --- |
| `--permission-mode <mode>` | Start in default, acceptEdits, plan, auto, dontAsk, bypassPermissions, or manual (an alias for default, v2.1.200+) |
| `--allowedTools "<rules>"` | Tools that run without a permission prompt, e.g. "Bash(git diff *)" "Read" |
| `--disallowedTools "<rules>"` | Deny rules; a bare tool name removes the tool from context entirely |
| `--tools "Bash,Edit,Read"` | Restrict which built-in tools are available at all |
| `--add-dir <path>` | Add a directory Claude may read and edit (grants file access, not configuration discovery) |
| `--model <alias\|name>` | Set the session model (sonnet, opus, or a full model name) |

**Session and start-up.** -c / --continue resumes the most recent conversation in the current directory, and -r / --resume <id|name> resumes a specific session. --bare is minimal mode: it skips auto-discovery of hooks, skills, plugins, MCP servers, auto memory, and CLAUDE.md so scripted calls start faster, leaving Claude with the Bash and file read/edit tools only. Reach for --bare when you want a fast, predictable scripted run and don't need project configuration loaded.

## GitHub Actions: Claude Code as a Workflow Step

Beyond the guide

Task Statement 3.6 describes CI/CD integration through the -p flag, output formats and session isolation, and never names GitHub Actions. Three readers who sat the exam report four or five questions on it, so this section is here for coverage. Verified against the GitHub Actions page of the Claude Code docs on 16 September 2026.

Anthropic ships the pipeline integration as a GitHub Action, anthropics/claude-code-action@v1, that runs Claude Code non-interactively inside a workflow job. It is built on the Agent SDK and accepts the same CLI flags as a headless claude -p run. Two settings decide how a workflow behaves.

Mode follows the prompt input. With no prompt, the action runs in interactive mode: it waits for the trigger phrase (@claude by default) in an issue or pull request comment and answers there. With a prompt, it runs in automation mode on whatever event fired the workflow, a pull request opening or a cron schedule, without waiting for a mention, and writes its result to the workflow run log unless the prompt tells it to post somewhere and it has a tool that can. With a plain-text prompt Claude has no shell or GitHub API access until the workflow grants the tools it needs, with --allowedTools in claude_args or a permissions.allow rule in the settings input.

CLI flags go through claude_args. There's no separate action input for the system prompt, the tool allowlist or the turn cap. You pass the flags from the reference table above as one string: --append-system-prompt, --allowedTools, --max-turns, --model, --mcp-config. So "add review criteria without replacing the default behaviour" is --append-system-prompt inside claude_args, exactly as it would be on the command line. The pre-v1 inputs map onto this: custom_instructions became --append-system-prompt, direct_prompt became prompt, and mode went away because the action now infers it.

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write
      actions: read
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 1
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: |
            --append-system-prompt "Review against the checklist in CLAUDE.md. Report only critical findings."
            --allowedTools "Read,Grep,Glob,Bash(git diff *)"
            --max-turns 10
```

How files reach Claude: actions/checkout puts the repository on the runner, so without that step there is nothing on disk to read. Claude reads the pull request itself through the GitHub tools the action provides, and the permissions block bounds what it can write back. id-token: write is required for the action's default GitHub App authentication and actions: read lets it see CI results on the pull request. The credential is a repository secret, anthropic_api_key for an API key or claude_code_oauth_token for a subscription token, and never a literal in the file.

## Parallel Sessions with Git Worktrees

Beyond the guide

The guide does not mention worktrees. The practice bank has tested them under this task statement since July, because parallel Claude Code instances are how large refactors are actually run. Verified against the worktrees page of the Claude Code docs on 16 September 2026.

A git worktree is a second working directory for the same repository, on its own branch, sharing the same history. Running each Claude Code session in its own worktree means edits in one session never touch files in another, which is what lets three instances extract three services from one monolith at the same time and commit to the same repository without colliding. claude --worktree <name> creates one under .claude/worktrees/<name>/ on a branch called worktree-<name> and starts the session inside it. git worktree add ../project-feature -b feature does the same by hand, with a path and branch of your choosing. Each session gets a full context budget of its own as well as its own files. Coordination on a shared file is sequencing, not locking: the first session merges, the second rebases onto the result before touching it. A custom subagent can run in a worktree of its own with isolation: worktree in its frontmatter, so parallel subagent edits don't collide either.

## Providing Existing Tests to Avoid Duplication

When running test generation in CI, include existing test files in context. Without them, Claude Code may suggest tests that already exist, wasting developer review time. Including existing tests enables Claude to identify coverage gaps rather than duplicating existing scenarios.

## Batch API vs Real-Time for CI Workflows

The Message Batches API offers 50% cost savings but has processing times up to 24 hours with no guaranteed latency SLA. This creates a clear decision boundary:

| Workflow type | API choice | Reason |
| --- | --- | --- |
| Pre-merge checks (blocking) | Real-time (synchronous) | Developers wait for results |
| Overnight technical debt reports | Batch API | Not time-sensitive, 50% savings |
| Weekly code audit | Batch API | Scheduled, latency-tolerant |
| Nightly test generation | Batch API | Runs overnight, reviewed next morning |

Pre-merge checks are blocking workflows. Developers can't merge until the check completes. The Batch API is unsuitable here because it gives no latency guarantee. The exam tests this distinction directly (Sample Question 11).

## Exam Traps

**Exam Trap**

CI pipeline hanging because Claude Code is waiting for interactive input

The fix is the -p (--print) flag. Not CLAUDE_HEADLESS=true (does not exist), not --batch (does not exist), not stdin redirection. The -p flag is the documented method for non-interactive execution.

**Exam Trap**

Assuming self-review in the same session is as effective as independent review

The same session retains reasoning context from code generation, making it less likely to question its own decisions. An independent review instance without that context is more effective at finding issues.

**Exam Trap**

Using the Batch API for pre-merge CI checks

The Message Batches API has up to 24-hour processing time with no latency SLA. Pre-merge checks are blocking workflows where developers wait for results. Use real-time API for blocking checks; batch API for overnight or weekly non-blocking analysis.

**Exam Trap**

Not including prior review findings in subsequent review runs

Without prior context, each review run analyses from scratch and produces duplicate comments. Include previous findings and instruct Claude to report only new or unaddressed issues to maintain developer trust.
