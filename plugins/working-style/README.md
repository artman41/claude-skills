# working-style

The default operating style I want from a coding agent on every task: act when there's enough to act on, ask only at real forks (2–4 options, recommendation first), build the least that works, fix root causes, verify before claiming success, report briefly and honestly, and confirm before risky or outward-facing actions.

Distilled from real sessions: the replies that got a straight "go" or "approved", the corrections that didn't, saved feedback memories, and the house rules in project `CLAUDE.md` files. The surgical-changes, simplicity and goal-driven-verification guidance is adapted from [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md).

[`skills/working-style/SKILL.md`](skills/working-style/SKILL.md) is the always-loaded core. Situation-specific detail (project setup, planning, docs/decisions/memory, debugging, `tools/` MCP tools) lives in [`skills/working-style/references/`](skills/working-style/references/), which the core tells the agent to load only when needed. For large multi-step work, pair it with [`milestone-driven-development`](../milestone-driven-development).

## Install (Claude Code)

```
/plugin install working-style@claude-skills
```

(requires the `claude-skills` marketplace to be added first — see the [repo README](../../README.md))

It loads itself: a `SessionStart` hook ([`hooks/hooks.json`](hooks/hooks.json)) injects the core `SKILL.md` into context at startup, after `/clear` and after compaction, so it applies without the model having to choose to invoke it. The `references/` fragments are still loaded on demand.

## Using it with other models / agents

`SKILL.md` is plain markdown with standard skill frontmatter, so it's portable:

- **Agents that support Agent Skills** (Kimi CLI, Codex, Gemini CLI, etc.): copy `skills/working-style/` into that agent's skills directory.
- **Make it always-on**: because this describes behaviour on *every* task rather than a specific job, it works best loaded unconditionally. Paste the body (everything below the frontmatter) into the agent's global instructions file — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or a system prompt — and keep `references/` (plus `agents-template.md`, `plan_server.py`, `plan-template.html`) somewhere the agent can read, fixing the fragment links to point there.
