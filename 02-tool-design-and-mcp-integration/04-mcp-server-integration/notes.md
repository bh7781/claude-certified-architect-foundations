# MCP Server Integration

## What You Need to Know

MCP (Model Context Protocol) servers extend Claude's capabilities by connecting it to external systems — databases, APIs, development tools, issue trackers. Configuring them correctly determines whether your team shares a consistent toolset or descends into configuration chaos.

## The Scoping Hierarchy

MCP server configuration lives at two levels, and mixing them up is where most setup problems start.

**Project-level: .mcp.json**
Lives in the project repository root. Version-controlled. Shared with every team member who clones or pulls the repository. Use this for servers that the entire team needs — your Jira integration, your GitHub tools, your internal API connectors.

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "atlassian": {
      "type": "http",
      "url": "https://mcp.atlassian.com/v1/mcp/authv2"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${WORKSPACE_ROOT:-.}"]
    }
  }
}
```

Note the two entry shapes. A remote server declares "type": "http" and a url. A local one declares a command and args, and speaks over stdio. An entry with a url but no type is a configuration error — Claude Code reads it as a stdio server, skips it, and tells you to add the type. Both GitHub and Atlassian ship official remote servers now, which is why neither is an npx line.

**User-level: ~/.claude.json**
Lives in the user's home directory. Personal. NOT version-controlled. NOT shared with teammates. Use this for experimental servers, personal integrations, or servers you're testing before proposing them to the team.

**Current state**

Exam guide v1.0 describes MCP configuration at two levels, project and user, and that is the expected exam answer. As of 14 August 2026 the MCP documentation documents three scopes — local (the default), project and user — selected with -s / --scope, with ~/.claude.json holding both the local and user entries. On the exam, answer with the two-level project-vs-user split.

Key principle: all tools from all configured servers (both project-level and user-level) are discovered at connection time and available simultaneously. There's no manual activation step — if a server is configured and reachable, its tools appear in the agent's toolkit.

## Environment Variable Expansion

The .mcp.json file supports ${VARIABLE_NAME} syntax for environment variable expansion. This is how you keep credentials out of version control whilst still sharing server configuration with your team.

```json
{
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "DATABASE_URL": "${DATABASE_URL}"
  }
}
```

Each developer sets their own tokens locally (in their shell profile, .env file, or secrets manager). The .mcp.json file references the variable names, not the values. This means:

- The configuration file is safe to commit to version control
- Each developer authenticates with their own credentials
- Token rotation does not require config file changes
- No secrets leak through repository history

There is a second form worth knowing: ${VAR:-default} expands to VAR when it is set and falls back to default when it is not. Use it for machine-specific paths that have a sensible fallback, as in the ${WORKSPACE_ROOT:-.} argument above. As of 14 August 2026, an unset variable with no default does not stop the rest of the configuration loading. Claude Code warns and carries on, so do not rely on a missing token failing loudly.

## MCP Resources

MCP resources expose content catalogues to agents without requiring exploratory tool calls. Instead of calling a tool to discover what data exists, the agent gets that information upfront.

That is the exam guide's framing and the keyed answer. One precision from the MCP specification (September 2026): resources are application-controlled. The server lists them, but the client decides when to attach one to the model's context, so the agent sees a resource only when the host surfaces it. Claude Code does that through @server:resource mentions and a resource-listing tool.

Examples of what to expose as resources:

- Issue summaries — a list of current Jira issues with titles and statuses
- Documentation hierarchies — a table of contents for your internal docs
- Database schemas — table names, column types, and relationships

The payoff is fewer wasted calls. Without resources, an agent might call list_tables, then describe_table for every table, burning tool calls just to get its bearings. With a database schema resource, it knows immediately.

Resources show agents what data is available. Tools let them act on it.

## The Build-vs-Use Decision

This decision comes up constantly, in the exam and in real work. Your team needs to integrate with an external system: build a custom MCP server, or use an existing community one?

Use community servers for standard integrations:

- Jira, GitHub, Slack, Linear, Notion — these all have maintained community MCP servers
- They cover standard use cases, are tested by the community, and receive updates
- Using them saves development time and maintenance burden

Build custom servers only when:

- Your team has specific workflows that community servers cannot handle
- You need custom business logic embedded in the tool layer
- You require integration with proprietary internal systems that have no community server

The exam consistently favours the pragmatic choice. "Evaluate community servers first" is always correct when a standard integration is involved. "Build custom" is only correct when the scenario explicitly describes team-specific requirements that community servers cannot meet.

## Enhancing MCP Tool Descriptions

Here's a subtle one: when an MCP tool has a sparse description, the agent may prefer built-in tools (like Grep) even when the MCP tool is more capable. The model simply has better context about built-in tools — their descriptions are rich and detailed.

The fix: enhance your MCP tool descriptions to explain capabilities and outputs in detail. Instead of:

```
search_codebase: "Searches code"
```

Write:

```
search_codebase: "Performs semantic code search across the
entire repository using AST-aware indexing. Returns matching
functions, classes, and methods with full context including
file path, line numbers, and surrounding code. More accurate
than text-based grep for finding code by intent rather than
exact string match. Use this instead of Grep when searching
for code by what it does rather than what it contains."
```

The enhanced description gives the model enough context to prefer the MCP tool when it's genuinely more capable than the built-in alternative.

**Key Concept**

Project-level .mcp.json is version-controlled and shared with the team. User-level ~/.claude.json is personal and not shared. Use ${ENV_VAR} syntax to keep credentials out of version control.

## Exam Traps

**Exam Trap**

Building a custom MCP server for a standard integration like Jira

Community MCP servers exist for standard integrations and should be evaluated first. Custom builds are only justified for team-specific workflows that community servers cannot handle.

**Exam Trap**

Putting team-wide MCP server configuration in ~/.claude.json

~/.claude.json is user-level and personal — it is not version-controlled or shared. Team-wide servers belong in .mcp.json at the project root.

**Exam Trap**

Committing credentials directly in .mcp.json instead of using environment variable expansion

Credentials in version control are a security risk. Use ${GITHUB_TOKEN} syntax so each developer sets tokens locally and secrets never enter repository history.

**Exam Trap**

Leaving MCP tool descriptions sparse, causing the agent to prefer built-in tools

The model defaults to tools it understands best. Sparse MCP descriptions lose out to detailed built-in tool descriptions. Enhance MCP descriptions to explain capabilities and outputs fully.