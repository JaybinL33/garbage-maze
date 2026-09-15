"""Types for the MLX 2.2 API used by this application."""

from collections.abc import Callable
from typing import Literal, TypeVar

_State = TypeVar("_State")

class Mlx:
    SYNC_WIN_COMPLETED: int

    def __init__(self) -> None: ...
    def mlx_init(self) -> int | None: ...
    def mlx_release(self, mlx_ptr: int) -> int: ...
    def mlx_new_window(
        self, mlx_ptr: int, width: int, height: int, title: str
    ) -> int | None: ...
    def mlx_destroy_window(self, mlx_ptr: int, win_ptr: int) -> int: ...
    def mlx_new_image(
        self, mlx_ptr: int, width: int, height: int
    ) -> int | None: ...
    def mlx_png_file_to_image(
        self, mlx_ptr: int, filename: str
    ) -> tuple[int | None, int, int]: ...
    def mlx_get_data_addr(
        self, img_ptr: int
    ) -> tuple[memoryview, int, int, int]: ...
    def mlx_put_image_to_window(
        self, mlx_ptr: int, win_ptr: int, img_ptr: int, x: int, y: int
    ) -> int: ...
    def mlx_destroy_image(self, mlx_ptr: int, img_ptr: int) -> int: ...

    # The wrapper passes param back unchanged and ignores callback returns.
    def mlx_key_hook(
        self,
        win_ptr: int,
        callback: Callable[[int, _State], object],
        param: _State,
    ) -> int: ...
    def mlx_expose_hook(
        self,
        win_ptr: int,
        callback: Callable[[_State], object],
        param: _State,
    ) -> int: ...

    # Only the close event is used; other events have different signatures.
    def mlx_hook(
        self,
        win_ptr: int,
        x_event: Literal[33],
        x_mask: int,
        callback: Callable[[_State], object],
        param: _State,
    ) -> int: ...
    def mlx_loop(self, mlx_ptr: int) -> int: ...
    def mlx_loop_exit(self, mlx_ptr: int) -> int: ...
    def mlx_sync(self, mlx_ptr: int, cmd: int, img_or_win_ptr: int) -> int: ...
