# MiniLibX 2.2

This is the unmodified Ubuntu x86-64 wheel from `mlx-2.2.tgz`, supplied with
the assignment. Despite the `py3-none-any` filename, its `libmlx.so` is a
Linux x86-64 binary.

- File: `ubuntu/mlx-2.2-py3-none-any.whl`
- SHA-256: `7a1a44b50b6295f574522ba1a1e589632c6299d193dec57c951e8fdfb3337195`
- Original archive SHA-256: `17c7197e0a0bdc6aa2172c14c712f2d16832f19485ca6f7aa94ddeff46346783`
- Copyright: 2025 42 Born2code - Olivier CROUZET
- License: MIT; see [LICENSE.md](LICENSE.md).

`pyproject.toml` installs this wheel from its local path for the application.
The standalone `mazegen` package does not depend on it. The host needs XCB,
XCB keysyms, Vulkan, zlib, libbsd, a working graphics driver, and an X11 display.
Wayland desktops need XWayland.

## Finding the API

The wheel includes the Python wrapper and C API documentation.
After `make install`, run this from the repository root:

~~~sh
.venv/bin/python -c 'import inspect; from mlx import Mlx; print(inspect.getfile(Mlx))'
~~~

Use the directory containing the reported `mlx.py` as your starting point.
Its `.venv/lib/python3.x/site-packages/mlx/` location depends on the Python version.

| File | What to look for |
| --- | --- |
| `mlx.py` | Python method arguments, return values, and callback wiring |
| `docs/mlx.h` | C API declarations, constants, resources, and image formats |
| `docs/mlx.3`, `docs/mlx_new_window.3` | Context and window creation/destruction |
| `docs/mlx_new_image.3` | PNG loading, pixel memory, row size, formats, and display |
| `docs/mlx_loop.3` | Event loop, hooks, and loop exit |
| `docs/mlx_extra.3` | `mlx_sync` and synchronization commands |
| `test/simple_test.py` | A working example: window, callbacks, and event loop |

The `.3` files are C API manual pages. Read them in an editor or run
`man -l mlx_new_image.3` from their `docs` directory. Check `mlx.py` for the
Python calling convention: values returned through C output pointers are
returned in Python tuples. For example, `mlx_get_data_addr(image)` returns
`(memoryview, bits_per_pixel, size_line, pixel_format)`.
The last value is a pixel format, not an endianness flag.

In the app, `self.mlx` is the Python `Mlx` wrapper, while `self.mlx_ptr` is
the native context handle returned by `mlx_init()`. `self.win_ptr` is the
window handle; `self.frame_ptr` is the full-window image handle.
`self.size_line` is the number of bytes per image row, including padding.
`Window`, `draw()`, and `draw_tile()` belong to this project, not the MLX API.

## Type declarations

[typings/mlx/mlx.pyi](../../typings/mlx/mlx.pyi) describes only the API used by
the app. A Pyright-generated draft was checked and refined against the supplied
`mlx.py` and `docs/mlx.h`. At runtime, Python uses the original MLX package,
not this stub.

Handle-returning creation functions return `None` on failure. The callback
type variable `_State` connects the type of the registered `param` to the
callback's parameter type. The wrapper ignores callback return values.
The `mlx_hook` declaration covers only close event 33, which the app uses.
Extend the stub if another API or event is needed.

basedpyright uses its default `typings` directory. mypy reads the same stubs
through `mypy_path` in `pyproject.toml`. The stubs are not included in the
standalone `mazegen` wheel.
