# REFramework Lua Namespaces

Signatures for every global namespace. Types (`REManagedObject`, `RETypeDefinition`, math
types, etc.) are in `types.md`; hooking detail is in `hooking.md`.

## Contents
- [`sdk`](#sdk) — the type database, singletons, calls, creation, conversions
- [`re`](#re) — callbacks (frame, UI, engine entry points)
- [`imgui`](#imgui) — Dear ImGui bindings for menus
- [`draw`](#draw) — 2D/3D overlay drawing
- [`json`](#json) — JSON load/dump
- [`fs`](#fs) — sandboxed filesystem
- [`log`](#log) — logging
- [`thread`](#thread) — thread id + hook storage
- [`reframework`](#reframework) — framework info + input

---

## `sdk`

The main gateway to the engine. Hooking functions (`sdk.hook`, `sdk.hook_vtable`,
`PreHookResult`) are documented in `hooking.md`.

### Type / singleton lookup
- `sdk.find_type_definition(name) -> RETypeDefinition` — look up a type by full name
  (`"app.Foo"`, `"via.Scene"`, `"System.Int32"`).
- `sdk.typeof(name) -> System.Type` — runtime `System.Type` for a name; equals
  `find_type_definition(name):get_runtime_type()`. Use when a method parameter is a
  `System.Type` (e.g. `getComponent(System.Type)`).
- `sdk.get_native_singleton(name) -> void*` — native singleton pointer; use with
  `call_native_func`. Names from Object Explorer's **Native Singletons** view.
- `sdk.get_managed_singleton(name) -> REManagedObject` — managed singleton. Names from the
  **Singletons** view.
- `sdk.game_namespace(name) -> string` — prefixes `name` with the current game's namespace
  (e.g. `app.` in DMC5, `offline.` in RE3). Essential for multi-game scripts.
- `sdk.get_tdb_version() -> int` — type DB version; a rough proxy for the RE Engine version.
- `sdk.get_primary_camera() -> REManagedObject` — the camera the engine is currently using.
- `sdk.get_thread_context()` — the current thread context.

### Method calls
- `sdk.call_native_func(object, type_definition, method_name, args...) -> any` — call a method
  on a **native** object (one from `get_native_singleton`). Pass the full prototype for
  overloads.
- `sdk.call_object_func(managed_object, method_name, args...) -> any` — call a method on a
  managed object. Prefer the shorthand `managed_object:call(method_name, args...)`.

```lua
local scene_manager = sdk.get_native_singleton("via.SceneManager")
local t = sdk.find_type_definition("via.SceneManager")
local scene = sdk.call_native_func(scene_manager, t, "get_CurrentScene")
if scene ~= nil then
    scene:call("set_TimeScale", 5.0)   -- scene is managed, so use :call
end
```

### Field access (native)
- `sdk.get_native_field(object, type_definition, field_name) -> any`
- `sdk.set_native_field(object, type_definition, field_name, value)`

Used mostly to read ValueType fields of raw pointers inside hooks:
```lua
local pos_t = sdk.find_type_definition("via.Position")
local x = sdk.get_native_field(args[3], pos_t, "x")
```

### Object creation
- `sdk.create_instance(typename, simplify=false) -> REManagedObject` — equivalent to
  `find_type_definition(typename):create_instance()`. If it returns `nil`, retry with
  `simplify=true`.
- `sdk.create_instance_global(typename, simplify=false)` — same, but exempt from Lua GC.
- `sdk.create_managed_string(str) -> System.String`.
- `sdk.create_managed_array(type, length) -> SystemArray` — `type` is a `System.Type`,
  `RETypeDefinition`, or type-name string.
- `sdk.create_delegate(type, num_methods) -> Delegate`.
- `sdk.create_resource(typename, resource_path) -> REResource` — `nil` if the type doesn't
  match the file or isn't a resource type.
- `sdk.create_userdata(typename, userdata_path) -> REManagedObject` — load a `via.UserData`;
  `typename` may be `"via.UserData"` if you don't know the exact type.
- `sdk.create_userdata_global(type_name, name)` — same, exempt from GC.

**Boxed primitives** (each returns an `REManagedObject` wrapping the value):
`sdk.create_sbyte`, `create_byte`, `create_int16`, `create_uint16`, `create_int32`,
`create_uint32`, `create_int64`, `create_uint64`, `create_single`, `create_double` — all take
a single `number`.

### Type checks & conversions
Mostly needed inside hooks, where arguments arrive as raw `void*`.
- `sdk.is_managed_object(value) -> bool` — thorough validity check; use sparingly (slow).
- `sdk.to_managed_object(value) -> REManagedObject|nil` — from a managed object, a numeric
  address, or a `void*`.
- `sdk.to_ptr(value) -> void*|nil` — from a managed object, number, boolean, or `void*`.
- `sdk.to_int64(value) -> int64` — from a `void*`. Mask for smaller types: `& 1` (bool),
  `& 0xFF` (byte), `& 0xFFFF` (2-byte), `& 0xFFFFFFFF` (4-byte).
- `sdk.to_float(value) -> float` / `sdk.to_double(value) -> double` — from a `void*`.
- `sdk.float_to_ptr(number) -> void*` — the usual way to return a float from a post hook.
- `sdk.to_valuetype(obj, t) -> ValueType` — reinterpret a number/`void*` as type `t`
  (`RETypeDefinition` or name string). A value already a ValueType is returned unchanged.
- `sdk.to_resource(ptr) -> REResource`.

### Serialization
- `sdk.deserialize(data) -> REManagedObject[]` — build managed objects from raw RSZ data (e.g.
  from a `.scn`). `data` is a Lua table of bytes starting at the `RSZ` header.

```lua
local rsz_data = json.load_file("Foobar.json")
for i, v in ipairs(sdk.deserialize(rsz_data)) do
    log.info(v:get_type_definition():get_full_name())
end
```

### Misc
- `sdk.copy_to_clipboard(text) -> bool`.

---

## `re`

Callback creators and small utilities. Only `application_entry` and `gui_draw_element` come as
pre/post **pairs** (pre before the engine's work, post after); `on_frame`, `on_draw_ui`,
`on_script_reset`, and `on_config_save` are single callbacks.

Any `re` callback may return **`re.CallbackNextAction.STOP`** to unregister itself (returning
nothing / `CallbackNextAction.CONTINUE` keeps it) — useful for one-shot setup that should run
once and detach.

- `re.on_frame(fn)` — every frame. `draw.*` is valid here. Avoid bare `imgui.*` (wrap in
  `imgui.begin_window`). Keep game-method calls minimal here for performance.
- `re.on_draw_ui(fn)` — every frame while REFramework's "Script Generated UI" menu is open.
  ImGui calls belong here; output appears in a dropdown in the REF menu.
- `re.on_pre_application_entry(name, fn)` / `re.on_application_entry(name, fn)` — run `fn` at a
  specific engine module entry. `name` is one of the `via.ModuleEntry` names (hundreds exist:
  `"Update"`, `"UpdateBehavior"`, `"LockScene"`, `"BeginRendering"`, `"EndRendering"`,
  `"UpdateMotion"`, `"UpdateHID"`, etc.). This is how you run logic at the right point in the
  frame — e.g. apply transform changes on `"LockScene"` so they stick.
- `re.on_pre_gui_draw_element(fn)` / `re.on_gui_draw_element(fn)` — `fn(element, context)`
  where `element` is an `REComponent`. The **pre** callback must return a `bool`; returning
  `false` prevents the element from drawing (used to hide HUD elements).
- `re.on_script_reset(fn)` — on script reload; good for cleanup. Also triggers `on_config_save`.
- `re.on_config_save(fn)` — when REFramework is about to save its config; write your settings here.
- `re.msg(text)` — blocking MessageBox. Game pauses until OK. Good for fatal setup errors.

```lua
re.on_pre_gui_draw_element(function(element, context)
    local go = element:call("get_GameObject")
    if go == nil then return true end
    local name = go:call("get_Name")
    if name == "GUIReticle" or name == "GUI_Reticle" then
        return false   -- hide the crosshair
    end
    return true
end)
```

Full lists of valid `on_application_entry` names (Initialize/Setup/Start/Update/Terminate/
Finalize phases) are in the docs; find them by viewing `via.ModuleEntry` in Object Explorer.

---

## `imgui`

Dear ImGui bindings. **Where to call them:** inside `re.on_draw_ui` (recommended for menus),
or inside `re.on_frame` only within an `imgui.begin_window`/`end_window` pair. Widgets that
edit a value return `changed, value` (sometimes more) — reassign the value.

```lua
re.on_draw_ui(function()
    local changed, val = imgui.slider_float("Speed", speed, 0.0, 10.0)
    if changed then speed = val end
end)
```

### Windows, trees, layout
`begin_window(name, open, flags) -> bool`, `end_window()` (on_frame only; returns false when
the user closes it) · `begin_child_window(size, border, flags)`, `end_child_window()` ·
`begin_group()`, `end_group()` · `begin_rect()`, `end_rect(additional_size, rounding)` ·
`begin_disabled(disabled=true)`, `end_disabled()` · `collapsing_header(name)` ·
`tree_node(label)`, `tree_node_ptr_id(id, label)`, `tree_node_str_id(id, label)`, `tree_pop()`
(every opened tree needs a matching `tree_pop`) · `set_next_item_open(is_open, condition)` ·
`begin_list_box(label, size)`, `end_list_box()` · `same_line()`, `spacing()`, `new_line()`,
`separator()`, `indent(w)`, `unindent(w)` · `item_size(pos, size)`, `item_add(label, pos, size)`
· `set_item_default_focus()`.

### Menus, popups, tooltips
`begin_main_menu_bar()`/`end_main_menu_bar()`, `begin_menu_bar()`/`end_menu_bar()`,
`begin_menu(label, enabled)`/`end_menu()`, `menu_item(label, shortcut, selected, enabled)` ·
`open_popup(str_id, flags)`, `begin_popup(str_id, flags)`/`end_popup()`,
`begin_popup_context_item(str_id, flags)`, `close_current_popup()`, `is_popup_open(str_id)` ·
`begin_tooltip()`/`end_tooltip()`, `set_tooltip(text)`.

### Window position/size & cursor
`set_next_window_pos(pos, condition, pivot)`, `set_next_window_size(size, condition)`,
`get_window_size()`, `get_window_pos()`, `get_display_size()` (all return `Vector2f`) ·
`get_cursor_pos()`/`set_cursor_pos(pos)`, `get_cursor_start_pos()`,
`get_cursor_screen_pos()`/`set_cursor_screen_pos(pos)`, `calc_text_size(text) -> Vector2f` ·
`get_id()`, `push_id(id)`/`pop_id()` (id: int, string, or `void*` — use to disambiguate
widgets in loops).

### Item width & style stacks
`push_item_width(w)`/`pop_item_width()`, `set_next_item_width(w)`, `calc_item_width()` ·
`push_style_color(style_color, color)`/`pop_style_color(count)`,
`push_style_var(idx, value)`/`pop_style_var(count)`.

### Scrolling
`get_scroll_x/y()`, `set_scroll_x/y(v)`, `get_scroll_max_x/y()`,
`set_scroll_here_x/y(ratio)`, `set_scroll_from_pos_x/y(local, ratio)`.

### Widgets
- `button(label, size) -> bool`, `small_button(label) -> bool`,
  `invisible_button(id, size, flags)`, `arrow_button(id, dir)`.
- `text(text)`, `text_colored(text, color)` (color is ARGB).
- `checkbox(label, value) -> changed, value`.
- `drag_float/float2/float3/float4(label, value, speed, min, max, fmt?) -> changed, value`
  (value is number / `Vector2f` / `Vector3f` / `Vector4f`).
- `drag_int(label, value, speed, min, max, fmt?) -> changed, value`.
- `slider_float/slider_int(label, value, min, max, fmt?) -> changed, value`.
- `input_text(label, value, flags?) -> changed, value, sel_start, sel_end`.
- `input_text_multiline(label, value, size, flags?) -> changed, value, sel_start, sel_end`.
- `combo(label, selection, values) -> changed, value` (`selection`/`value` is the **key** into
  `values`, whose values are strings; for a plain array table that key is the 1-based index).
- `progress_bar(progress, size, overlay)` (progress 0–1; `size` is `Vector2f`).
- Color: `color_picker/color_picker3/color_picker4`, `color_edit/color_edit3/color_edit4`,
  and `_argb` variants — all `-> changed, value`. Non-`_argb` take **ABGR**.

### Item state & input
`is_item_hovered(flags)`, `is_item_active()`, `is_item_focused()` · `get_mouse() -> Vector2f`
(window space) · `is_key_down/pressed/released(key)`, `get_key_index(imgui_key)` ·
`is_mouse_down/clicked/released/double_clicked(button)` · `get_clipboard()`, `set_clipboard(text)`.

### Fonts
`load_font(filepath, size, ranges?)` (from `reframework/fonts`; `nil` path = default; returns a
handle), `push_font(font, size?)`/`pop_font()`, `push_font_size(size)`/`pop_font_size()`,
`get_default_font_size()`.

### Tables
`begin_table(str_id, column, flags, outer_size, inner_width?)`/`end_table()` ·
`table_next_row(row_flags, min_row_height)`, `table_next_column()`,
`table_set_column_index(i)` · `table_setup_column(label, flags, init_width_or_weight, user_id)`,
`table_setup_scroll_freeze(cols, rows)`, `table_headers_row()`, `table_header(label)` ·
`table_get_sort_specs()`, `table_get_column_count/index()`, `table_get_row_index()`,
`table_get_column_name(col)`, `table_get_column_flags(col)`,
`table_set_bg_color(target, color, column)`.

### Draw lists (ImGui, distinct from the `draw` namespace)
Retrieve: `get_window_draw_list()`, `get_background_draw_list()`, `get_foreground_draw_list()`.
Window-level path helpers: `draw_list_path_clear()`, `draw_list_path_line_to(pos)`,
`draw_list_path_stroke(color, closed, thickness)`.
`ImDrawList` methods (called as `dl:method(...)`): `add_line`, `add_rect`, `add_rect_filled`,
`add_rect_filled_multi_color`, `add_quad`, `add_quad_filled`, `add_triangle`,
`add_triangle_filled`, `add_circle`, `add_circle_filled`, `add_ngon`, `add_ngon_filled`,
`add_ellipse`, `add_ellipse_filled`, `add_text(pos, color, text)`, `add_bezier_cubic`,
`add_bezier_quadratic`; clip-rect and `path_*` helpers mirror ImGui.

### Enums
`imgui.new_enum(name, key1, val1, key2, val2, ...)` registers an enum table (used e.g. for
`ImGuizmoOperation`/`ImGuizmoMode` with `draw.gizmo`).

---

## `draw`

Overlay drawing. 2D functions take screen coordinates; `world_*`/3D functions take world
positions and project internally. Call these from `re.on_frame`.

- `draw.world_to_screen(world_pos) -> Vector2f|nil` — project a world point; `nil` if off-screen.
  `world_pos` may be `Vector2f/3f/4f`. The building block for world-anchored UI.
- `draw.world_text(text, pos_3d, color?)` — text at a world position; `color` defaults to
  `0xFFFFFFFF`.
- `draw.text(text, x, y, color)` — screen-space text.
- `draw.filled_rect(x, y, w, h, color)`, `draw.outline_rect(x, y, w, h, color)`.
- `draw.line(x1, y1, x2, y2, color)`.
- `draw.outline_circle(x, y, radius, color, num_segments=32)`,
  `draw.filled_circle(x, y, radius, color, num_segments=32)`.
- `draw.outline_quad(x1,y1,x2,y2,x3,y3,x4,y4, color)`,
  `draw.filled_quad(x1,y1,x2,y2,x3,y3,x4,y4, color)`.
- `draw.sphere(world_pos, radius, color, outline)` — 3D sphere (2D approximation).
- `draw.capsule(world_start, world_end, radius, color, outline)`.
- `draw.cube(matrix)`, `draw.grid(matrix, size)`.
- `draw.gizmo(unique_id, matrix, operation?, mode?) -> changed, matrix` — interactive
  ImGuizmo transform handle. `unique_id` an int64 unique per gizmo (an object's address works;
  shared ids move together). `operation` defaults to `UNIVERSAL` (`imgui.ImGuizmoOperation`),
  `mode` defaults to `WORLD` (`imgui.ImGuizmoMode`). See `recipes.md` for a full example.

Color is typically **ABGR** (`0xAABBGGRR`) here, matching `imgui`'s non-`_argb` functions.

---

## `json`

Paths resolve under `reframework/data/`.
- `json.load_string(json_str) -> value|nil`.
- `json.dump_string(value, indent=-1) -> string` (empty string on error; `0`=no indent,
  `-1`=no indent and no line breaks).
- `json.load_file(filepath) -> value|nil` (`nil` if missing).
- `json.dump_file(filepath, value, indent=4) -> bool`.

Round-trip caveat: JSON objects have string keys, so Lua tables with integer gaps or mixed
keys may come back with stringified keys (`{9,8,nil,6}` → `{["1"]=9,["2"]=8,["4"]=6}`). Keep
config tables as clean sequences or clean string-keyed maps.

---

## `fs`

Sandboxed filesystem. Also governs `io.open`, `require`, etc.
- `fs.glob(filter, modifier?) -> string[]` — `filter` is a **regex** string. `modifier` picks
  the base: `$natives` or `$autorun`.
- `fs.read(filename) -> string`.
- `fs.write(filename, data)`.

Base dirs: default → `reframework/data/`; `$natives/` → `natives/` next to the REF DLL;
`$autorun/` → `reframework/autorun/`. **Rules:** paths must be relative (no `..`, no absolute
paths); writing `.dll`/`.exe` is blocked.

```lua
local json_files = fs.glob([[my-cool-mod\\.*json]])
for _, v in ipairs(json_files) do
    -- v like "my-cool-mod\config-1.json"
end
```

---

## `log`

- `log.info(text)`, `log.warn(text)`, `log.error(text)`.
- `log.debug(text)` — only visible in DebugView, a debugger, or the "Spawn Debug Console"
  under ScriptRunner.
- `log.set_level(level)` — `"info"`, `"warn"`, `"error"`, or `"debug"`; messages below are
  suppressed.

Output also lands in the game-folder log (e.g. `re2_framework_log.txt`). Always `tostring()`
non-string values before concatenating.

---

## `thread`

- `thread.get_id() -> int` — current thread id.
- `thread.get_hash() -> int` — hash of the current thread id.
- `thread.get_hook_storage() -> table` — per-hook ephemeral table for passing data from a pre
  hook to its post hook. Prefer this over globals; it's safe for recursion and cleared at the
  end of the post hook. See `hooking.md`.

---

## `reframework`

Framework info and raw input.
- `reframework:get_game_name() -> string` — `"re2"`, `"re3"`, `"re4"`, `"re7"`, `"re8"`,
  `"dmc5"`, `"mhrise"`, etc. Branch your code on this.
- `reframework:is_drawing_ui() -> bool` — is the REF menu open.
- `reframework:save_config()` — trigger a config save.
- Input: `reframework:is_key_down(vkey)` (Windows virtual key code),
  `reframework:get_keyboard_state() -> array` (256 entries, nonzero = pressed),
  `reframework:get_first_key_down() -> int|nil` (lowest vkey currently down).
- Version/build: `get_version_string()`, `get_version_major/minor/patch()`,
  `get_commit_count()`, `get_branch()`, `get_commit_hash()`, `get_tag()`, `get_tag_long()`,
  `get_commits_past_tag()`, `get_build_date()`, `get_build_time()`.
