(This page is a work-in-progress! Much more to come. If you run into build problems and figure out the solution please contribute to this page!)

# Core MicroPython

## `STATIC` 

To fix this, replace all usages of `STATIC` with `static` in your code (likely a User C Module).

See https://github.com/micropython/micropython/pull/13763 for details.

## `mp_generic_unary_op` missing

This function was removed in v1.21. If you have a module that defined a type that used it, then likely all you need to do is remove the `unary_op` slot from your type.

See https://github.com/micropython/micropython/pull/10348 for more details. This PR identified that there were a bunch of places that used `mp_generic_unary_op` to enable the default implementation of the hash operator on types. Instead it was easier to enable hashing by default for all type, and just disable it for types that shouldn't get it

## DEFINE_CONST_OBJ_TYPE

If you see errors involving the `DEFINE_CONST_OBJ_TYPE` macro, or anything to do with the definition of `mp_obj_type_t` then see [#8813](https://github.com/micropython/micropython/pull/8813). This PR changed the way object types are defined, in order to save significant amounts of ROM. The `mp_obj_type_t` struct previously always stored 12 pointers to various functions that customise the type's behavior. However this meant that all types, even very simple ones, always used 12 words of ROM. Now the type only uses as much ROM as it has slots defined. Unfortunately the way this is represented can't be easily done using plain C initialisers, so the implementation of this is hidden in a new macro.

You will need to update any definition of types in your custom modules from:

```c
const mp_obj_type_t mp_type_foo = {
    { &mp_type_type },
    .name = MP_QSTR_foo,
    .print = array_print,
    .make_new = array_make_new,
    ...
    locals_dict, (mp_obj_dict_t *) &mp_obj_array_locals_dict,
};
```

to

```c
MP_DEFINE_CONST_OBJ_TYPE(
    mp_type_foo,
    MP_QSTR_foo,
    MP_TYPE_FLAG_NONE,
    print, array_print,
    make_new, array_make_new,
    ...
    locals_dict, &mp_obj_array_locals_dict
);
```

Note that a trailing comma after the last argument is not allowed, and the cast is no longer required on the locals dict.

The first three arguments (symbol name, type name QSTR, flags) are required, and then a variable number of "slots" can be specified. If you don't have any flags (most types), then use `MP_TYPE_FLAG_NONE`.

If your type was previously static, i.e.

```c
STATIC const mp_obj_type_t mp_type_foo = {
```

then you can add `STATIC` in front of the `MP_DEFINE_CONST_OBJ_TYPE`.

```c
STATIC MP_DEFINE_CONST_OBJ_TYPE(
    mp_type_foo,
    ...
```

In most cases this change should be mechanical, pass the type, name, and flags as the first three arguments, then just replace all remaining `.a = b,` with `a, b,`. The two exceptions are `buffer` and `getiter` / `iternext`, see the next two sections.

If your code need to access properties on a give type, e.g. `mp_type_foo.make_new` then it needs to be updated to use the accessor macros.

```c
MP_OBJ_TYPE_HAS_SLOT(type, slot) # True if type->slot is non-NULL
MP_OBJ_TYPE_GET_SLOT(type, slot) # equivalent to type->slot (but you must know that the slot is set)
MP_OBJ_TYPE_GET_SLOT_OR_NULL(type, slot) # marginally less efficient but will return NULL if the slot is not set
```

If your code needs to access fields on `mp_obj_type_t` (this should be relatively rare), then you will now need to do so via the helper macros. Code that previously did:

```c
if (type->call) {}  // See if field is set.
mp_call_fun_t f = type->call;  // Access field.
type->call = f;  // Set field.
```

will need to be changed to:

```c
if (MP_OBJ_TYPE_HAS_SLOT(type, call)) {}
mp_call_fun_t f = MP_OBJ_TYPE_GET_SLOT(type, call); // Or MP_OBJ_TYPE_GET_SLOT_OR_NULL(type, call) if you do not know whether the slot is set.
MP_OBJ_TYPE_SET_SLOT(type, call, f, index);
```

In the last case, you need to know the index (likely this is being used in a situation where you're initialising a new mp_obj_type_t instance so you can generate the slots sequentially).

## buffer

The definition for a type with a buffer slot has been simplified and no longer requires a nested struct.

As part of updating to use `MP_DEFINE_CONST_OBJ_TYPE`, change

```c
const mp_obj_type_t mp_type_foo = {
...
    .buffer_p = { .get_buffer = mp_obj_str_get_buffer },
...
}
```

to

```c
MP_DEFINE_CONST_OBJ_TYPE(
...
    buffer, mp_obj_str_get_buffer,
...
);
```

## getiter/iternext

If you see errors about `getiter` and/or `iternext` then also see #8813.

In order to save space, the `getiter` and `iternext` slots were merged on `mp_obj_type_t` into a single new slot `iter`. The following changes need to be made to your object type definitions.

- If you previously had just a `getiter`, then change `getiter` to `iter` and set the `MP_TYPE_FLAG_ITER_IS_GETITER`.
- If you had `getiter` as `mp_identity_getiter` and a custom `iternext`, then pass your iternext function to the `iter` slot, and set the `MP_TYPE_FLAG_ITER_IS_ITERNEXT` flag.
- If you had `getiter` as `mp_identity_getiter` and `mp_stream_unbuffered_iter` as `iternext`, then just set the `MP_TYPE_FLAG_ITER_IS_STREAM` and do not set the `iter` slot.
- If you had both a custom getiter and iternext, then you need to pass an instance of a `mp_getiter_iternext_custom_t` to the `iter` slot and set the `MP_TYPE_FLAG_ITER_IS_CUSTOM` flag. See [moduasyncio.c](https://github.com/micropython/micropython/blob/master/extmod/moduasyncio.c).

# Dependencies

## Submodules

If you see compile errors about NimBLE, mbedtls, etc, then it's likely that the required submodules are not available. Run

```
make BOARD=... submodules
```

to automatically initialise required submodules.

When the error is not solved and your build target is `esp32` then proof via `idf.py --version` that you are working with a supported esp-idf version (see https://github.com/micropython/micropython/blob/master/ports/esp32/README.md#setting-up-esp-idf-and-the-build-environment)

