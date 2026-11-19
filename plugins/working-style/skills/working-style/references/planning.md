# Bigger work: clarify, plan, approve, then branch

Load this for medium to large work (anything that spans several files or steps), when the
user asks for a plan, `PLAN.md` or the plan page, and when something unforeseen comes up
mid-plan. Skip it for small, direct tasks (a one-file fix, a question).

1. **Clarify** anything that changes the shape of the work, in one round (ask the way the
   core skill describes).
2. **Write the plan to `PLAN.md`** at the repo root: milestones in order, each
   independently shippable and verifiable, each paired with its check
   (`M1: <what> → verify: <how>`). Call out the **main risk** and anything uncertain, and
   order the riskiest milestone early, or last if it's optional. Keep it short: bold
   milestone name, a few bullets each. Summarise it in chat too.
   - **Offer an interactive plan page** where the user approves or requests changes per
     milestone, answers questions and adds notes, and the answers come straight back to
     you. When the user says they want it, **start it immediately**. Don't describe it
     first.
     - Write the plan as JSON (format at the top of [`plan-template.html`](../plan-template.html))
       to a temp file **outside the repo**.
     - Run [`plan_server.py`](../plan_server.py) (in the skill folder, standard-library
       Python) **in the background**: `python plan_server.py <plan.json>`. It serves the
       page on localhost only, opens it in the user's browser, and prints
       `PLAN_URL <url>` to stderr. Give the user the URL in case the browser didn't open.
     - When the user presses **Send to agent**, the server prints one line,
       `PLAN_FEEDBACK {json}`, also writes it to `plan-feedback.json` next to the plan
       file, and exits. A background-task notification is your cue. Without background
       tasks, run it as a blocking call with a long timeout, or poll for the file.
     - **Loop until the whole plan is approved.** Work starts only when the feedback
       has every milestone `approved` and nothing left to change. Otherwise, revise and
       go round again:
       - A milestone with changes requested or no response, a question answered with
         something other than your proposal or with a note, overall notes, or a comment
         that alters an approved milestone all mean: fold them into `PLAN.md`, rewrite the
         JSON, and restart the server with `--no-browser`. Tell the user in one line what
         changed and to reload the tab.
       - Open the summary of the revised plan with what changed since the last round
         ("Revised: M2 now calibrates first; Q1 answered as a PR"), so the user can see
         their input was taken.
       - Re-present every milestone for approval, not just the changed ones, since one
         change can affect the others. The page starts each round fresh.
       - A comment on an approved milestone that doesn't change it (a note or a
         reminder) is recorded in `PLAN.md` and needs no new round.
     - If the page can't reach the server, it shows the feedback as text to paste into
       chat instead.
3. **`PLAN.md` is local only. It's never committed or pushed.** Make sure it's in
   `.gitignore` before writing it, and check it isn't staged before every commit.
4. **Don't start until the user has reviewed the plan and said they're happy with it.**
   Pushback is normal; revise `PLAN.md` and re-present.
5. **Ask once about the branch** before the first milestone. For large changes, the
   recommended option is to branch off and do all the work on a separate branch (propose a
   name), keeping the main branch clean until the work is done. Staying on the current
   branch is the alternative.
   - In the same question, ask how the branch should land when the work is finished:
     **merge locally and push**, or **push the branch and raise a PR**. Then do whichever
     the user chose once the plan is complete, without asking again.
6. **Keep `PLAN.md` current** as work lands. A running record that's wrong is worse than
   none, so fix stale claims when you notice them. Anything in it worth keeping
   (measurements, what reality overturned) goes into `docs/`, and the user's decisions go
   into `PAST-DECISIONS.md` (both in [records.md](records.md)). Commit both with the
   milestone that settles them. Never reference `PLAN.md` from either.
7. **When something unforeseen comes up mid-plan** (a fact the plan got wrong, a missing
   decision, a blocker), first **try to answer it yourself** with whatever tools and
   resources you have: read the code and docs, run a probe, check the logs, search,
   look at the live system. Only what you genuinely can't settle goes to the user. Then
   offer exactly two options:
   1. **Keep going:** you carry out every step that doesn't depend on the open questions,
      collecting the questions as you go, then raise them all together in one round.
   2. **Pause now:** you stop implementing and draft `OPEN-QUESTIONS.md` with everything
      that must be answered before you continue.

   For each question, `OPEN-QUESTIONS.md` holds: what you found, why it blocks, what you
   already tried in order to answer it yourself, the options with your recommendation,
   and which milestones it affects. It's local only and gitignored, like `PLAN.md`. Fold
   the answers into `PLAN.md` (and `PAST-DECISIONS.md` where they're critical
   decisions). If an answer changes the plan's milestones, re-run the plan review (step 2)
   before continuing. When every question is answered, ask whether the file can be
   deleted.
8. **When the plan is fully executed,** land the branch the way the user chose in step 5.
   Then ask whether `PLAN.md` can be deleted. Don't delete it unasked.
