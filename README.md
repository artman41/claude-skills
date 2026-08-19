# claude-skills

My personal collection of [Claude Code](https://claude.com/claude-code) skills, distributed as a plugin marketplace so they install the same way anywhere I use Claude Code.

Each skill lives in its own plugin under [`plugins/`](plugins/), so it can be installed independently of the others.

## Setup

Add this repo as a marketplace, once per machine:

```
/plugin marketplace add artman41/claude-skills
```

Then install whichever skill(s) you want:

```
/plugin install milestone-driven-development@claude-skills
```

`/plugin marketplace update claude-skills` pulls in anything added here since you last installed.

## What's here

| Plugin | Skill | What it does |
|---|---|---|
| [`milestone-driven-development`](plugins/milestone-driven-development) | `milestone-driven-development` | How to run large, multi-part, or open-ended work: plan it into shippable milestones, ask at real forks instead of guessing, verify each milestone for real before calling it done, commit as you go, delegate well-specified chunks to background subagents, and treat existing code and the user's request as having reasonable intent behind them. |

## Repo layout

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json       # marketplace manifest — lists every plugin below
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json    # plugin manifest
        ├── skills/
        │   └── <skill-name>/
        │       └── SKILL.md   # the actual skill
        └── README.md
```

## Adding a new skill

1. Scaffold a plugin directory:

   ```
   mkdir -p plugins/<plugin-name>/.claude-plugin plugins/<plugin-name>/skills/<skill-name>
   ```

2. Write `plugins/<plugin-name>/.claude-plugin/plugin.json` (name, version, description, author — see any existing plugin here for the shape).
3. Write `plugins/<plugin-name>/skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`) followed by the skill body. The description is what Claude actually matches against to decide when to trigger it, so make it specific about when to use the skill, not just what it does.
4. Add an entry for it to the `plugins` array in `.claude-plugin/marketplace.json`, pointing `source` at `./plugins/<plugin-name>`.
5. Validate before committing:

   ```
   claude plugin validate .
   claude plugin validate ./plugins/<plugin-name>
   ```

6. Commit, push, then `/plugin marketplace update claude-skills` (and `/plugin install <plugin-name>@claude-skills` if it's new) to pick it up in an existing session.

One plugin per skill (or per small group of closely related skills) rather than one giant plugin — it keeps installs granular and keeps this README's table meaningful.
