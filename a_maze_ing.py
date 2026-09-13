# pyright: reportAny=false, reportExplicitAny=false
"""Read a maze request, generate and save it, then open the MLX window."""

import sys
from collections.abc import Callable
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from random import Random
from typing import Any

from mazegen import ALL_WALLS, NORTH_BIT, WEST_BIT, MazeGenerator

_CELL = 16
_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT", "SEED"}
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
        Zero after the window loop returns; one if startup fails.
    """
    if len(arguments) != 1:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        return 1

    # Read and convert settings now, so callbacks never interpret config text.
    try:
        config = parse_config(Path(arguments[0]).read_text(encoding="utf-8"))
        width, height = int(config["WIDTH"]), int(config["HEIGHT"])
        x, y = map(int, config["ENTRY"].split(","))
        entry_cell = (x, y)
        x, y = map(int, config["EXIT"].split(","))
        exit_cell = (x, y)
        perfect_text = config["PERFECT"]
        if perfect_text not in ("True", "False"):
            raise ValueError("PERFECT must be True or False")
        perfect = perfect_text == "True"
        output = Path(config["OUTPUT_FILE"])
        seed = int(config["SEED"]) if "SEED" in config else None
    except KeyError as error:
        print(f"Error: missing config key {error.args[0]}", file=sys.stderr)
        return 1
    except Exception as error:  # noqa: BLE001
        message = str(error) or type(error).__name__
        print(f"Error: {arguments[0]}: {message}", file=sys.stderr)
        return 1

    try:
        # Seed once per session; R continues the stream instead of resetting.
        rng = Random(seed)  # noqa: S311

        def generate_and_save() -> MazeGenerator:
            """Create the next maze in the session's random sequence."""
            maze = MazeGenerator(
                width,
                height,
                entry_cell,
                exit_cell,
                rng=rng,
                perfect=perfect,
            )
            # A failed save must not replace the maze displayed by Window.
            _ = output.write_text(encode_maze(maze), encoding="utf-8")
            return maze

        maze = generate_and_save()
        # Only glyph cells remain fully walled after generation.
        if not any(ALL_WALLS in row for row in maze.walls):
            print("Error: maze is too small for 42", file=sys.stderr)
        return Window(maze, generate_and_save).run()
    except Exception as error:  # noqa: BLE001
        message = str(error) or type(error).__name__
        print(f"Error: {message}", file=sys.stderr)
        return 1


# --- Convert values; main owns the file reads and writes ---


def parse_config(text: str) -> dict[str, str]:
    """Read KEY=VALUE lines, ignoring blank lines and full-line comments.

    Check syntax and known names here; main checks required keys and values.

    Args:
        text: Complete configuration contents, not a filename.

    Returns:
        Trimmed names and values; the last duplicate name wins.

    Raises:
        ValueError: A non-comment line lacks '=' or has an unsupported key.
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
        if key not in _KEYS:
            raise ValueError(f"line {line_num}: invalid key {key!r}")
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
    wall_rows = ["".join(f"{wall:X}" for wall in row) for row in maze.walls]
    moves = "".join(
        _MOVES[next_x - x, next_y - y]
        for (x, y), (next_x, next_y) in pairwise(maze.path)
    )
    return "\n".join(
        [
            *wall_rows,
            "",
            f"{maze.entry[0]},{maze.entry[1]}",
            f"{maze.exit[0]},{maze.exit[1]}",
            moves,
            "",
        ]
    )


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

        # Defer native GUI loading until the window is opened.
        self.api: Any = import_module("mlx").Mlx()
        self.mlx: Any = self.api.mlx_init()
        if self.mlx is None:
            raise RuntimeError("mlx_init failed")

        self.window: int | None = None
        self.frame: int | None = None
        # Python GC does not destroy MLX images; keep handles for close().
        self.images: list[int] = []
        self.tiles: dict[str, list[tuple[int, int, bytes]]] = {}
        try:
            # Include the 2px outer wall beyond the last row and column.
            win_w = len(initial.walls[0]) * _CELL + 2
            win_h = len(initial.walls) * _CELL + 2
            self.window = self.api.mlx_new_window(
                self.mlx, win_w, win_h, "A-Maze-ing"
            )
            if self.window is None:
                raise RuntimeError("mlx_new_window failed")

            self._load_tiles()
            # One full-window image; pixels borrows its native memory.
            self.frame = self.api.mlx_new_image(self.mlx, win_w, win_h)
            if self.frame is None:
                raise RuntimeError("mlx_new_image failed")
            self.images.append(self.frame)
            self.pixels: memoryview
            self.stride: int
            self.pixels, _, self.stride, _ = self.api.mlx_get_data_addr(
                self.frame
            )
        except BaseException:
            # Release partial resources even on KeyboardInterrupt.
            self.close()
            raise

    def _load_tiles(self) -> None:
        """Load each PNG once and keep its visible row segments for drawing."""
        assets = Path(__file__).parent / "assets" / "16"
        for name in _ASSETS:
            image, width, height = self.api.mlx_png_file_to_image(
                self.mlx, str(assets / name)
            )
            if image is None:
                raise RuntimeError(f"cannot load asset {name}")
            self.images.append(image)
            pixels, _, stride, pixel_format = self.api.mlx_get_data_addr(image)
            # MLX uses 4-byte pixels: BGRA for format 0, ARGB for format 1.
            alpha_offset = 3 if pixel_format == 0 else 0
            self.tiles[name] = []
            for y in range(height):
                # stride includes row padding; keep only the actual pixels.
                row_start = y * stride
                row_end = row_start + width * 4
                row = bytes(pixels[row_start:row_end])
                # Asset rows have alpha 0/255 and at most one opaque run.
                alpha = row[alpha_offset::4]
                left = alpha.find(b"\xff")
                if left == -1:
                    continue
                byte_start = left * 4
                byte_end = (alpha.rfind(b"\xff") + 1) * 4
                self.tiles[name].append((left, y, row[byte_start:byte_end]))

    # --- Callbacks may use the window until the event loop returns ---

    def run(self) -> int:
        """Draw the initial frame, then handle events until exit.

        Returns:
            Zero when the loop ends; one if initial drawing fails.
        """
        # The wrapper retains callback objects, including their bound self.
        try:
            _ = self.api.mlx_key_hook(self.window, self.key, None)
            _ = self.api.mlx_expose_hook(self.window, self.draw, None)
            # A close request ends the loop; cleanup waits for its return.
            _ = self.api.mlx_hook(
                self.window, 33, 0, self.api.mlx_loop_exit, self.mlx
            )
            if not self.draw():
                return 1
            _ = self.api.mlx_loop(self.mlx)
            return 0
        finally:
            self.close()

    def close(self) -> None:
        """Release images before their window, and the MLX context last."""
        # Invalidate the borrowed view before freeing its native image memory.
        if hasattr(self, "pixels"):
            self.pixels.release()
        for image in reversed(self.images):
            _ = self.api.mlx_destroy_image(self.mlx, image)
        if self.window is not None:
            _ = self.api.mlx_destroy_window(self.mlx, self.window)
        _ = self.api.mlx_release(self.mlx)

    # --- Build the background, add markers, then present the frame ---

    def draw(self, _state: object | None = None) -> bool:
        """Reuse the maze background; rebuild overlays and present the frame.

        Args:
            _state: Unused MLX callback argument.

        Returns:
            True after presentation completes; False on a reported error.
        """
        try:
            # Build or restore the maze layer; key() invalidates it on changes.
            if self.background is None:
                wall_tile = f"wall-{self.wall_color}.png"
                for y, row in enumerate(self.maze.walls):
                    for x, walls in enumerate(row):
                        px, py = x * _CELL, y * _CELL
                        self.draw_tile(wall_tile, px, py)
                        if walls == ALL_WALLS:
                            self.draw_tile("pattern.png", px, py)
                        # Open tiles start at the cell above or to the left.
                        # Paint both cells before drawing their opening.
                        if not walls & NORTH_BIT:
                            self.draw_tile("open-s.png", px, py - _CELL)
                        if not walls & WEST_BIT:
                            self.draw_tile("open-e.png", px - _CELL, py)
                # Cache no markers, so hiding the path erases its old pixels.
                self.background = bytes(self.pixels)
            else:
                self.pixels[:] = self.background

            # Draw the path first so entry and exit markers stay on top.
            if self.path_visible:
                for x, y in self.maze.path:
                    self.draw_tile("path.png", x * _CELL, y * _CELL)
            x, y = self.maze.entry
            self.draw_tile("entry.png", x * _CELL, y * _CELL)
            x, y = self.maze.exit
            self.draw_tile("exit.png", x * _CELL, y * _CELL)
            _ = self.api.mlx_put_image_to_window(
                self.mlx, self.window, self.frame, 0, 0
            )
            # Finish the GPU read before an event edits this frame.
            _ = self.api.mlx_sync(
                self.mlx, self.api.SYNC_WIN_COMPLETED, self.window
            )
        except Exception as error:  # noqa: BLE001
            # Report here: exceptions cannot propagate through a C callback.
            message = str(error) or type(error).__name__
            print(f"Error: {message}", file=sys.stderr)
            _ = self.api.mlx_loop_exit(self.mlx)
            return False
        return True

    def draw_tile(self, name: str, pixel_x: int, pixel_y: int) -> None:
        """Copy a tile's visible pixels into the frame, without presenting.

        Args:
            name: Loaded asset filename identifying the tile.
            pixel_x: Tile origin in frame pixels, measured from the left.
            pixel_y: Tile origin in frame pixels, measured from the top.
        """
        for tile_x, tile_y, segment in self.tiles[name]:
            offset = (pixel_y + tile_y) * self.stride + (pixel_x + tile_x) * 4
            end = offset + len(segment)
            self.pixels[offset:end] = segment

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
        except Exception as error:  # noqa: BLE001
            message = str(error) or type(error).__name__
            print(f"Error: {message}", file=sys.stderr)
            return
        # draw() reports its own errors; keep it outside this handler.
        _ = self.draw()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
