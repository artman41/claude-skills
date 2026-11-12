---
name: reframework
description: >-
  Write, debug, and explain mods and scripts for REFramework (REF, by praydog) — the
  modding framework, scripting platform, and VR injector for Capcom RE Engine games
  (Resident Evil 2/3/4/7/8/Requiem, Monster Hunter Rise/Wilds, Dragon's Dogma 2, Devil
  May Cry 5, Street Fighter 6, Kunitsu-Gami, Onimusha, and more). Use this whenever the
  task involves REFramework Lua scripting (autorun scripts, mod menus), the `sdk`, `re`,
  `imgui`, `draw`, `json`, `fs`, `log`, or `thread` namespaces, `REManagedObject` /
  `RETypeDefinition` / `SystemArray` / the RE Engine type database (TDB), method hooking
  with `sdk.hook`, reading or calling game methods, fields, and singletons via reflection,
  the C++ plugin API (`reframework::API`, `include/reframework`), or the C# REFramework.NET
  API. Trigger on any "do X to an RE Engine game" modding intent — e.g. toggling infinite
  stats in DMC5, reading the player's world position in RE2, scaling monster damage in MH
  Wilds, drawing an on-screen overlay, or iterating engine arrays — even when the user
  names no REF-specific terms and only says things like "RE Engine mod", "praydog
  framework", "REF script", "hook this game function", or names a supported game with a
  modding/scripting intent. Don't rely on built-in knowledge for this API; it is niche and
  easy to get subtly wrong.
---

# REFramework

REFramework (REF) is praydog's open-source mod loader, scripting platform, and VR support
layer for **RE Engine** games (Capcom). It exposes the engine's live type system to **Lua**
scripts and to native **C++** / managed **C#** plugins, letting you read and call any game
method, hook functions, draw overlays, and build in-game menus.

This skill is about getting that API right. The surface is large and idiosyncratic, so the
details here matter more than general intuition. **Lua is the primary and most common
interface** — focus there unless the user clearly wants a C++/C# plugin.

## When you are blocked on game-specific names

The single biggest practical issue: type, method, and field names are **game-specific** and
live in the game's Type Database (TDB). You cannot guess them reliably (e.g. the player
manager singleton is `app.PlayerManager` in some games, `snow.player.PlayerManager` in MHRise,
and reached differently in each). When a script needs a concrete name you don't know:

1. Tell the user to find it in the **Object Explorer** (REFramework menu →
   `DeveloperTools` → `ObjectExplorer`), or the **Singletons** / **Native Singletons** views.
2. Point them at praydog's **`re-engine-mcp`** (an MCP server that gives an AI agent live
   access to a running RE Engine game via REFramework) if they want you to introspect directly.
3. Write the script so unknown names are clearly marked constants at the top, and add
   reflection-based discovery helpers (see `references/recipes.md`) so the user can dump
   candidates themselves.

Never silently invent a plausible-looking type name as if it were verified — say it's a
placeholder the user must confirm.

## Mental model

Everything funnels through the engine's reflection system (the **TDB**):

- **`sdk.find_type_definition("namespace.Type")`** → an `RETypeDefinition`. From it you get
  methods (`get_method`) and fields (`get_field` / `get_fields`).
- **Singletons are the entry points** into game state:
  - `sdk.get_managed_singleton("app.Foo")` → an `REManagedObject` (a GC-managed engine object).
  - `sdk.get_native_singleton("via.Foo")` → a raw `void*`, used with `sdk.call_native_func`.
- **`REManagedObject`** wraps a live engine object. You interact with it mainly by:
  - `obj:call("methodName", args...)` — invoke a method (return value auto-converts to Lua).
  - `obj:get_field("name")` / `obj:set_field("name", value)` — read/write a field.
- **Type names** are `namespace.Type`. The game's own namespace varies (`app.`, `snow.`,
  `offline.` ...); `sdk.game_namespace("PlayerManager")` prefixes the right one for the
  current game, which is how you write multi-game scripts.
- **Overloaded methods** are disambiguated by passing the full prototype as the method name:
  `obj:call("getComponent(System.Type)", t)`.

Return values and arguments are auto-converted between Lua and engine types for normal calls
(numbers, strings, `via.vec3`→`Vector3f`, etc.) — see `references/types.md`. The big
exception is **inside hooks**, where everything is a raw `void*` you must convert yourself.

## Script lifecycle

- **Autorun:** REFramework runs every `*.lua` file in `<game_dir>/reframework/autorun/` at
  startup. This is where mods live. You can also load a script manually via ScriptRunner.
- **One shared Lua state.** All scripts share globals, so **declare everything `local`** to
  avoid clobbering other mods. This is the most common real-world bug.
- **Callbacks** (full list in `references/namespaces.md`) are how your code runs over time:
  - `re.on_frame(fn)` — every frame. Use `draw.*` here. Do **not** call bare `imgui.*` here
    unless wrapping in `imgui.begin_window`.
  - `re.on_draw_ui(fn)` — every frame while REFramework's "Script Generated UI" is open;
    this is where ImGui menu code belongs (it appears in a dropdown in the REF menu).
  - `re.on_application_entry(name, fn)` / `re.on_pre_application_entry(name, fn)` — run at a
    specific point in the engine loop (e.g. `"UpdateBehavior"`, `"LockScene"`,
    `"BeginRendering"`). Names come from `via.ModuleEntry`.
  - `re.on_script_reset(fn)` — cleanup when scripts reload; also fires `on_config_save`.
- **Script reset** destroys and re-creates the Lua state. Objects you created and kept alive
  with `add_ref_permanent` survive; normal references are collected.

## Minimal examples

Read a game value every frame (native singleton → managed object):

```lua
local function get_scene()
    local scene_manager = sdk.get_native_singleton("via.SceneManager")
    local t = sdk.find_type_definition("via.SceneManager")
    return sdk.call_native_func(scene_manager, t, "get_CurrentScene")
end

re.on_frame(function()
    local scene = get_scene()
    if scene == nil then return end
    -- scene is an REManagedObject from here on
    local timescale = scene:call("get_TimeScale")
end)
```

A mod menu with persisted config:

```lua
local config = { enabled = true, speed = 2.0 }

-- Load saved settings (reframework/data/mymod.json)
local saved = json.load_file("mymod.json")
if saved ~= nil then config = saved end

re.on_config_save(function()
    json.dump_file("mymod.json", config)
end)

re.on_draw_ui(function()
    if imgui.tree_node("My Mod") then
        local changed
        changed, config.enabled = imgui.checkbox("Enabled", config.enabled)
        changed, config.speed   = imgui.slider_float("Speed", config.speed, 0.0, 10.0)
        imgui.tree_pop()
    end
end)
```

Hook a method to change its return value (makes the game run faster):

```lua
local scene_t = sdk.find_type_definition("via.Scene")

sdk.hook(
    scene_t:get_method("get_TimeScale"),
    function(args) end,                       -- pre: args are raw void*
    function(retval)                          -- post: convert custom returns
        return sdk.float_to_ptr(2.0)
    end
)
```

Hooking is the most error-prone part of the API. Read `references/hooking.md` before writing
or editing any `sdk.hook` call — raw pointer args, static vs instance `args` offsets, ByRef
out-parameters, and `thread.get_hook_storage()` for passing data pre→post all have sharp edges.

## Core API you will use constantly

| Need | Call |
| --- | --- |
| Look up a type | `sdk.find_type_definition("app.Foo")` |
| Managed singleton | `sdk.get_managed_singleton("app.Foo")` |
| Native singleton | `sdk.get_native_singleton("via.Foo")` + `sdk.call_native_func` |
| Game's namespace prefix | `sdk.game_namespace("Foo")` |
| Call a method | `obj:call("get_Bar")` / `obj:call("Set(System.Int32)", 3)` |
| Read/write a field | `obj:get_field("_Foo")` / `obj:set_field("_Foo", v)` |
| typeof for `System.Type` args | `sdk.typeof("via.render.Mesh")` |
| Create an object | `sdk.create_instance("app.Foo", true)` |
| Hook a method | `sdk.hook(type:get_method("Foo"), pre, post)` |
| Which game is this? | `reframework:get_game_name()` ("re2", "dmc5", "mhrise", ...) |
| Iterate an engine array | `arr:get_elements()` then `ipairs`, **or** `pairs(arr)` |

## Critical gotchas

These are the mistakes that actually break REFramework scripts. Keep them in mind:

- **Use `local` for everything.** The Lua state is shared across all mods.
- **Never `ipairs` a raw `SystemArray`.** It skips element 0 and overruns the end. Either call
  `arr:get_elements()` first (returns a real Lua table) or use `pairs(arr)`.
- **In hooks, args/retval are raw `void*`.** Convert with `sdk.to_managed_object`,
  `sdk.to_int64`, `sdk.to_float`, etc. For instance methods `args[1]`=thread context,
  `args[2]`=`this`, params follow; for static methods params start at `args[2]`. Return custom
  values via `sdk.to_ptr` / `sdk.float_to_ptr`.
- **Be careful hooking `get_`/`set_` accessors.** They're tiny, so the compiler often merges
  several into one function; your hook may fire for unrelated calls. Check the disassembly in
  Object Explorer and verify the object type in `args` before acting.
- **Performance: cache reflection lookups.** `obj:call(...)` and `get_field` do a hashmap
  lookup each time. In hot paths (`on_frame`, per-entity `update` hooks), cache the
  `RETypeDefinition`, `REMethodDefinition`, and `REField` once outside the loop.
- **Reference counting is mostly automatic** — but objects the engine hands you fresh (arrays,
  results of `create_instance`) may need `add_ref()` / `release()`. Setting fields via
  `obj.field = x` handles refcounts for you; don't also call `add_ref_permanent`/`force_release`.
- **`ValueType:set_field` is local only** — it doesn't change anything in-game until you pass
  the ValueType into a method that consumes it.
- **ByRef (`T**`) out-params aren't auto-supported.** They can only be read in the post hook;
  stash the pointer in `thread.get_hook_storage()` during pre. See `references/hooking.md`.
- **Colors:** `imgui` and `draw` generally expect **ABGR**; `_argb`-suffixed functions take ARGB.
- **File paths are sandboxed.** `json`/`fs` paths are relative (no `..`, no absolute paths) and
  resolve under `reframework/data/` by default.

## Reference files

Load the one relevant to the task — don't pull in all of them:

- **`references/namespaces.md`** — every function in `sdk`, `re`, `imgui`, `draw`, `json`,
  `fs`, `log`, `thread`, `reframework`, with signatures. The API dictionary.
- **`references/types.md`** — `REManagedObject`, `RETypeDefinition`, `REField`,
  `REMethodDefinition`, `SystemArray`, `ValueType`, and the math types (`Vector2f/3f/4f`,
  `Matrix4x4f`, `Quaternion`, `RETransform`), plus the Lua↔engine type conversion rules.
- **`references/hooking.md`** — `sdk.hook` / `sdk.hook_vtable` in depth: argument layout,
  `PreHookResult`, converting raw pointers, ByRef out-params, `thread.get_hook_storage`,
  and the hooking gotchas. Read before writing any hook.
- **`references/recipes.md`** — copy-ready patterns: get the local player per game, enumerate
  components, generate enum tables, keybinding systems, world-to-screen drawing, 3D gizmos,
  config save/load, best practices, and reflection-based name discovery.
- **`references/plugins.md`** — the native C++ plugin API (`reframework::API`,
  `reframework_plugin_initialize`), the C# REFramework.NET API, build/placement, and tools
  (Object Explorer, Chain Viewer, `re-engine-mcp`).

## Authoritative sources

- Docs: <https://refdocs.praydog.com/>
- Source: <https://github.com/praydog/REFramework> (example Lua in `scripts/`, example plugin
  in `examples/example_plugin/`, plugin headers in `include/reframework/`)

The API signatures in this skill's reference files were taken from REFramework's own Lua
binding source (`src/mods/bindings/`, `src/mods/ScriptRunner.cpp`), so treat them as accurate.
What is *not* fixed is **game-specific content** — the type, method, field, and singleton names
that vary per game and per nightly. Resolve those against the running game (Object Explorer /
`re-engine-mcp`), not by guessing.
