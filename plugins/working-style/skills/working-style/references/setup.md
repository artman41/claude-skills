# First time in a project

Load this the first time you work in a project directory, or when it's missing any of the
things below. Do each once.

- **Make sure it's a git repository.** If it isn't, run `git init` (don't commit unless asked).
  Check first that `.git` really is missing: git reports a "dubious ownership" folder (one
  owned by another user or Administrators) much like a missing repo, and re-initialising
  over it would be wrong. For that case, use `git -c safe.directory=<path> …` or tell the
  user how to trust the folder.
- **Keep local-only files out of git.** Make sure `.gitignore` lists `PLAN.md`,
  `OPEN-QUESTIONS.md` ([planning.md](planning.md)) and `MEMORY.md` ([records.md](records.md))
  before any of them is written.
- **Make sure there are agent instructions.** If neither `AGENTS.md` nor `CLAUDE.md` exists,
  create an `AGENTS.md` from [`agents-template.md`](../agents-template.md) (in the skill
  folder), plus a `CLAUDE.md` that just references it (`@AGENTS.md` on its own line), so
  every agent and developer reads the same file.
  - Fill the project sections from what you actually find: what it is, how to build,
    test and run it, the layout, and the conventions visible in the code. Durable
    quirks go in the relevant `docs/` page; the user's decisions go in
    `PAST-DECISIONS.md` ([records.md](records.md)). Neither goes in `AGENTS.md`.
  - Copy the "How we work" section as it is. It points other developers' agents at this
    skill, with a short summary as a fallback. Don't paste the whole skill in.
  - If either file already exists, read it and follow it; don't restructure it. If it has
    no "How we work" section, offer to add one.
- **Set up a project-wide language server (LSP) if one is available,** for the agent
  you're running as, and configure it at project level so it applies to everyone working
  in the repo:
  - In Claude Code, enable the language's LSP plugin in the project's
    `.claude/settings.json` (`enabledPlugins`), not just in user settings.
  - In other agents, use their own LSP configuration, or an LSP-bridging MCP server
    registered in `.mcp.json`.

  Use what's already installed. If the language server itself is missing, suggest
  installing it rather than doing it silently (no new dependencies without asking). Check
  it works with one real query (document symbols on a known file).
