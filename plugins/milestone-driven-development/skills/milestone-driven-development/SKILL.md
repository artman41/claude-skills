---
name: milestone-driven-development
description: How to run a large, multi-part, or open-ended piece of work well — break it into shippable milestones, let the user pick direction at real forks instead of guessing, verify each milestone for real before calling it done, commit as you go, delegate well-specified chunks to background subagents, and treat existing code and the user's request as having reasonable intent behind them rather than assuming bugs or scope. Use this whenever a task is going to span many files, many steps, or an extended session — building out a whole feature area, "add tests for X", a multi-phase migration, an epic, or anything where the first message is closer to a mission than a single edit. Also use it when the user explicitly asks for a plan, milestones, or to work incrementally. Don't force this ceremony onto a small, single-shot task (a one-file fix, a quick question) — the judgment of when the work is "big enough" is itself part of this skill.
---

# Milestone-driven development

This is the operating loop for work that's too big to do in one shot: plan it, cut it into milestones, ship and commit each one, verify for real before moving on, ask the user only at genuine forks, and keep the whole thing moving without babysitting. It's a way of working, not a checklist to recite at the user — they should feel the effects (steady progress, clean commit history, being asked the right questions at the right time) more than they see the machinery.

**Scale the ceremony to the task.** A three-file bug fix doesn't need a written plan, milestones, or a commit per step — just fix it. This skill is for work where a plan actually changes what you'd do next, and where "milestones" are a real decomposition, not a formality. If you notice a task shrinking as you learn more about it, it's fine to drop into a simpler, direct mode.

## 1. Plan first, and let the plan be genuinely revisable

Before writing code on anything sizeable, work out the shape of the whole thing: what are the pieces, what order do they go in, what's genuinely unknown or risky, what needs a decision from the user before you can proceed. If you're in an environment with a plan mode, use it — the point of showing the plan before acting is that the user can redirect *before* you've sunk cost into the wrong approach, which is far cheaper than redirecting after.

Treat rejection or edits to the plan as normal, not as a failure state. If the user pushes back on part of it ("do X differently", "don't build Y yet"), fold that in and re-present rather than treating the first draft as precious. A plan's job is to get argued with once, cheaply, before the expensive part starts.

While planning, actually go look at the code, run discovery commands, read the relevant modules — a plan built on guesses about what exists will fall apart on contact with the codebase. If a plan depends on how some subsystem behaves and you're not sure, that's a concrete thing to verify (read the source, write a two-line probe script) before it goes in the plan as fact.

## 2. Cut the work into milestones that are each worth shipping alone

A milestone is a coherent, independently valuable, independently verifiable slice — not just "step 3 of 12". Good milestones tend to be things you could stop after and the user would be strictly better off than before you started. For a test-suite build-out, that's "one suite, fully green" — not "half the suites, all red because a shared helper is wrong." For a refactor, it's "this layer converted and everything still builds" — not an in-between state that only makes sense once every layer is done.

Order milestones so that the highest-uncertainty or highest-value ones happen early: if something is going to reveal that the plan needs to change, better to find out on milestone 1 than milestone 8. Infrastructure/helpers that many later milestones depend on usually come first, but don't let "build all the shared infrastructure up front" become an excuse to defer the first real, visible milestone indefinitely.

## 3. Ask the user at real forks — not more, not less

Use a structured choice (numbered options, a recommended default) when there are genuinely multiple reasonable next steps or approaches and no principled way to pick one from the task alone — for example, several roughly-equal-value milestones to do next, or a design choice with real tradeoffs the user might feel differently about than you'd guess. Put your actual recommendation first and mark it as such; the user is choosing *between* real options, not being quizzed.

Don't ask when:
- There's a clearly-better answer you can just take (that's not a fork, it's you doing your job)
- The task already told you the order or the approach
- You're just checking in for permission to keep going — if the plan was approved, keep going

Do ask when:
- You're genuinely blocked on something only the user can decide (scope, location/visibility of an artifact, an irreversible or wide-blast-radius action, a real design tradeoff)
- You've hit new information that changes the plan enough that continuing on the old assumption would waste real work

The test is: would a competent senior engineer in your position, with your context, actually need this decision made by someone else — or are you reaching for a question because the next step is merely *uncertain*, not because it's *theirs to make*? Most uncertainty should be resolved by you going and finding out (reading code, running something), not by asking.

## 4. Verify each milestone for real before calling it done

"I wrote the code" and "this works" are different claims — only make the second one after checking. Run the thing: the test suite, the build, the actual feature in a browser, the script against real input. Read the failure, understand *why*, fix the real cause, run again. A milestone isn't done at "no more obvious errors in the diff", it's done at "I watched it pass."

If the work touches anything with real-world non-determinism — timing, concurrency, distributed systems, network calls, flaky external services — running it once green is weaker evidence than usual. Run it again, a few times, before trusting it. If it's sometimes green and sometimes not, that's a real signal to chase down (see §6), not noise to average away by re-running until you get lucky.

When you hit a failure you don't understand, resist the urge to guess-and-check your way out with random plausible-looking edits. Form a hypothesis, find the cheapest way to test *just* that hypothesis (a standalone script, an added log line, reading the actual source of the thing that's misbehaving instead of assuming its behavior), and only then make the real fix. Debugging by mutation (change something, rerun the whole suite, see if it helped, repeat) is slow and teaches you nothing when it doesn't work. A five-line probe script that isolates the one thing in question is usually faster than another full test run.

## 5. Commit each milestone before moving to the next

Once a milestone is verified, commit it — with a message that explains *why*, not a restatement of the diff — before starting the next one. This keeps history bisectable, means nothing large is ever sitting uncommitted where it can be lost, and gives the user a running, readable log of what happened and in what order even if they weren't watching every step. It also gives *you* a clean recovery point: if the next milestone goes sideways, there's solid ground right behind you.

Don't batch multiple unrelated milestones into one commit for tidiness, and don't commit broken or half-verified work just to keep the cadence — the ordering is verify, *then* commit, always in that order. If the user has told you to commit as you go, that instruction stands for the rest of the task; don't re-ask permission for each subsequent commit, and don't stop and wait after committing — go on to the next milestone.

## 6. Keep going without waiting to be re-told

Once direction is set (a plan is approved, or the user picked an option, or they said "commit as you go" / "keep going"), that authorization covers the rest of the natural sequence of milestones, not just the next one. Don't stop after each milestone to ask "should I continue?" — that's the check-in-for-permission failure mode from §3. If you finish a milestone and there's an obvious next one implied by the original ask, start it.

The exception is genuinely running out of well-defined work: if you reach a point where the remaining direction really does have multiple reasonable next milestones and nothing in the conversation picked one, that's a real fork — ask (§3), don't guess silently and don't stall waiting either.

## 7. Delegate well-defined, separable chunks to background subagents

Not everything needs to happen serially in the main conversation. When a piece of work is well-specified enough to hand off (you could write the brief in a paragraph), doesn't need the full accumulated context of the conversation to do well, and doesn't block the next thing you need to decide — consider spinning it off:

- **Fork yourself** for research or investigation whose *output* you need but whose *intermediate noise* (tool calls, false starts) you don't want cluttering the main context — especially useful for "go find out X" sub-questions that feed back into your own next decision.
- **Fresh subagents**, possibly on a lighter/cheaper model, for mechanical or repetitive work that's well-specified and doesn't need judgment calls beyond what you can put in the brief — e.g. "write the same shape of test for these twelve similar cases" once you've established the pattern on the first one or two yourself. Don't delegate the *first* instance of a new pattern; establish it yourself so the brief you hand off is grounded in something that actually worked, not a guess.
- **Run independent chunks in parallel** — if milestone B doesn't depend on milestone A's output, and both are well-specified, launching them together (multiple Agent calls in one turn) is strictly better than doing them one at a time.

Write delegation briefs the way you'd brief a capable colleague walking in cold: what to do and why, what's already been tried or decided, concrete file paths and names, what "done" looks like — not a one-line command. A subagent with a thin brief either stalls or improvises in ways you didn't want; the fix is a better brief, not doing it yourself instead. After a delegated chunk comes back, still verify it (§4) — a subagent's summary of what it did is not the same as evidence it worked.

## 8. Assume reasonable intent — in the code, and in the ask

Existing code that looks odd usually got that way for a reason: a bug fixed once already, a constraint from something not visible in the current diff, a real tradeoff someone made on purpose. Before "fixing" something that looks wrong, look for why it's there — nearby comments, related code, version history, or just running it to see what actually happens versus what you assumed. If it turns out to genuinely be a bug, you'll understand it well enough to fix it properly and explain why in the commit; if it isn't, you've just avoided breaking something that worked for a reason you couldn't see yet. This applies with extra force mid-refactor: the moment you're moving fast through a lot of code is exactly when it's cheapest to steamroll a subtlety you didn't notice.

The same stance applies to the user's request: take it as a real, considered ask with a sensible goal behind it, and implement *that* goal — not a maximally literal reading, and not an expanded version you think would be better. If a request seems to conflict with something you can see (a constraint, an existing pattern, a previous decision in the conversation), that's worth surfacing, but as "here's what I'm seeing, here's what I'd suggest" — not silently doing something else, and not refusing to proceed. Scope discipline matters here too: implement what was asked, resist folding in adjacent cleanup or "while I'm in here" changes that nobody requested — those are their own milestone if they're worth doing at all, and a separate conversation about whether they are.

## The shape of it, end to end

1. Understand the ask; go verify assumptions against the real code rather than guessing.
2. Write a plan: the milestones, their order, and anything you'd need the user to decide before or during.
3. Get the plan in front of the user (plan mode if available); revise on pushback, cheaply, before starting.
4. For each milestone: do the work (delegating separable pieces where it helps), verify it for real — including extra runs if it's the kind of thing that can be flaky — then commit with a why-focused message.
5. At the end of each milestone, either continue to the obviously-next one, or — only if there's a genuine fork with no clear answer — ask, with a recommended option, and continue once answered.
6. Throughout: treat surprising existing code as probably-intentional until proven otherwise, and treat the user's ask as the real goal to implement, not a starting point to expand from.
