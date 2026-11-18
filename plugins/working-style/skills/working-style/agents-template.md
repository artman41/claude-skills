# AGENTS.md

<!-- Project facts: fill these from what you actually find in the repo. Keep them short. -->

## Project

<What this is, in one or two sentences.>

- **Build:** `<command>`
- **Test:** `<command>`
- **Run:** `<command>`
- **Layout:** <the few directories that matter, and what's in them>
- **Conventions:** <style, patterns and rules visible in the code>

## Documentation

Docs live in [`docs/`](docs/README.md), split by the area they cover. Start at
`docs/README.md` (the index) and read only the page for the area you're changing.
Update the relevant page in the same commit as any feature or change; add a new page
for a new area rather than growing an existing one into a catch-all. Hard-won quirks
go on the page for the area they affect.

## Past decisions

[`PAST-DECISIONS.md`](PAST-DECISIONS.md) records every critical decision the user has
made, including each time they overruled the AI about how it should work. Read it before
starting, and follow it. Add an entry whenever a new decision is made. It must never
contain secrets, local paths, company or organisation names, file contents, or
references to `PLAN.md`. When a doc page or section it references changes, update the
entry in the same commit.

## Memory

Session memory goes in `MEMORY.md` at the repo root. It's gitignored and never committed
unless the user says otherwise. It may hold secrets, local paths, organisation names and
file contents, so never copy from it into anything committed or shared. Write entries as
situation → what happened → solution.

**When something comes up,** check `PAST-DECISIONS.md` first (has the user decided this?),
then `MEMORY.md` (has this happened before, and what fixed it?), and only then work it
out from scratch.

## How we work

This project follows the **working-style** skill. Load it before starting any task; if
anything below disagrees with it, the skill wins.

- **Claude Code:** `/plugin marketplace add artman41/claude-skills`, then
  `/plugin install working-style@claude-skills`. It then applies automatically.
- **Other agents with skill support** (Kimi, Codex, Gemini, …): install the
  `plugins/working-style/skills/working-style/` folder from
  https://github.com/artman41/claude-skills into your skills directory.
- **No skill support:** read
  https://raw.githubusercontent.com/artman41/claude-skills/master/plugins/working-style/skills/working-style/SKILL.md
  and follow it.

The core of it, for when the skill can't be loaded:

1. **Act when you have enough to act.** Read the code and run things to answer your own
   questions. Ask the user only about decisions that are genuinely theirs.
2. **Ask well.** Use one round of numbered options, recommendation first, each with its
   consequence. Put the questions in the chat, not in a document.
3. **Plan medium and large work in `PLAN.md`.** It's local only, gitignored, and never
   committed or pushed. Clarify first, then write milestones (each `→ verify: <how>`).
   Offer the skill's interactive plan page (served locally by `plan_server.py`) for
   approving or commenting on each milestone. If anything is rejected or changed,
   revise the plan and run the review again, until every milestone is approved. Only
   then start. If something unforeseen comes up mid-plan, try to answer it yourself
   first. If you can't, offer two options: keep going with every step that doesn't depend
   on it and ask at the end, or pause and draft a local `OPEN-QUESTIONS.md`. For large
   changes, recommend a separate branch, and ask once both which branch to use and
   whether to merge locally and push or push the branch and raise a PR. When the plan
   is done, land the branch that way, then ask whether `PLAN.md` can be deleted.
4. **Document as you go** in `docs/`, one page per area, in the same commit as the change.
   Record the user's decisions and overrules in `PAST-DECISIONS.md` (no secrets, paths,
   org names, file contents or `PLAN.md` references), and keep its doc links in step.
   Keep session memory in the local, gitignored `MEMORY.md`, and check it after
   `PAST-DECISIONS.md`.
5. **Understand before changing.** Find the root cause, and fix it once where every
   caller routes through.
6. **Build the least that works.** Reuse what exists, prefer stdlib, add no new
   dependencies without asking, and add no unrequested abstractions.
7. **Make surgical changes.** Every changed line traces back to the request. Don't tidy
   neighbouring code; mention it instead.
8. **Verify before claiming done.** Run it and look at it. Report what was checked and
   what wasn't, and own your mistakes.
9. **Commit with discipline.** Use separate commits with "why" messages. Don't commit
   outside an approved plan unless asked, and never push unless asked.
10. **Use Playwright for web access** (testing UIs, reading or driving pages) unless
    told otherwise, and close the browser afterwards.
11. **Respect the live machine.** Don't take over the mouse, steal focus, or restart
    apps the user is using.
12. **Spend tokens carefully.** Read narrowly, filter output, and batch calls. If the
    same complex calls keep repeating, suggest a `tools/` script exposed through
    `.mcp.json` as a token-efficiency improvement.
13. **Report briefly and in plain language.** Use **Cause → Fix → Checked → Not yet
    tested**, then one question.
