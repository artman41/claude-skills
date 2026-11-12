# REFramework Lua Types & Conversion Rules

The object types you get back from the API, and how values convert between Lua and the engine.

## Contents
- [Lua ↔ engine conversion rules](#conversion-rules) — read this first
- [`REManagedObject`](#remanagedobject) — the core game object
- [`RETypeDefinition`](#retypedefinition) — type metadata
- [`REMethodDefinition`](#remethoddefinition)
- [`REField`](#refield)
- [`SystemArray`](#systemarray) — engine arrays (mind the iteration trap)
- [`ValueType`](#valuetype) — structs / unknown value types
- [Math types](#math-types) — `Vector2f/3f/4f`, `Matrix4x4f`, `Quaternion`
- [`RETransform`](#retransform)

---

## Conversion rules

Applies to `obj:call`, `obj:get_field`, `sdk.call_native_func`, `sdk.get_native_field`, and
`REMethodDefinition:call`. **Return values are auto-converted** to native Lua types:

| Engine type | Becomes |
| --- | --- |
| `System.String` | Lua `string` |
| `System.Boolean` | Lua `boolean` |
| `System.SByte/Byte/Int16/UInt16/Int32/UInt32/Int64/UInt64` | Lua `number` |
| `System.Single` / `System.Double` | Lua `number` |
| `via.vec2` / `via.vec3` / `via.vec4` | `Vector2f` / `Vector3f` / `Vector4f` |
| `via.mat4` | `Matrix4x4f` |
| `via.quat` | `Quaternion` |
| other managed objects | `REManagedObject` |
| arrays | `SystemArray` |
| other value types | `ValueType` |

**Arguments** convert the other direction automatically for normal calls: pass Lua numbers,
strings, booleans, `Vector3f`, `REManagedObject`, etc. directly.

**The exception is inside `sdk.hook`**, where arguments and the return value are raw `void*`
that you must convert yourself (`sdk.to_managed_object`, `sdk.to_int64`, `sdk.float_to_ptr`,
`sdk.get_native_field` for ValueType fields). See `hooking.md`.

---

## REManagedObject

A live, GC-managed engine object. The workhorse type.

### Common methods
- `self:call(method_name, args...) -> any` — invoke a method (wraps `sdk.call_object_func`).
  For overloads, pass the full prototype: `self:call("foo(System.String, System.Single)", a, b)`.
  Valid names are under **TDB Methods** in Object Explorer.
- `self:get_type_definition() -> RETypeDefinition`.
- `self:get_field(name) -> any` / `self:set_field(name, value)`.
- `self:get_address() -> number`.
- `self:get_reference_count() -> number`.
- `self:get_object_size() -> number` — size in bytes.
- `self:deserialize_native(data, objects)` — experimental; deserialize RSZ bytes into `self`
  (native `via` types only).

### Sugar (indexers)
- `self.foo` → the field (or `REMethodDefinition`) named `foo`.
- `self:foo(a, b)` → calls method `foo` (use `self:call` with a prototype for overloads).
- `self.foo = bar` → assigns a field **and handles refcounting** of old/new values. Don't mix
  with `force_release`/`add_ref_permanent`.
- `self[i]` → `get_Item(i)` if it exists; `self[i] = v` → `set_Item(i, v)`.
- `a == b` → true if both wrap the same object.

### Reference counting
Lua auto-`add_ref()`s on reference and `release()`s on GC. You only manage refcounts manually
for objects the engine hands you fresh — arrays and `sdk.create_instance()` results — if you
keep them around.

- `self:add_ref()` — increment refcount.
- `self:add_ref_permanent()` — increment without REF managing it (survives Lua-state teardown).
- `self:release()` — decrement; destroys at 0. Lua-managed objects only.
- `self:force_release()` — decrement on **any** object; **can crash the game**. Last resort.

### Raw memory (dangerous — prefer `get_field`/`call`)
- Reads: `read_byte/read_short/read_dword/read_qword/read_float/read_double(offset)`.
- Writes: `write_byte/write_short/write_dword/write_qword/write_float/write_double(offset, value)`.

---

## RETypeDefinition

Type metadata, from `sdk.find_type_definition` or `obj:get_type_definition`.

### Names / hierarchy
- `get_full_name()` (namespace + name), `get_name()`, `get_namespace()`.
- `get_parent_type() -> RETypeDefinition`.
- `get_runtime_type() -> System.Type` (C# `typeof` equivalent).
- `get_types_inheriting_from_this() -> RETypeDefinition[]`.
- `is_a(name_or_typedef) -> bool` — self or an ancestor matches.

### Members
- `get_method(name) -> REMethodDefinition` — pass a prototype to pick an overload:
  `t:get_method("Bar(System.Int32, System.Single)")`. Use with `sdk.hook`.
- `get_methods() -> REMethodDefinition[]` (excludes likely stubs/nulls).
- `get_field(name) -> REField`, `get_fields() -> REField[]`.
- `get_generic_argument_types()`, `get_generic_type_definition()`.

### Classification / size
- `is_value_type()` (note: `via.vec3` is a value type without inheriting `System.ValueType`),
  `is_enum()`, `is_array()`, `is_by_ref()`, `is_pointer()`, `is_primitive()`,
  `is_generic_type()`, `is_generic_type_definition()`.
- `get_size()` — full object size (e.g. `0x14` for `System.Int32`).
- `get_valuetype_size()` — value size (e.g. `4` for `System.Int32`).
- `get_fqn_hash()` (FNV-1a of full name), `get_crc_hash()`.

### Creation
- `create_instance() -> REManagedObject`.
- `create_instance_gc_safe()` — like above but registered as a Lua global so it isn't GC'd.

`a == b` is true when both refer to the same type.

---

## REMethodDefinition

From `RETypeDefinition:get_method(...)`. Pass this to `sdk.hook`.
- `get_name()`.
- `call(obj, args...) -> any` — same as `obj:call(args...)`; also callable as
  `method(obj, args...)`. Pass `nil` as `obj` for static methods.
- `get_return_type() -> RETypeDefinition`.
- `get_declaring_type() -> RETypeDefinition`.
- `get_function() -> void*` — pointer to the real function in memory.
- `get_num_params()`, `get_param_types() -> RETypeDefinition[]`,
  `get_param_names() -> string[]`.
- `is_static() -> bool`.

```lua
local app_t = sdk.find_type_definition("via.Application")
local get_uptime = app_t:get_method("get_UpTimeSecond")
local seconds = get_uptime:call(nil)   -- static method
```

---

## REField

From `RETypeDefinition:get_field(...)` / `get_fields()`.
- `get_name()`.
- `get_type() -> RETypeDefinition`.
- `get_declaring_type() -> RETypeDefinition`.
- `get_offset_from_base()`, `get_offset_from_fieldptr()`.
- `get_flags()`, `is_static()`, `is_literal()`.
- `get_data(obj) -> any` — the field's value for `obj`. `obj` may be `nil` (static field), an
  `REManagedObject`, or a `void*` to a managed object / ValueType.

```lua
-- Build an enum table from a type's static fields
local t = sdk.find_type_definition("via.hid.GamePadButton")
local enum = {}
for _, field in ipairs(t:get_fields()) do
    if field:is_static() then
        enum[field:get_name()] = field:get_data(nil)
    end
end
```

---

## SystemArray

An engine array. **Iteration is the classic trap.**

- `self:get_elements() -> table` — all elements as a real Lua array of `REManagedObject`
  (elements are boxed objects, not raw ValueTypes).
- `self:get_element(index) -> REManagedObject`.
- `self:get_size() -> number`.
- `self[i]` → `get_element(i)` (0-based, bounds-checked: out-of-range or non-integer → `nil`).
- `self[i] = managed_obj` → sets element `i` (the value must be an `REManagedObject`).

**Do not `ipairs` a raw `SystemArray`** — it skips element 0 and runs past the end. Either:

```lua
for _, v in ipairs(arr:get_elements()) do ... end   -- preferred: real Lua table
-- or
for _, v in pairs(arr) do ... end                   -- pairs is safe on the array itself
```

---

## ValueType

"Container for unknown ValueTypes" — structs the API doesn't have a dedicated wrapper for.
- `ValueType.new(type_definition) -> ValueType`.
- `self:call(name, args...)`, `self:get_field(name)`, `self:set_field(name, value)`.
  **`set_field` is local only** — it changes the ValueType in Lua, not the game. You must pass
  the modified ValueType into a method/field setter that consumes it for the change to take effect.
- `self:address()` and `self:get_address()` (both exist and are equivalent),
  `self:get_type_definition()`.
- Properties: `self.type`, `self.data` (raw `std::vector<uint8_t>`).
- Dangerous raw accessors (use only if necessary):
  `read_byte/short/dword/qword/float/double(offset)` and the `write_*(offset, value)` pair.

Note: `via.vec3`/`mat4`/`quat` are auto-converted to the math types below, so you rarely touch
`ValueType` for those — it's for less common structs.

---

## Math types

### Vector2f / Vector3f / Vector4f
Constructors: `Vector2f.new(x, y)`, `Vector3f.new(x, y, z)`, `Vector4f.new(x, y, z, w)`.
Fields: `.x`, `.y` (all), `.z` (3f/4f), `.w` (4f).

Methods (all): `dot(other)`, `length()`, `normalize()` (in place, returns nothing),
`normalized()` (returns a copy), `clone()`.
Vector3f/4f add: `cross(other)`, `reflect(normal)`, `refract(normal, eta)`, `lerp(other, t)`,
`to_quat()` / `to_mat()` (treat self as the forward vector; built with a left-handed lookAt),
plus conversions `to_vec2/to_vec3/to_vec4` as applicable. `Vector2f` has only the common
methods plus `to_vec3`/`to_vec4` — no `cross`/`reflect`/`refract`/`lerp`. `Vector4f:cross`
ignores `w` and returns a `Vector3f`.

Operators: `v + v`, `v - v`, `v * scalar` **only**. There is no `==` metamethod (two vectors
with equal components are not `==`; compare components yourself) and no division or
vector×vector multiply.

### Matrix4x4f
`Matrix4x4f` is a GLM `mat4` (**column-major**). Constructors: `Matrix4x4f.new()`,
`Matrix4x4f.new(col1, col2, col3, col4)` (four `Vector4f` columns), or
`Matrix4x4f.new(16 floats)`. Static: `Matrix4x4f.identity()` (use this when you want identity —
don't assume `.new()` is identity).

Methods: `to_quat()`, `inverse()` (returns a copy), `invert()` (in place), `interpolate(other, t)`,
`matrix_rotation()` (extract the rotation matrix), `clone()`.
Operators: `mat * mat`, `mat * Vector4f`.

**Indexing — `mat[i]` returns column `i` as a `Vector4f`.** `i` must be an integer in `[0, 4)`
(anything else yields `nil`). Because the matrix is column-major, `mat[3]` is the **translation
column**, so `mat[3].x/.y/.z` is the position. `mat[i] = some_vec4` replaces column `i`.
```lua
local mat = transform:call("get_WorldMatrix")   -- via.mat4 -> Matrix4x4f
local pos = mat[3]                               -- Vector4f: the translation column
transform:set_position(mat[3])                   -- set_position takes a Vector4f
transform:set_rotation(mat:to_quat())
```

### Quaternion
Usually produced by the engine (`get_rotation`, `Matrix4x4f:to_quat`, `Vector3f:to_quat`), but
you can also construct one.

Constructors:
- `Quaternion.new()` — identity-ish default.
- `Quaternion.new(w, x, y, z)` — **GLM scalar-first order: `w` comes first**, not last. This
  trips people up; prefer the engine-provided quaternions or `:to_quat()` when you can.
- `Quaternion.new(euler_vec3)` — from Euler angles (radians).
- Static `Quaternion.identity()`.

Fields: `.x`, `.y`, `.z`, `.w`.
Methods: `clone()`, `to_mat4() -> Matrix4x4f`, `to_euler() -> Vector3f`, `inverse()` (copy),
`invert()` (in place), `normalize()` (in place), `normalized()` (copy), `slerp(other, t)`,
`dot(other)`, `length()`, `conjugate()`.
Operators: `q * q` (compose rotations), `q * Vector3f -> Vector3f` and
`q * Vector4f -> Vector4f` (rotate a vector), `q[i]` read (`i` in `[0,4)` → float),
`q[i] = float` write.

---

## RETransform

A game object's transform component (from `game_object:call("get_Transform")`). The methods
below are **native REFramework bindings** — call them directly (`transform:get_position()`).
Anything not in this list (e.g. `get_Joints`, `get_WorldMatrix`, `get_GameObject`, `get_Child`,
`get_Next`) is an engine reflection method reached through `:call("...")` instead.

- `get_position() -> Vector4f` / `set_position(position, no_dirty?)` — world position.
  `no_dirty=true` skips marking the transform and parents dirty; needed when the scene is
  locked, or parent transforms can get stuck.
- `get_rotation() -> Quaternion` / `set_rotation(rotation)` — world rotation.
- `calculate_base_transform(joint) -> Matrix4x4f` — reference (T-pose) transform for a joint,
  local to the transform origin.
- `calculate_tpose_pos_world(joint, depth=1) -> Vector4f` — world T-pose position for a joint
  (`depth` = levels from root).
- `apply_joints_tpose(joints_table, additional_parents)` — apply T-pose to a table of REJoint.
- `hook_update(fn)` — register a per-frame callback for **this specific transform** without a
  global update hook.

Joints are commonly reached with `transform:call("get_Joints")` (a `SystemArray`) and each
joint's `get_WorldMatrix` / `set_Position` / `set_Rotation`. See `recipes.md` for the gizmo
example that walks joints.
