# Implement Session Management Strategies

## What You'll Learn

- The three session management options: resume, fork_session, and fresh start with summary injection
- Why resuming after file changes leads to the stale context problem
- How structured summary injection preserves knowledge without stale tool results
- When targeted re-analysis is more efficient than full re-exploration
- The difference between fork_session (divergent exploration) and resume (continuation)

---

## Step 1: Create a Named Claude Code Session for Codebase Analysis

Create a Claude Code session that analyses a 10-file codebase and name it with `--name` for later resumption.

**Why:** Named sessions resumed with `--resume` enable continuation of work across breaks. The exam tests when resume is appropriate (no files changed) versus when it creates the stale context problem (files have been modified since the last session).

**You should see:** A named Claude Code session that reads and analyses 10 source files. The session name should be memorable for later resumption. The agent should produce findings about each file.

### Nudge

How do you give a Claude Code session a name you can resume by later? Which flag sets it at start-up?

### Guidance

Use the `--name` (or `-n`) flag to set a session name when starting Claude Code, then resume it later with `--resume` and the same name. Ask it to analyse all files in the codebase directory.

### Starter Code

```bash
claude -n code-review-session "Analyse all files in ./src and identify bugs, security issues, and code quality problems. Provide findings for each file."
```

---

## Step 2: Record Key Findings as a Structured Summary

Record the key findings from the initial analysis as a structured summary (file names, issues found, recommendations).

**Why:** This structured summary is the knowledge you will inject into the fresh session later. The exam tests whether you preserve prior findings without carrying stale tool results. A good summary captures conclusions without raw tool output.

**You should see:** A structured document listing each file name, the issues found in it, severity ratings, and specific recommendations. This should be concise enough to inject into a prompt but complete enough to preserve all key findings.

### Nudge

What information from the analysis would a fresh session need to continue effectively? Focus on conclusions, not raw file contents.

### Guidance

Create a JSON or markdown summary with: file name, issues (description + severity), and recommendations for each file. Do not include raw file contents — just the analysis conclusions.

### Starter Code

```markdown
# Session Summary: code-review-session

## Findings
- **auth.ts**: SQL injection in login query (critical), missing input validation (high)
- **database.ts**: Connection pool not closed on error (medium), no retry logic (low)
- **api-routes.ts**: No rate limiting on public endpoints (high), inconsistent error responses (medium)
- **utils.ts**: No issues found
...

## Key Recommendations
1. Fix SQL injection in auth.ts immediately
2. Add connection cleanup in database.ts error handlers
3. Implement rate limiting middleware for api-routes.ts
```

---

## Step 3: Modify Files to Create Stale Context Conditions

Modify 3 files in the codebase to fix some of the identified issues.

**Why:** Modifying files after a session creates the conditions for stale context. The old file contents remain as tool results in the session history while the actual files now contain different code. This is the exact scenario that triggers the contradictory advice bug.

**You should see:** Three files modified with fixes for the issues identified in the initial analysis. The changes should be substantive enough that the old and new versions would produce different analysis results.

### Nudge

Which files from the analysis had the most critical issues? Fix those to create a clear contrast between old and new contents.

### Guidance

Make meaningful changes: fix the SQL injection in auth.ts, add connection cleanup in database.ts, and add rate limiting in api-routes.ts. Save all three files.

### Starter Code

```markdown
# Example fixes to apply:
# auth.ts: Replace string concatenation with parameterised query
# database.ts: Add try/finally with pool.release() in error path
# api-routes.ts: Add rate limiting middleware to public endpoints
```

---

## Step 4: Attempt to Resume the Session and Observe Stale Context Issues

Attempt to resume the session with `--resume` and observe any stale context issues (contradictory advice, references to old code).

**Why:** This demonstrates the stale context problem. The resumed session contains old tool results showing the unfixed code. The agent may recommend fixing issues that are already fixed, or give contradictory advice by referencing both old and new file contents.

**You should see:** The agent giving contradictory advice: recommending fixes for issues already resolved, referencing code that no longer exists, or providing inconsistent guidance about the modified files. These are the hallmarks of stale context.

### Nudge

After resuming, ask about the files you modified. Does the agent reference the old code or the new code?

### Guidance

Resume with the same session name and ask: What is the current state of auth.ts? Are there still security issues? Watch for references to the SQL injection you already fixed.

### Starter Code

```bash
claude --resume code-review-session "What is the current state of auth.ts? Are there still security issues that need fixing?"
# Watch for:
# - Recommending fixes you already applied
# - Referencing old code that no longer exists
# - Contradictory statements about the same file
```

---

## Step 5: Start a Fresh Session with Structured Summary Injection

Start a fresh session with the structured summary injected into the initial prompt, specifying the 3 changed files for targeted re-analysis.

**Why:** Fresh start with summary injection is the correct approach when files have changed. The exam specifically tests this: no stale tool results, preserved knowledge from the prior session, and targeted re-analysis of only the changed files instead of wasteful full re-exploration.

**You should see:** A clean session that knows about the prior findings (from the injected summary), targets only the 3 changed files for re-analysis, and produces consistent advice without contradictions.

### Nudge

How do you start fresh while preserving knowledge? Inject the summary into the initial prompt and specify which files changed.

### Guidance

Start a new session (no `--resume`) with the summary from step 2 injected into the prompt. Explicitly list the 3 modified files for targeted re-analysis.

### Starter Code

```bash
claude "Previous analysis summary:\n[paste structured summary here]\n\nThe following 3 files have been modified since the last analysis: auth.ts, database.ts, api-routes.ts.\n\nPlease re-analyse ONLY these 3 files to verify the fixes and check for any new issues. The analysis of all other files remains valid."
```

---

## Step 6: Compare Resume and Fresh Start with Summary Injection

Compare the quality and consistency of advice between the stale resume and the fresh start with targeted re-analysis.

**Why:** This comparison demonstrates why the exam favours fresh start with summary injection over naive resume after file changes. The fresh start produces consistent, accurate advice while the resume produces contradictions from stale context.

**You should see:** A clear quality difference: the resume session gives contradictory or outdated advice about the modified files, while the fresh session gives accurate, consistent analysis based on the current file contents.

### Nudge

What specific differences did you observe? Focus on accuracy of references to the modified files.

### Guidance

Document: (1) Did the resume session reference old code? (2) Did it recommend already-applied fixes? (3) Did the fresh session correctly identify the current state? (4) Did targeted re-analysis avoid wasting time on unchanged files?

### Starter Code

```markdown
# Comparison Results
| Metric | --resume | Fresh + Summary |
|--------|----------|----------------|
| References old code | Yes - cited unfixed SQL injection | No - recognised parameterised query |
| Recommends applied fixes | Yes - suggested fixing auth.ts | No - confirmed fix was correct |
| Consistent advice | No - contradicted itself on auth.ts | Yes - all advice matched current code |
| Files analysed | All 10 (unnecessary) | Only 3 changed files (efficient) |
```