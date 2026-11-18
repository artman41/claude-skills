# working-style

The default operating style I want from a coding agent on every task: act when there's enough to act on, ask only at real forks (2–4 options, recommendation first), build the least that works, fix root causes, verify before claiming success, report briefly and honestly, and confirm before risky or outward-facing actions.

Distilled from real sessions: the replies that got a straight "go" or "approved", the corrections that didn't, saved feedback memories, and the house rules in project `CLAUDE.md` files. The surgical-changes, simplicity and goal-driven-verification guidance is adapted from [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md).

See [`skills/working-style/SKILL.md`](skills/working-style/SKILL.md) for the full content. For large multi-step work, pair it with [`milestone-driven-development`](../milestone-driven-development).

## Install (Claude Code)

```
/plugin install working-style@claude-skills
```

(requires the `claude-skills` marketplace to be added first — see the [repo README](../../README.md))

## Using it with other models / agents

`SKILL.md` is plain markdown with standard skill frontmatter, so it's portable:

- **Agents that support Agent Skills** (Kimi CLI, Codex, Gemini CLI, etc.): copy `skills/working-style/` into that agent's skills directory.
- **Make it always-on**: because this describes behaviour on *every* task rather than a specific job, it works best loaded unconditionally. Paste the body (everything below the frontmatter) into the agent's global instructions file — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or a system prompt.
