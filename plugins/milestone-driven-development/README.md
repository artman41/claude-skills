# milestone-driven-development

A Claude Code skill for running large, multi-part, or open-ended work well: plan it into shippable milestones, ask at real forks instead of guessing, verify each milestone for real before calling it done, commit as you go, delegate well-specified chunks to background subagents, and treat existing code and the user's request as having reasonable intent behind them.

See [`skills/milestone-driven-development/SKILL.md`](skills/milestone-driven-development/SKILL.md) for the full skill content.

## Install

```
/plugin install milestone-driven-development@claude-skills
```

(requires the `claude-skills` marketplace to be added first — see the [repo README](../../README.md))

## Triggering

This skill activates automatically once installed, whenever a task looks like it'll span many files, many steps, or an extended session. You can also invoke it explicitly:

```
/milestone-driven-development
```
