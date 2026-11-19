# Turning repeated work into a `tools/` MCP tool

Load this when you notice you keep making the same or similar calls that are complex
enough to cost real tokens each time (a multi-step query, a long pipeline, a
login-then-fetch sequence, a parser run over logs), or when the user agrees to build one.

- **Suggest it, and say it's a token-efficiency improvement:** "I've run this 4-step query
  5 times; a `tools/` MCP tool would make it one short call each time." Don't build it
  unasked.
- If the user agrees:
  - Write it under `tools/`, in the project's language or a simple one (bash, Python,
    Node.js). Keep it small, with one job per tool.
  - Expose it as an MCP server and register it in the project's `.mcp.json`
    (`{"mcpServers": {"<name>": {"command": "python", "args": ["tools/<name>.py"]}}}`).
    Use the official MCP SDK for the language if a dependency is acceptable (ask first);
    otherwise write a minimal stdio JSON-RPC server.
  - Document it in `docs/` and verify it with one real call. The user may need to approve
    the new server, or restart the session, before it appears.
