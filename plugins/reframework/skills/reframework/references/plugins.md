# REFramework Plugins (C++ / C#) & Tools

Lua covers most mods. Reach for a plugin when Lua can't do something, or is too slow for
heavy per-frame work. A common hybrid: keep logic in Lua, expose expensive operations from a
native plugin.

## Contents
- [Native C++ plugins](#cpp)
- [C# plugins (REFramework.NET)](#csharp)
- [Choosing Lua vs C++ vs C#](#choosing)
- [Tools](#tools)

---

## C++ plugins

Native DLLs placed in `<game_dir>/reframework/plugins/`. They get more freedom than Lua plus
access to SDK functions and callbacks for rendering, input, and game code. REFramework can also
act as a plain DLL loader for plugins that don't use its API.

**Setup:** add the repo's `include/` directory to your include path and include
`reframework/API.hpp` (C++ interface) — there's also a C header `reframework/API.h`.

**Exported entry points** (both optional):

```cpp
#include "reframework/API.hpp"

// OPTIONAL: version gate. Major mismatch or too-low minor => plugin won't load;
// patch mismatch => loads with a warning.
extern "C" __declspec(dllexport)
void reframework_plugin_required_version(REFrameworkPluginVersion* version) {
    version->major = REFRAMEWORK_PLUGIN_VERSION_MAJOR;
    version->minor = REFRAMEWORK_PLUGIN_VERSION_MINOR;
    version->patch = REFRAMEWORK_PLUGIN_VERSION_PATCH;
    // version->game_name = "MHRISE"; // optionally restrict to one game
}

using namespace reframework;

// OPTIONAL: main initialization — register callbacks here.
extern "C" __declspec(dllexport)
bool reframework_plugin_initialize(const REFrameworkPluginInitializeParam* param) {
    API::initialize(param);

    const auto functions = param->functions;
    functions->on_lua_state_created(on_lua_state_created);
    functions->on_lua_state_destroyed(on_lua_state_destroyed);
    functions->on_frame(on_frame);
    functions->on_pre_application_entry("BeginRendering", on_pre_begin_rendering);
    functions->on_post_application_entry("EndRendering", on_post_end_rendering);
    functions->on_device_reset(on_device_reset);
    functions->on_message((REFOnMessageCb)on_message);
    functions->log_info("%s %s", "Hello", "info");
    return true;
}
```

You can instead export a `DllMain` if the plugin must load immediately or doesn't need the
REFramework plugin API.

**Using the SDK from C++** (mirrors the Lua `sdk`):

```cpp
auto& api = API::get();
const auto tdb = api->tdb();
auto vm_context = api->get_vm_context();

const auto scene_manager      = api->get_native_singleton("via.SceneManager");
const auto scene_manager_type = tdb->find_type("via.SceneManager");
const auto get_main_view      = scene_manager_type->find_method("get_MainView");
const auto main_view = get_main_view->call<API::ManagedObject*>(vm_context, scene_manager);
if (main_view == nullptr) return;

// Call a method (two styles)
float size[3]{};
main_view->call("get_Size", &size, vm_context, main_view);     // direct call
auto result = main_view->invoke("get_Size", {});               // invoke form
```

Key C++ API types: `API` (singleton gateway), `API::ManagedObject`, `API::TypeDefinition`,
`API::Method`, plus the callback registration on `param->functions`. The headers in
`include/reframework/` are the authoritative reference.

**Examples in the repo:** `examples/example_plugin/` (full plugin with D3D11/D3D12 + ImGui
rendering) and `examples/weapon_stay_big_plugin/`. External: `reframework-d2d` (Direct2D
drawing for Lua).

---

## C# plugins (REFramework.NET)

A managed API for people who prefer C# and want typed, IDE-assisted access to game types. Per
the docs it runs ~3–7× faster than Lua single-threaded, and much faster multi-threaded.

**Prerequisites:** .NET 10 runtime, a REFramework **nightly** with .NET support, and
`csharp-api.zip` extracted into the game root.

**Two ways to ship code:**
- **Source (dev):** drop a `.cs` file in `reframework/plugins/source/` — it compiles
  automatically and **hot-reloads on save**.
- **Precompiled (distribution):** an x64 `.dll` in `reframework/plugins/managed/`
  (dependencies in `managed/dependencies/`).

**Minimal plugin:**

```csharp
using REFrameworkNET;
using REFrameworkNET.Attributes;

public class MyPlugin {
    [PluginEntryPoint]
    public static void Main() {
        API.LogInfo("Hello from C#!");
    }
}
```

**How it loads:** REF starts the .NET runtime → generates reference assemblies from the game's
TDB into `reframework/plugins/managed/generated/` (so each game type becomes a C# interface
with autocomplete) → loads dependencies → compiles `source/*.cs` → loads precompiled assemblies
→ runs `[PluginEntryPoint]` methods. On hot-reload/exit, `[PluginExitPoint]` methods run first.

**Key concepts:** `API` (logging, singletons, TDB), `ManagedObject` / `NativeObject`,
`TypeDefinition`, `IObject` (reflection-style access), `PreHookResult` (`Continue`/`Skip`).
Attributes: `[PluginEntryPoint]`, `[PluginExitPoint]`, `[MethodHook]`, `[Callback]`. Hooks run
on multiple threads — mind thread safety (the docs cover `LocalFrameGC()` and threading notes).

RE9 Additional Save Slots (`praydog/RE9AdditionalSaveSlots`) is a real-world C# plugin example.

---

## Choosing

- **Lua** — default. Fast to iterate (autorun + script reset), no build step, great for menus,
  overlays, tweaks, and most gameplay mods.
- **C#** — typed, autocompleted, much faster; still hot-reloadable from `source/`. Good when a
  mod grows large or Lua perf bites. Needs a .NET nightly.
- **C++** — maximum control and speed, custom rendering (D2D/D3D), anything the managed APIs
  can't reach. Full compile/deploy cycle; highest effort.

---

## Tools

- **Object Explorer** (REF menu → `DeveloperTools → ObjectExplorer`) — browse the live TDB:
  types, methods, fields, singletons (managed and native), and method disassembly. The primary
  way to find the exact names a script needs. Note: only TDB methods/fields are fully supported;
  reflection-only methods/properties aren't.
- **Chain Viewer** and **Behavior Tree / FSM Editor** — specialized viewers under the dev tools
  for inspecting render chains and AI logic.
- **`object_explorer:handle_address(addr)`** — from a script, open any object in the explorer
  (call inside `on_draw_ui`). Great for debugging what you've grabbed.
- **`re-engine-mcp`** (`github.com/praydog/re-engine-mcp`) — an MCP server that gives an AI
  agent live access to a running RE Engine game via REFramework. If it's available, use it to
  introspect real type/method/field names instead of guessing.
- **RE_RSZ** — recommended for editing `.scn`/resource files and inserting game objects into a
  scene without live runtime state.

## Debugging & logs

- Script errors at startup show a MessageBox; callback errors go to the log / ScriptRunner
  window (newer nightlies) / DebugView. `log.debug` output needs DebugView, a debugger, or the
  "Spawn Debug Console" in ScriptRunner.
- Bug reports: attach the whole `*_framework_log.txt` from the game folder, plus
  `reframework_crash.dmp` on a crash.
