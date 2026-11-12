# reframework

A Claude Code skill for writing, debugging, and explaining mods and scripts for [REFramework](https://github.com/praydog/REFramework) (REF, by praydog) — the modding framework, scripting platform, and VR injector for Capcom RE Engine games (Resident Evil 2/3/4/7/8/Requiem, Monster Hunter Rise/Wilds, Dragon's Dogma 2, Devil May Cry 5, Street Fighter 6, and more).

It gives Claude an accurate, source-grounded map of the REFramework Lua API (the `sdk`, `re`, `imgui`, `draw`, `json`, `fs`, `log`, and `thread` namespaces), the RE Engine type system (`REManagedObject`, `RETypeDefinition`, `SystemArray`, the type database), method hooking with `sdk.hook`, and the C++ / C# plugin APIs — plus the gotchas that make this niche API easy to get subtly wrong (shared Lua state, `ipairs` on engine arrays, raw `void*` hook arguments, caching reflection lookups, and more).

See [`skills/reframework/SKILL.md`](skills/reframework/SKILL.md) for the full skill content, with deeper reference files under [`skills/reframework/references/`](skills/reframework/references/):

- `namespaces.md` — every function in each global namespace.
- `types.md` — the object/type system and Lua↔engine conversion rules.
- `hooking.md` — `sdk.hook` in depth (arg layout, `PreHookResult`, ByRef, hook storage).
- `recipes.md` — copy-ready patterns (per-game local player, components, config, keybinds, world-to-screen, gizmos).
- `plugins.md` — the native C++ and C# (REFramework.NET) plugin APIs and tooling.

## Install

```
/plugin install reframework@claude-skills
```

(requires the `claude-skills` marketplace to be added first — see the [repo README](../../README.md))

## Triggering

This skill activates automatically once installed, whenever a task involves REFramework or RE Engine modding — including when you only name a supported game with a modding intent ("make a mod menu for DMC5", "read the player's HP in RE2", "hook the damage function in Monster Hunter Wilds"). You can also invoke it explicitly:

```
/reframework
```

## Sources

The API details are grounded in REFramework's docs (<https://refdocs.praydog.com/>) and its Lua binding source (`src/mods/bindings/` and `src/mods/ScriptRunner.cpp` in [praydog/REFramework](https://github.com/praydog/REFramework)). Game-specific type/method/field names vary per game and build; the skill directs you to the in-game Object Explorer / `re-engine-mcp` to confirm them rather than guessing.
