# Built-in Tools

## What You Need to Know

Claude Code provides six built-in tools for working with codebases: Read, Write, Edit, Bash, Grep, and Glob. Each has a specific purpose, and using the wrong tool for a task wastes time, context tokens, or both. The exam deliberately presents scenarios where confusing these tools leads to incorrect answers.

## Grep vs Glob: The Core Distinction

This is the distinction that matters most in this task statement. Get it wrong and you'll lose marks.

Grep searches file CONTENTS for patterns. Use Grep when you need to find text inside files. Function callers. Error messages. Import statements. Variable assignments. Any time you are searching for what files contain, Grep is the tool.

```
// Find all files that call processLegacyOrder()
Grep: "processLegacyOrder"

// Find all error messages containing "timeout"
Grep: "timeout"

// Find all files that import a specific module
Grep: "import.*from 'utils/auth'"
```

Glob matches file PATHS by naming patterns. Use Glob when you need to find files by name, extension, or directory structure. Test files. Configuration files. All TypeScript files in a specific directory. Any time you are searching for files based on their path, Glob is the tool.

```
// Find all test files
Glob: "**/*.test.tsx"

// Find all configuration files
Glob: "**/config.*"

// Find all MDX files in the domains directory
Glob: "content/domains/**/*.mdx"
```

The distinction in one sentence: Grep finds what is INSIDE files. Glob finds files by their NAMES.

The exam presents scenarios where a developer uses the wrong tool. Use Glob to find function callers and it fails — Glob matches paths, not contents. Use Grep to find test files by naming pattern and it works technically (by searching for "test" in filenames via content), but it's the wrong tool, and the exam expects you to identify the correct one.

## Read, Write, and Edit

These three tools handle file operations, each optimised for a different use case.

Edit performs targeted modifications using unique text matching. You specify the exact text to find and its replacement. It's fast and precise because it touches only the specific text you identify.

```
Edit:
  old_string: "function processOrder(id: string)"
  new_string: "function processOrder(id: string, validate: boolean = true)"
```

**When Edit fails:** Edit requires unique text matching. If the text you specify appears in multiple places in the file, Edit can't tell which occurrence you mean, so it fails. That's a safety mechanism, not a bug — it stops you changing text you never meant to touch.

**When Edit can't find a unique anchor: the exam's answer.** The exam guide names one fallback, Read + Write. Read the full file, then Write the complete modified version back. It works every time, because you're no longer asking Edit to guess. It also spends a file's worth of tokens on what was usually a one-line change, which is why it's the fallback and not the default.

**When Edit can't find a unique anchor: current Claude Code.** The Edit tool docs now give you a cheaper move first: widen old_string with more surrounding context until it pins down one location, or set replace_all: true if you actually want every occurrence updated. Both keep you on Edit and cost almost no extra context. In real work, do that before you reach for Read + Write.

The ordering in real work:

1. Try Edit with the shortest anchor that's plausibly unique.
2. On a non-unique match, widen old_string until it matches one location, or use replace_all: true if you want every occurrence changed.
3. Fall back to Read + Write when neither of those can disambiguate the target.

The ordering on the exam has two steps: Edit first, Read + Write when Edit fails. Both orderings agree on the first step. Don't default to Read + Write for every modification. The exam penalises that because it burns context tokens.

**Current state**

Exam guide v1.0 frames Read + Write as the documented fallback when Edit cannot find unique anchor text ("Using Read to load full file contents followed by Write when Edit cannot find unique anchor text"). As of 14 August 2026 the Edit tool reference documents widening old_string or setting replace_all: true as the behaviour on a non-unique match. On the exam, answer Read + Write. In real work, widen the anchor first — it is cheaper and the practice above still holds.

## Incremental Codebase Understanding

How you explore a codebase matters as much as which tools you use. There's a right way and a wrong way.

**Wrong: Read all files upfront.** Loading every file into context before you know what you need is a context-budget killer. A 200-file codebase read in full swallows your entire context window, mostly on files that have nothing to do with your task. No other exploration mistake costs you more.

**Right: Incremental discovery.** Start narrow. Expand only as needed.

1. Grep to find entry points. Search for the function name, class name, or error message that anchors your investigation. This tells you which files are relevant.
2. Read to follow imports and trace flows. Once you know which files matter, Read them to understand the code structure. Follow import statements to discover related files.
3. Grep again to trace usage. The files you read in step 2 may expose the function under another name: a wrapper (submitOrder() that calls processOrder() inside it) or a barrel file that re-exports it (export { processOrder as submitOrder }). Callers of the new name never mention the original, so your first Grep never saw them. Grep for each new name, across the whole codebase, to get the full list of consumers. The next section works through an example.
4. Read only what you need. Each file you read should be justified by what you discovered in the previous step.

That's minimal context for maximum understanding. You map the codebase progressively, spending tokens only on files that matter to the task.

## Tracing Function Usage Across Wrapper Modules

A common codebase pattern: a function is defined in one module, re-exported through a wrapper, and consumed through the wrapper's name. A simple Grep for the original name misses every consumer who imports through the wrapper.

The correct approach:

1. Grep for the function definition to find where it is defined
2. Read the defining file to identify exported names
3. Grep for each exported name across the codebase to find all consumers
4. If the function is re-exported through a barrel file (e.g. index.ts), Grep for the barrel file's module name to find consumers who import from it

Concretely: processOrder is defined in orders.ts. The barrel utils/index.ts re-exports it as submitOrder, and three of its five consumers import submitOrder from utils. A Grep for processOrder finds the definition, the barrel line and the two consumers that import the original name. It cannot find the other three, because the string processOrder never appears in their files. Read the barrel, spot the rename, Grep for submitOrder, and the three turn up.

The multi-step trace catches indirect consumers a single Grep would miss.

## The Deprecation Scenario

This one turns up constantly in exam prep: find every file that calls a deprecated function AND the test files that exercise it. The correct sequence:

1. Grep for the function name — finds every file whose contents reference the function, including any tests that import it directly (content search)
2. Glob for sibling test files — finds the test file that pairs with each caller by naming convention, e.g. OrderProcessor.ts → OrderProcessor.test.tsx, even when the test exercises the function indirectly through the source module (path matching)
3. Grep again for wrapper names — when a caller exposes the function through a wrapper (e.g. applyLegacyOrder calls processLegacyOrder internally), Grep for the wrapper name to find tests that cover the function transitively through it

Say Grep reveals that OrderProcessor.ts and RefundHandler.ts call the deprecated function. Glob for **/OrderProcessor.test.* and **/RefundHandler.test.* to pull in their sibling test files, even if those tests never mention processLegacyOrder by name. And if either source file wraps the function under a new name, Grep for the wrapper to catch any remaining tests.

This is Grep, then Glob, then Grep again — content search for direct references, path matching for adjacent tests, content search for indirect coverage. Not Glob first.

**Key Concept**

Grep searches file contents. Glob matches file paths. Edit is the default for modifications. On a non-unique match the exam's answer is Read + Write. Current Claude Code widens the anchor or uses replace_all: true first, and that is the better move in real work. Build codebase understanding incrementally. Never read all files upfront.

## Exam Traps

**Exam Trap**

Using Glob to find function callers (it searches paths, not contents)

Glob matches file paths by naming pattern. It cannot search inside files for function calls. Use Grep to search file contents for function names, import statements, or error messages.

**Exam Trap**

Using Grep to find files by extension or naming pattern

While Grep could technically find filenames mentioned in content, Glob is the purpose-built tool for matching file paths. Use Glob for **/*.test.tsx, **/config.*, and similar path-based searches.

**Exam Trap**

Reading all source files upfront before understanding what is relevant

Loading every file into context is a context-budget killer. The correct approach is incremental: Grep to find entry points, then Read to trace flows from those specific entry points.

**Exam Trap**

Defaulting to Read + Write for every file modification instead of trying Edit first

Edit is faster and uses less context because it only touches the specific text. Read + Write loads the entire file. Try Edit first. Read + Write is the fallback for when Edit cannot find a unique anchor, not the standard response.

**Exam Trap**

Answering 'widen old_string or set replace_all' when a question asks what to do after Edit reports a non-unique match

That is what current Claude Code does, and it is the cheaper move in real work. The exam guide names Read + Write as the fallback when Edit cannot find unique anchor text, and every keyed answer follows the guide. Read the full file, then Write the complete modified version.