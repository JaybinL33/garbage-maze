# pyright: reportAny=false, reportExplicitAny=false
"""Read a maze request, generate and save it, then open the MLX window."""

import sys
from collections.abc import Callable
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from random import Random
from typing import Any

from mazegen import ALL_WALLS, NORTH_BIT, WEST_BIT, Cell, MazeGenerator

_MOVES = {(0, -1): "N", (1, 0): "E", (0, 1): "S", (-1, 0): "W"}
_ASSETS = (
    "wall-0.png",
    "wall-1.png",
    "open-e.png",
    "open-s.png",
    "pattern.png",
    "path.png",
    "entry.png",
    "exit.png",
)


# --- Read once; generate and save again whenever R is pressed ---


def main(arguments: list[str]) -> int:
    """Read the configuration and connect generation, saving, and display.

    Args:
        arguments: Command-line arguments without the program name.

    Returns:
        Zero after normal window exit, or one after a reported error.
    """
    if len(arguments) != 1:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        return 1

    # Missing keys belong to configuration errors, not to later callbacks.
    try:
        config = parse_config(Path(arguments[0]).read_text(encoding="utf-8"))
        width = _parse_int(config["WIDTH"], "WIDTH")
        height = _parse_int(config["HEIGHT"], "HEIGHT")
        entry = _parse_cell(config["ENTRY"], "ENTRY")
        exit_cell = _parse_cell(config["EXIT"], "EXIT")
        perfect_text = config["PERFECT"]
        if perfect_text not in ("True", "False"):
            raise ValueError("PERFECT must be True or False")
        output = Path(config["OUTPUT_FILE"])
        seed = _parse_int(config["SEED"], "SEED") if "SEED" in config else None
    except KeyError as error:
        print(f"Error: missing config key {error.args[0]}", file=sys.stderr)
        return 1
    except MemoryError:
        print("Error: not enough memory", file=sys.stderr)
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}", file=sys.stderr)
        return 1

    try:
        rng = Random(seed)  # noqa: S311

        def generate_and_save() -> MazeGenerator:
            """Consume the session stream and return a maze after saving it.

            A failed save propagates without rewinding the random stream.
            """
            maze = MazeGenerator(
                width,
                height,
                entry,
                exit_cell,
                rng=rng,
                perfect=perfect_text == "True",
            )
            _ = output.write_text(encode_maze(maze), encoding="utf-8")
            return maze

        maze = generate_and_save()
        if not any(ALL_WALLS in row for row in maze.walls):
            print("Error: maze is too small for 42", file=sys.stderr)
        Window(maze, generate_and_save).run()
    except MemoryError:
        print("Error: not enough memory", file=sys.stderr)
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


# --- Convert values; main owns the file reads and writes ---


def _parse_int(value: str, key: str) -> int:
    """Convert a setting to an integer, naming invalid input.

    Args:
        value: Text from the configuration file.
        key: Setting name to include in an error message.

    Returns:
        The parsed integer.
    """
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{key} must be an integer") from error


def _parse_cell(value: str, key: str) -> Cell:
    """Parse a coordinate pair; the generator checks its bounds.

    Args:
        value: Coordinate text in x,y format.
        key: Setting name to include in an error message.

    Returns:
        The parsed (x, y) coordinates.
    """
    try:
        x, y = map(int, value.split(","))
    except ValueError as error:
        raise ValueError(
            f"{key} must contain two integers in x,y format"
        ) from error
    return x, y


def parse_config(text: str) -> dict[str, str]:
    """Read KEY=VALUE lines, ignoring blank lines and full-line comments.

    Args:
        text: Complete configuration contents, not a filename.

    Returns:
        Trimmed names and values; the last duplicate name wins.

    Raises:
        ValueError: A non-comment line lacks '=' or a key name.
    """
    config: dict[str, str] = {}
    for line_num, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"line {line_num}: missing '=' delimiter")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"line {line_num}: missing key")
        config[key] = value.strip()
    return config


def encode_maze(maze: MazeGenerator) -> str:
    """Return subject-format text for a completed maze.

    Args:
        maze: Generated walls, endpoints, and an entry-to-exit path.

    Returns:
        Hex wall rows, a blank line, endpoints, and NESW moves,
        with a final newline.
    """
    wall_rows = ("".join(f"{wall:X}" for wall in row) for row in maze.walls)
    endpoints = (f"{x},{y}" for x, y in (maze.entry, maze.exit))
    moves = "".join(
        _MOVES[next_x - x, next_y - y]
        for (x, y), (next_x, next_y) in pairwise(maze.path)
    )
    return "\n".join((*wall_rows, "", *endpoints, moves, ""))


# --- Own one MLX session and its images ---


class Window:
    """Keep the displayed maze, event callbacks, and native resources alive."""

    def __init__(
        self, initial: MazeGenerator, regenerate: Callable[[], MazeGenerator]
    ) -> None:
        """Open a fixed-size window, releasing partial resources on failure.

        Args:
            initial: Completed maze to display first.
            regenerate: Callback returning a newly generated, saved maze.
        """
        self.maze: MazeGenerator = initial
        self.regenerate: Callable[[], MazeGenerator] = regenerate
        self.path_visible: bool = True
        self.wall_color: int = 0
        self.background: bytes | None = None
        self.draw_error: Exception | None = None

        self.api: Any = import_module("mlx").Mlx()
        self.mlx: Any = self.api.mlx_init()
        if self.mlx is None:
            raise RuntimeError("mlx_init failed")

        self.window: int | None = None
        self.frame: int | None = None
        self.images: list[int] = []
        self.tiles: dict[str, list[tuple[int, int, bytes]]] = {}
        try:
            # Select the largest asset size that fits, including outer walls.
            columns, rows = len(initial.walls[0]), len(initial.walls)
            _, screen_width, screen_height = self.api.mlx_get_screen_size(
                self.mlx
            )
            for cell, wall_width in ((32, 4), (16, 2), (8, 1)):
                if (
                    columns * cell + wall_width <= screen_width - 64
                    and rows * cell + wall_width <= screen_height - 64
                ):
                    break
            else:
                raise ValueError("maze is too large to display on this screen")
            self.cell: int = cell
            window_width = columns * cell + wall_width
            window_height = rows * cell + wall_width
            self.window = self.api.mlx_new_window(
                self.mlx, window_width, window_height, "A-Maze-ing"
            )
            if self.window is None:
                raise RuntimeError("mlx_new_window failed")

            self._load_tiles()
            # One full-window image; pixels borrows its native memory.
            self.frame = self.api.mlx_new_image(
                self.mlx, window_width, window_height
            )
            if self.frame is None:
                raise RuntimeError("mlx_new_image failed")
            self.images.append(self.frame)
            self.pixels: memoryview
            self.stride: int
            self.pixels, _, self.stride, _ = self.api.mlx_get_data_addr(
                self.frame
            )
        except BaseException:
            # Cleanup also runs on interruption; the exception still escapes.
            self.close()
            raise

    def _load_tiles(self) -> None:
        """Load each PNG once and keep its visible row segments for drawing."""
        assets = Path(__file__).parent / "assets" / str(self.cell)
        for name in _ASSETS:
            image, width, height = self.api.mlx_png_file_to_image(
                self.mlx, str(assets / name)
            )
            if image is None:
                raise RuntimeError(f"cannot load asset {name}")
            self.images.append(image)
            pixels, _, stride, pixel_format = self.api.mlx_get_data_addr(image)
            alpha_offset = 3 if pixel_format == 0 else 0
            self.tiles[name] = []
            for y in range(height):
                row_start = y * stride
                row_end = row_start + width * 4
                row = bytes(pixels[row_start:row_end])
                # Our assets have one solid segment per row, or an empty row.
                alpha = row[alpha_offset::4]
                left = alpha.find(b"\xff")
                if left != -1:
                    first_byte = left * 4
                    last_byte = (alpha.rfind(b"\xff") + 1) * 4
                    self.tiles[name].append(
                        (left, y, row[first_byte:last_byte])
                    )

    # --- Callbacks may use the window until the event loop returns ---

    def run(self) -> None:
        """Register callbacks, draw once, and release resources after exit."""
        # Mlx retains the bound methods; this call keeps their owner alive.
        try:
            _ = self.api.mlx_key_hook(self.window, self.key, None)
            _ = self.api.mlx_expose_hook(self.window, self.redraw, None)
            _ = self.api.mlx_hook(
                self.window, 33, 0, self.api.mlx_loop_exit, self.mlx
            )
            self.draw()
            _ = self.api.mlx_loop(self.mlx)
            # Re-raise only after returning from the C callback boundary.
            if self.draw_error is not None:
                raise self.draw_error
        finally:
            self.close()

    def redraw(self, _state: object | None = None) -> None:
        """Stop the event loop if a callback cannot draw the maze.

        Args:
            _state: Unused MLX callback argument.
        """
        if self.draw_error is not None:
            return
        try:
            self.draw()
        except Exception as error:  # noqa: BLE001
            self.draw_error = error
            _ = self.api.mlx_loop_exit(self.mlx)

    def close(self) -> None:
        """Release images before their window, and the MLX context last."""
        if hasattr(self, "pixels"):
            self.pixels.release()
        for image in reversed(self.images):
            _ = self.api.mlx_destroy_image(self.mlx, image)
        if self.window is not None:
            _ = self.api.mlx_destroy_window(self.mlx, self.window)
        _ = self.api.mlx_release(self.mlx)

    # --- Build the background, add markers, then present the frame ---

    def draw(self, _state: object | None = None) -> None:
        """Reuse the maze background; rebuild overlays and present the frame.

        Args:
            _state: Unused MLX callback argument.
        """
        if self.background is None:
            wall_tile = f"wall-{self.wall_color}.png"
            for y, row in enumerate(self.maze.walls):
                for x, walls in enumerate(row):
                    pixel_x, pixel_y = x * self.cell, y * self.cell
                    self.draw_tile(wall_tile, pixel_x, pixel_y)
                    if walls == ALL_WALLS:
                        self.draw_tile("pattern.png", pixel_x, pixel_y)
                    # Join the tiles already drawn above and left.
                    if not walls & NORTH_BIT:
                        self.draw_tile(
                            "open-s.png", pixel_x, pixel_y - self.cell
                        )
                    if not walls & WEST_BIT:
                        self.draw_tile(
                            "open-e.png", pixel_x - self.cell, pixel_y
                        )
            # Do not cache markers: hiding the path must erase its old pixels.
            self.background = bytes(self.pixels)
        else:
            self.pixels[:] = self.background

        if self.path_visible:
            for x, y in self.maze.path:
                self.draw_tile("path.png", x * self.cell, y * self.cell)
        self.draw_tile(
            "entry.png",
            self.maze.entry[0] * self.cell,
            self.maze.entry[1] * self.cell,
        )
        self.draw_tile(
            "exit.png",
            self.maze.exit[0] * self.cell,
            self.maze.exit[1] * self.cell,
        )
        _ = self.api.mlx_put_image_to_window(
            self.mlx, self.window, self.frame, 0, 0
        )
        # Wait for the GPU to finish reading before an event edits this frame.
        _ = self.api.mlx_sync(
            self.mlx, self.api.SYNC_WIN_COMPLETED, self.window
        )

    def draw_tile(self, name: str, pixel_x: int, pixel_y: int) -> None:
        """Copy a tile's visible pixels into the frame, without presenting.

        Args:
            name: Loaded asset filename identifying the tile.
            pixel_x: Tile origin in frame pixels, measured from the left.
            pixel_y: Tile origin in frame pixels, measured from the top.
        """
        for tile_x, tile_y, pixels in self.tiles[name]:
            first_byte = (pixel_y + tile_y) * self.stride
            first_byte += (pixel_x + tile_x) * 4
            last_byte = first_byte + len(pixels)
            self.pixels[first_byte:last_byte] = pixels

    # --- Change state first; draw only after that change succeeds ---

    def key(self, keycode: int, _state: object) -> None:
        """Update state and redraw, keeping errors inside the C callback.

        Args:
            keycode: MLX key symbol for Escape, P, C, or R.
            _state: Unused MLX callback argument.
        """
        try:
            if keycode == 65_307:
                _ = self.api.mlx_loop_exit(self.mlx)
                return
            pressed = chr(keycode).lower() if keycode < 256 else ""
            if pressed == "p":
                self.path_visible = not self.path_visible
            elif pressed == "c":
                self.wall_color = 1 - self.wall_color
                self.background = None
            elif pressed == "r":
                self.maze = self.regenerate()
                self.background = None
            else:
                return
            self.redraw()
        except MemoryError:
            print("Error: not enough memory", file=sys.stderr)
        except Exception as error:  # noqa: BLE001
            print(f"Error: {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
