"""
Tool implementations and tool definitions for the Multi-Tool Agent Loop exercise.

Each tool has two halves:
  1. A plain Python function that actually does the work (the "implementation").
  2. An entry in TOOLS describing the tool to Claude via the Messages API's
     `tools` parameter, so the model knows the tool exists, what it does, and
     what input shape (JSON Schema) it expects.

Claude never calls these Python functions directly — it returns a `tool_use`
content block naming the tool and its input, and it's our job (in the agent
loop) to look up the matching function, run it, and send the result back.
"""

# --- calculator tool implementation ---


def calculator(expression: str) -> dict:
    """
    Evaluate a basic arithmetic expression like '12 * (3 + 4)'.

    We use Python's built-in eval() to actually do the math, but we pass
    `{"__builtins__": {}}` as the second argument. That tells eval() "don't
    give this expression access to any of Python's built-in functions"
    (things like __import__, open, etc.), so the expression can only do
    plain arithmetic and can't do anything dangerous, even though the
    expression string is coming from the model rather than from us.
    """
    try:
        result = eval(expression, {"__builtins__": {}})
        return {"result": result}
    except Exception as exc:
        return {"error": f"Could not evaluate '{expression}': {exc}"}


# --- web_search tool implementation (stub) ---


def web_search(query: str) -> dict:
    """
    Mock web search. Returns fake but realistically-shaped results so the
    agent loop can be built and tested without a real search API/key.
    """
    return {
        "query": query,
        "results": [
            {
                "title": f"Result 1 for '{query}'",
                "url": "https://example.com/result-1",
                "snippet": f"This is a mock search snippet about {query}.",
            },
            {
                "title": f"Result 2 for '{query}'",
                "url": "https://example.com/result-2",
                "snippet": f"Another mock snippet discussing {query} in more detail.",
            },
        ],
    }


# --- tool definitions (what Claude sees via the Messages API `tools` param) ---

TOOLS = [
    {
        "name": "calculator",
        "description": (
            "Evaluates a basic arithmetic expression (+, -, *, /, **) and "
            "returns the numeric result. Use this whenever the user asks "
            "for a calculation instead of computing it yourself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A basic arithmetic expression, e.g. '12 * (3 + 4)'.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Searches the web for a query and returns a list of results "
            "(title, url, snippet). Use this when the user asks about "
            "something that requires up-to-date or external information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string.",
                }
            },
            "required": ["query"],
        },
    },
]

# Maps a tool name (as Claude will send it in a tool_use block) to the
# Python function that implements it. The agent loop (later steps) will use
# this to dispatch tool_use requests to the right implementation.
TOOL_IMPLEMENTATIONS = {
    "calculator": calculator,
    "web_search": web_search,
}
