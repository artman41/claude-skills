# Project records: `docs/`, `PAST-DECISIONS.md`, `MEMORY.md`

Load this when you write or change docs, when the user makes a critical decision or
overrules how you work, or when you save or look up session memory.

**Lookup order when something comes up:** check `PAST-DECISIONS.md` first, for whether the
user has already decided how it should be handled. Then check `MEMORY.md`, for whether this
situation has happened before and what solved it. Only then work it out from scratch.

## Documentation in `docs/`

- As features and changes land, write or update the docs in `docs/` in the same commit, so
  the docs match the code at every commit.
- **Split docs by the area they affect**, one file (or folder) per subsystem, feature or
  concern: for example `docs/architecture.md`, `docs/api/…`, `docs/ui.md`,
  `docs/build.md`. Never one huge file. A human or an agent should be able to open
  just the page for the area they're touching.
- Keep `docs/README.md` as the index: one line per page saying what it covers.
- Before changing a subsystem, read its page. If you learn something it doesn't say,
  update it.
- Write for both audiences: plain explanations for people, and exact names, paths and
  commands for agents. Prefer tables and short sections to long prose.
- When you change or rename a page or section, check `PAST-DECISIONS.md` for references
  to it and update them in the same commit.

## The user's decisions: `PAST-DECISIONS.md`

`PAST-DECISIONS.md` at the repo root is committed, and it's the record of every critical
decision the user has made. Read it before starting work, and treat its entries as standing
instructions.

- **What goes in:** decisions that shape the project or how work is done. Examples: a
  scope or design call at a fork, rejecting a proposed approach, choosing a dependency or
  rejecting one, and **every time the user overrules the AI about how it should operate
  or interact** ("don't restart the app mid-game", "use `mv`, not `git mv`", "ask before
  pushing").
- **When:** in the same turn the decision is made. Create the file with the first entry.
- **Entry format:** a numbered heading with the date and a short title, then
  **Decision** (what was decided), **Why** (the user's reason, if given), **Applies to**
  (when it should change behaviour), and optionally **See** (a link to a doc page or
  section, e.g. `docs/ui.md#overlays`).
- **Never store:** secrets, credentials or tokens; local file paths; company or
  organisation names; file contents or code excerpts; or any reference to `PLAN.md`.
  Describe the decision in general terms instead. ("Overlays must never steal focus
  from the game" is fine; a path, a client name or a pasted config isn't.)
- **Keep it in step with `docs/`.** Referencing doc pages and sections is fine, but
  whenever a referenced page or section changes, is renamed, moves or is deleted, update
  the affected entries in the same commit, so every link resolves and every entry still
  matches what the doc says.
- **Superseded decisions stay.** When the user reverses a decision, add a new entry and
  mark the old one "Superseded by #N" rather than deleting or rewriting it.

## Session memory: `MEMORY.md`

Session memory lives in **`MEMORY.md` at the repo root**. Unless the user says otherwise,
it's local only: add it to `.gitignore` before writing to it, and check it isn't staged
before every commit.

- **What goes in:** anything that would help a later session: situations you hit and how
  they were solved, environment quirks that cost time, how to reach and authenticate
  against things, corrections and preferences, and project context that isn't in the code.
  Write each entry as **situation → what happened → solution**, with the date.
- **It may hold specifics** that are banned from `PAST-DECISIONS.md`: secrets and tokens,
  local file paths, company or organisation names, and file contents. That's its purpose.
  So never copy from it into anything committed or shared: docs, `PAST-DECISIONS.md`,
  commit messages, PR descriptions, issues or comments.
- Update existing entries rather than duplicating them. Delete entries that turn out to be
  wrong. Don't record what the repo or its history already records.
- If the environment also has its own memory system, still write project knowledge to
  `MEMORY.md`, so any agent working in this checkout can use it.
- When the user corrects or overrules how you work, the decision goes in
  `PAST-DECISIONS.md` (shared, general terms), and any specifics go in `MEMORY.md`.
