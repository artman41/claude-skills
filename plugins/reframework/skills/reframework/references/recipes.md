# REFramework Recipes & Patterns

Copy-ready solutions to the tasks that come up constantly. Names marked as placeholders
(`app.Foo`) are game-specific — confirm them in Object Explorer. These are cleaned-up versions
of the official example snippets.

## Contents
- [Get the local player (per game)](#get-the-local-player)
- [Get components from a game object](#get-components)
- [Current time / uptime](#time)
- [Generate an enum table](#generate-enums)
- [Config save / load](#config)
- [Keybinding system](#keybinds)
- [World-to-screen drawing](#world-to-screen)
- [3D gizmos on a transform and its joints](#gizmos)
- [Cache lookups for performance](#caching)
- [Discover names by reflection](#discovery)
- [Organize code into modules](#modules)
- [Best practices summary](#best-practices)

---

## Get the local player

The player manager singleton and accessor differ per game. Dispatch on `get_game_name()`:

```lua
local gn = reframework:get_game_name()

local function get_localplayer()
    if gn == "re2" or gn == "re3" then
        local pm = sdk.get_managed_singleton(sdk.game_namespace("PlayerManager"))
        return pm and pm:call("get_CurrentPlayer")
    elseif gn == "dmc5" then
        local pm = sdk.get_managed_singleton(sdk.game_namespace("PlayerManager"))
        if pm == nil then return nil end
        local comp = pm:call("get_manualPlayer")
        return comp and comp:call("get_GameObject")
    elseif gn == "re8" then
        local pm = sdk.get_managed_singleton(sdk.game_namespace("PropsManager"))
        return pm and pm:call("get_Player")
    elseif gn == "mhrise" then
        local pm = sdk.get_managed_singleton("snow.player.PlayerManager")
        if pm == nil then return nil end
        local comp = pm:call("findMasterPlayer")
        return comp and comp:call("get_GameObject")
    end
    return nil
end
```

---

## Get components

```lua
-- One component by type name (returns the component or nil)
local function get_component(game_object, type_name)
    local t = sdk.typeof(type_name)
    if t == nil then return nil end
    return game_object:call("getComponent(System.Type)", t)
end

-- All components as a Lua table
local function get_components(game_object)
    local transform = game_object:call("get_Transform")
    if not transform then return {} end
    return game_object:call("get_Components"):get_elements()
end

-- Example: find the mesh
local mesh = get_component(game_object, "via.render.Mesh")
```

---

## Time

```lua
-- Engine uptime in seconds (works everywhere)
local app_t = sdk.find_type_definition("via.Application")
local get_uptime = app_t:get_method("get_UpTimeSecond")
local function get_time()
    return get_uptime:call(nil)   -- static
end
-- Newer builds also expose os.clock().
```

---

## Generate enums

Build a Lua table from a type's static fields — handy for buttons, input modes, states:

```lua
local function generate_enum(typename)
    local t = sdk.find_type_definition(typename)
    if not t then return {} end
    local enum = {}
    for _, field in ipairs(t:get_fields()) do
        if field:is_static() then
            enum[field:get_name()] = field:get_data(nil)
        end
    end
    return enum
end

local GamePadButton = generate_enum("via.hid.GamePadButton")
```

---

## Config

Persist settings as JSON under `reframework/data/`, saving when REF saves its config:

```lua
local config = { enabled = true, scale = 1.0, color = 0xFFFF00FF }

local saved = json.load_file("mymod/config.json")
if saved ~= nil then
    for k, v in pairs(saved) do config[k] = v end   -- merge, so new keys keep defaults
end

re.on_config_save(function()
    json.dump_file("mymod/config.json", config)
end)
```

Keep `config` a clean string-keyed table (JSON round-trips those safely).

---

## Keybinds

Edge-detect key presses (fire once per press, not every frame it's held):

```lua
local prev = {}
local function key_pressed(vkey)
    local down = reframework:is_key_down(vkey)
    local was  = prev[vkey]
    prev[vkey] = down
    return down and not was
end

re.on_frame(function()
    if key_pressed(0x79) then   -- F10 (Windows virtual key code)
        config.enabled = not config.enabled
    end
end)

-- Interactive "press a key to bind" (in on_draw_ui):
-- local key = reframework:get_first_key_down()
-- if key ~= nil then config.bound_key = key end
```

---

## World-to-screen

Project world positions to the screen and draw there (from `re.on_frame`):

```lua
re.on_frame(function()
    local player = get_localplayer()
    if player == nil then return end
    local transform = player:call("get_Transform")
    local pos = transform:call("get_Position")        -- Vector4f (world)
    local screen = draw.world_to_screen(pos)
    if screen ~= nil then
        draw.text("PLAYER", screen.x, screen.y, 0xFFFFFFFF)   -- ABGR
        draw.filled_circle(screen.x, screen.y, 4, 0xFF00FF00, 16)
    end
    -- Or let the engine project for you:
    draw.world_text("PLAYER", pos, 0xFFFFFFFF)
end)
```

---

## Gizmos

Interactive transform handles. Give each gizmo a stable unique id (the object's address).
Queue changes and apply them at a safe point (`"LockScene"`) so parent transforms don't fight:

```lua
local joint_work = {}

re.on_pre_application_entry("LockScene", function()
    for _, w in pairs(joint_work) do w.func(w.mat) end
    joint_work = {}
end)

re.on_frame(function()
    local player = get_localplayer()
    if player == nil then return end
    local transform = player:call("get_Transform")
    if transform == nil then return end

    local mat = transform:call("get_WorldMatrix")
    local changed
    changed, mat = draw.gizmo(transform:get_address(), mat)
    if changed then
        transform:set_rotation(mat:to_quat())
        transform:set_position(mat[3])
    end

    -- Gizmos on joints near the mouse
    local joints = transform:call("get_Joints")
    local mouse = imgui.get_mouse()
    for _, joint in ipairs(joints:get_elements()) do
        local jmat = joint:call("get_WorldMatrix")
        local a = draw.world_to_screen(jmat[3])
        local b = draw.world_to_screen(jmat[3] + Vector3f.new(0, 0.1, 0))
        if a and b and (a - mouse):length() <= (a - b):length() then
            local jchanged, newmat = draw.gizmo(joint:get_address(), jmat)
            if jchanged then
                table.insert(joint_work, { mat = newmat, func = function(m)
                    joint:call("set_Rotation", m:to_quat())
                    joint:call("set_Position", m[3])
                end })
            end
        end
    end
end)
```

---

## Caching

`:call` and field access do a hashmap lookup every time. In hot paths, resolve once:

```lua
local scene_t      = sdk.find_type_definition("via.Scene")
local get_timescale = scene_t:get_method("get_TimeScale")
local set_timescale = scene_t:get_method("set_TimeScale")

re.on_frame(function()
    local scene = get_scene()
    if scene == nil then return end
    local ts = get_timescale:call(scene)          -- cached method
    set_timescale:call(scene, ts)                 -- no per-frame lookup
end)
```

Cache `RETypeDefinition`, `REMethodDefinition`, and `REField` at file scope (as `local`s),
never inside the per-frame callback.

---

## Discovery

When you don't know a name, dump candidates at runtime instead of guessing.

```lua
-- All methods of a type
local t = sdk.find_type_definition("app.Foo")
for _, m in ipairs(t:get_methods()) do
    log.info(m:get_name() .. "  params=" .. tostring(m:get_num_params()))
end

-- All fields of a type
for _, f in ipairs(t:get_fields()) do
    log.info(f:get_name() .. " : " .. f:get_type():get_full_name())
end

-- Dump an existing object's fields with live values
local function dump_object(obj)
    local td = obj:get_type_definition()
    log.info("== " .. td:get_full_name() .. " ==")
    for _, f in ipairs(td:get_fields()) do
        local ok, val = pcall(function() return f:get_data(obj) end)
        log.info("  " .. f:get_name() .. " = " .. (ok and tostring(val) or "<err>"))
    end
end
```

For interactive exploration, add an Object Explorer button for any object:
```lua
re.on_draw_ui(function()
    object_explorer:handle_address(some_object:get_address())
end)
```

This, plus the in-menu Object Explorer (`DeveloperTools → ObjectExplorer`) and praydog's
`re-engine-mcp`, is how you resolve game-specific names reliably.

---

## Modules

Split large mods into files. Put a module in a subfolder of `autorun`, return a table, and
`require` it with a path relative to `autorun` (no extension):

```lua
-- reframework/autorun/mymod/util.lua
local util = {}
function util.clamp(x, lo, hi) return math.max(lo, math.min(hi, x)) end
return util
```
```lua
-- reframework/autorun/mymod_main.lua
local util = require("mymod/util")
```

---

## Best practices summary

- **`local` everything** — one shared Lua state across all mods.
- **Guard `nil`** at every step — singletons, players, components, and transforms can all be
  `nil` during loads, menus, and scene transitions. Return early.
- **`get_elements()` before iterating** engine arrays, or use `pairs` — never `ipairs` on a raw
  `SystemArray`.
- **Cache reflection lookups** in hot paths.
- **Hook sparingly**; prefer polling in `on_frame` for read-only needs. See `hooking.md` before
  hooking accessors.
- **ImGui in `on_draw_ui`**; `draw.*` in `on_frame`.
- **Save config in `on_config_save`**; clean up in `on_script_reset`.
- **Consider a native/C# plugin** for heavy per-frame work (see `plugins.md`).
