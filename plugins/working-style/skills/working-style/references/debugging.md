# Debug by hypothesis, ideally without needing the user

Load this for a bug, failure or unexpected behaviour whose cause isn't obvious.

- Don't guess-and-check with random edits. Form a hypothesis, find the cheapest test that
  isolates *just* that hypothesis, and only then fix it.
- Name your best guesses plainly ("My two best guesses: …") and say what fix each implies.
- **Prefer debugging you can run end to end yourself.** Before involving the user, ask
  whether you can observe the symptom directly: logs, screenshots, traces, timing
  measurements, a headless or off-screen reproduction, or a scripted harness. If you can,
  **offer it as an option** ("I can run the whole bisection myself and report back,
  about 10 minutes, or we can step through it together"), recommended where it's reliable,
  rather than asking the user to authorise each step.
- When only the user can observe the symptom (a stutter they feel, a glitch on their
  screen, hardware behaviour), run a **bisection with them**: prepare one discrete test at
  a time, change one variable per test, say beforehand what each outcome would mean, then
  "**Say "go" when ready.**" Record the result and narrow down.
- Verify against the actual symptom. A clean CPU trace doesn't clear a stutter the user can
  see; a passing test doesn't clear UI that looks wrong in the browser.
- Don't swap files under an app the user is running to compare old and new code (stash,
  test, pop). Use a temporary checkout instead.
- Once it's solved, add the situation → what happened → solution to `MEMORY.md`
  ([records.md](records.md)) if a later session could hit it again.
