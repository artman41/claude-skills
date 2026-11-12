# REFramework Hooking (`sdk.hook`)

Hooking intercepts every call the game makes to a method, so you can inspect/modify arguments,
skip the original, or replace the return value. It's powerful and the most bug-prone part of
the API because **arguments and return values are raw `void*`** — none of the usual
auto-conversion applies. Read this fully before writing or editing a hook.

## Signatures

```lua
sdk.hook(method_definition, pre_function, post_function, ignore_jmp=false)
sdk.hook_vtable(object, method_definition, pre_function, post_function)
```

- `method_definition` is an `REMethodDefinition` from `type:get_method("Name")` (pass a full
  prototype to select an overload).
- `sdk.hook` is **global** — it fires for every instance/caller of that method.
- `sdk.hook_vtable` hooks a **single object** and only works on **virtual** methods.
- `ignore_jmp` skips following the first jump in the function; occasionally needed for thin
  wrapper functions. Some native wrapper methods can't be hooked at all.

## The pre function: `function(args) ... end`

`args` is a table of raw `void*`. The layout depends on the method kind:

| Index | Instance method | Static method |
| --- | --- | --- |
| `args[1]` | thread context | thread context |
| `args[2]` | `this` (the object) | first parameter |
| `args[3]` | first parameter | second parameter |
| ... | ... | ... |

Some native functions instead put the object at `args[1]` and the rest at `args[2]` — verify
in Object Explorer if a hook misbehaves.

**Converting args** (nothing is auto-converted):
```lua
local this   = sdk.to_managed_object(args[2])   -- object pointer -> REManagedObject
local n      = sdk.to_int64(args[3])            -- integer-ish arg
local flag   = sdk.to_int64(args[3]) & 1 == 1   -- boolean (mask low bit)
local f      = sdk.to_float(args[3])            -- float arg

-- A ValueType argument (e.g. a struct passed by value): read its fields directly
local pos_t  = sdk.find_type_definition("via.Position")
local x      = sdk.get_native_field(args[3], pos_t, "x")
```

`args` entries are **modifiable** — assign a converted `void*` (via `sdk.to_ptr` /
`sdk.float_to_ptr`) back into `args[n]` to change what the original function receives.

**Return value — control whether the original runs:**
- Return nothing or `sdk.PreHookResult.CALL_ORIGINAL` → the original method runs (default).
- Return `sdk.PreHookResult.SKIP_ORIGINAL` → the original is skipped.

## The post function: `function(retval) ... end`

- `retval` is the raw `void*` return of the original. Return a replacement to change it, or
  return `retval` unchanged.
- **Convert custom return values**: `return sdk.to_ptr(x)` (objects/ints/bools) or
  `return sdk.float_to_ptr(x)` (floats).
- The post function **still runs even when the pre returned `SKIP_ORIGINAL`** — in that case
  `retval` is not valid, so guard against it if your logic reads it.

## Canonical template

```lua
local function pre(args)
    -- args[1]=thread_context, args[2]="this", args[3..]=params (instance method)
    -- Convert before using: sdk.to_managed_object(args[2]), sdk.to_int64(args[3]), ...
    -- return sdk.PreHookResult.SKIP_ORIGINAL   -- to block the original
end

local function post(retval)
    return retval   -- or sdk.to_ptr(custom) / sdk.float_to_ptr(custom)
end

sdk.hook(sdk.find_type_definition("via.Scene"):get_method("get_TimeScale"), pre, post)
```

Example — double the time scale by rewriting the return:
```lua
local scene_t = sdk.find_type_definition("via.Scene")
sdk.hook(
    scene_t:get_method("get_TimeScale"),
    function(args) end,
    function(retval) return sdk.float_to_ptr(2.0) end
)
```

## Passing data from pre to post: `thread.get_hook_storage()`

Don't use globals to carry state between pre and post — the hook is no longer guaranteed to be
locked across both callbacks, which can deadlock, and globals break under recursion. Use the
per-hook ephemeral storage, which is recursion-safe and cleared at the end of post:

```lua
local pawn_t = sdk.find_type_definition("app.Pawn")
sdk.hook(
    pawn_t:get_method("updateMove"),
    function(args)
        thread.get_hook_storage()["this"] = sdk.to_managed_object(args[2])
    end,
    function(retval)
        local this = thread.get_hook_storage()["this"]
        log.info(this:get_type_definition():get_full_name())
        return retval
    end
)
```

## ByRef / out-parameters (`T**`)

REFramework does **not** auto-support ByRef parameters (a `T**`, typically an out-param). You
must dereference manually, and **out values can only be read in the post hook** (the game fills
them during the call). The pattern:

1. In **pre**, stash the raw arg pointer in hook storage.
2. In **post**, wrap the pointer as a `System.UInt64` with `sdk.to_valuetype`, read its
   `mValue` field to dereference, then convert the result (e.g. `sdk.to_managed_object`) and
   `add_ref()` it if you keep it.

```lua
sdk.hook(
    some_method,
    function(args)
        thread.get_hook_storage()["out_ptr"] = args[3]  -- the T** out-param
    end,
    function(retval)
        local out_ptr = thread.get_hook_storage()["out_ptr"]
        local as_u64  = sdk.to_valuetype(out_ptr, "System.UInt64")
        local deref   = as_u64:get_field("mValue")       -- dereference T** -> T*
        local obj     = sdk.to_managed_object(deref)
        if obj ~= nil then obj:add_ref() end
        return retval
    end
)
```

## Hooking gotchas

- **`get_`/`set_` accessors are dangerous to hook.** They're tiny, so the compiler often folds
  several unrelated accessors into one shared function. Your hook can then fire for calls you
  didn't intend and crash the game if you alter control flow. Before hooking one: check its
  disassembly in Object Explorer; verify the object type in `args` is what you expect; and
  leave arguments and control flow untouched until you're certain it's the right call.
- **Performance.** Hooks on hot methods (per-entity `update`, anything per-frame) add overhead
  proportional to what you do inside them. Mitigate by: doing minimal work in the callback,
  caching type/method/field lookups outside, spreading work across frames, or moving heavy
  logic to a native plugin.
- **Don't over-hook.** If you only need to read state periodically, poll from `re.on_frame`
  instead of hooking a high-frequency method.
- **Convert everything.** The #1 hook bug is treating a raw `void*` arg as if it were already a
  Lua value. It isn't.
