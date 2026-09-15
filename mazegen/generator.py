"""Build a maze, then keep its walls, endpoints, and shortest path."""

import random
from collections import deque
from typing import TypeAlias

Coord: TypeAlias = tuple[int, int]

# Coordinates are (x, y). During generation, cell = y * width + x.
NORTH_BIT, EAST_BIT, SOUTH_BIT, WEST_BIT = 1, 2, 4, 8
ALL_WALLS = 15
_MIN_LOOPS = 2
# dx, dy, wall here, the same shared wall seen from the neighbour.
_DIRECTIONS = (
    (0, -1, NORTH_BIT, SOUTH_BIT),
    (1, 0, EAST_BIT, WEST_BIT),
    (0, 1, SOUTH_BIT, NORTH_BIT),
    (-1, 0, WEST_BIT, EAST_BIT),
)
_PATTERN_42 = (
    "#...###",
    "#.....#",
    "###.###",
    "..#.#..",
    "..#.###",
)
_PATTERN_WIDTH = len(_PATTERN_42[0])
_PATTERN_HEIGHT = len(_PATTERN_42)


class MazeGenerator:
    """Generate once; expose the completed maze without files or graphics."""

    walls: tuple[bytes, ...]
    entry: Coord
    exit: Coord
    path: tuple[Coord, ...]

    def __init__(  # noqa: C901
        self,
        width: int,
        height: int,
        entry_cell: Coord,
        exit_cell: Coord,
        *,
        rng: random.Random,
        perfect: bool = False,
    ) -> None:
        """Connect the maze, optionally add loops, and find a shortest path.

        Args:
            width: Positive number of columns.
            height: Positive number of rows.
            entry_cell: In-bounds (x, y) start, outside the closed 42 cells.
            exit_cell: Different in-bounds (x, y) end, outside those cells.
            rng: Caller-owned random stream to consume, not reset or retain.
            perfect: True keeps a tree; False adds loops at dead ends first.

        Attributes:
            walls: Wall codes as walls[y][x]; N/E/S/W bits are 1/2/4/8.
            entry: Start coordinates.
            exit: End coordinates.
            path: A shortest route, including both endpoints.

        Example:
            rng = random.Random(42)
            maze = MazeGenerator(20, 15, (0, 0), (19, 14), rng=rng)
        """
        # Validate the request before allocating the working grid.
        if width <= 0 or height <= 0:
            raise ValueError("WIDTH and HEIGHT must be positive")
        for name, (x, y) in (("ENTRY", entry_cell), ("EXIT", exit_cell)):
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(f"{name} {(x, y)} is outside the maze")
        if entry_cell == exit_cell:
            raise ValueError("ENTRY and EXIT must be different")

        start = entry_cell[1] * width + entry_cell[0]
        end = exit_cell[1] * width + exit_cell[0]
        pattern = _pattern_cells(width, height, perfect=perfect)
        if start in pattern or end in pattern:
            raise ValueError(
                "ENTRY and EXIT must not overlap the centred 42 pattern"
            )
        # A full grid's loop capacity is edges - cells + 1, before the glyph.
        if not perfect and (width - 1) * (height - 1) < _MIN_LOOPS:
            raise ValueError(
                f"PERFECT=False needs {_MIN_LOOPS} independent loops"
            )

        # In allowed_mask, 1 permits opening; in walls, 1 means a wall exists.
        # Start with every direction, then exclude the border and the 42.
        cell_count = width * height
        allowed_mask = bytearray([ALL_WALLS]) * cell_count
        for x in range(width):
            allowed_mask[x] &= ~NORTH_BIT
            allowed_mask[(height - 1) * width + x] &= ~SOUTH_BIT
        for y in range(height):
            allowed_mask[y * width] &= ~WEST_BIT
            allowed_mask[(y + 1) * width - 1] &= ~EAST_BIT
        # Exclude directions into the glyph, then all directions out of it.
        # Border exclusions keep the neighbour index within the array.
        for cell in pattern:
            for dx, dy, wall_bit, back_bit in _DIRECTIONS:
                if allowed_mask[cell] & wall_bit:
                    allowed_mask[cell + dx + dy * width] &= ~back_bit
            allowed_mask[cell] = 0

        # Carve a connected tree; non-perfect mode adds passages, never walls.
        walls = bytearray([ALL_WALLS]) * cell_count
        _carve_dfs(width, walls, allowed_mask, start, rng)
        if not perfect:
            _braid(width, walls, allowed_mask)

        # Solve on the flat grid, then keep only the completed result.
        path = _solve_bfs(width, walls, start, end)
        rows: list[bytes] = []
        for row_start in range(0, cell_count, width):
            row_end = row_start + width
            rows.append(bytes(walls[row_start:row_end]))
        self.walls = tuple(rows)
        self.entry = entry_cell
        self.exit = exit_cell
        self.path = path


# --- Place the closed 42 cells ---


def _pattern_cells(width: int, height: int, *, perfect: bool) -> set[int]:
    """Place the fixed glyph without disconnecting the surrounding grid.

    Args:
        width: Number of columns.
        height: Number of rows.
        perfect: Whether a closed corner is permitted for the tightest fit.

    Returns:
        Closed glyph cells as y * width + x, or an empty set if too small.
    """
    if width < _PATTERN_WIDTH + 1 or height < _PATTERN_HEIGHT + 1:
        return set()
    # The tightest fit blocks a corner; non-perfect mazes keep corners open.
    if not perfect and (width, height) == (
        _PATTERN_WIDTH + 1,
        _PATTERN_HEIGHT + 1,
    ):
        return set()
    # Floor division chooses the upper-left placement when centring ties.
    left = (width - _PATTERN_WIDTH) // 2
    top = (height - _PATTERN_HEIGHT) // 2
    return {
        (top + y) * width + left + x
        for y, row in enumerate(_PATTERN_42)
        for x, mark in enumerate(row)
        if mark == "#"
    }


# --- Open passages within the allowed directions ---


def _carve_dfs(
    width: int,
    walls: bytearray,
    allowed_mask: bytearray,
    start: int,
    rng: random.Random,
) -> None:
    """Open a spanning tree in walls in place, consuming rng.

    Args:
        width: Row stride for the flat cell arrays.
        walls: Initially closed wall bits, modified on both sides of a move.
        allowed_mask: Read-only opening permissions, excluding border/glyph.
        start: Flat cell index at which DFS begins.
        rng: Random stream used to choose unvisited neighbours.
    """
    dirs = tuple(
        (dx + dy * width, wall_bit, back_bit)
        for dx, dy, wall_bit, back_bit in _DIRECTIONS
    )
    stack = [start]
    while stack:
        cell = stack[-1]
        # An arrival opens a wall, marking the cell visited without a set.
        # Glyph cells also stay closed, but allowed_mask excludes entry.
        unvisited = [
            (cell + offset, wall_bit, back_bit)
            for offset, wall_bit, back_bit in dirs
            if allowed_mask[cell] & wall_bit
            and walls[cell + offset] == ALL_WALLS
        ]
        if not unvisited:
            _ = stack.pop()
            continue
        neighbor, wall_bit, back_bit = rng.choice(unvisited)
        walls[cell] &= ~wall_bit
        walls[neighbor] &= ~back_bit
        stack.append(neighbor)


def _braid(
    width: int,
    walls: bytearray,
    allowed_mask: bytearray,
) -> None:
    """Add passages at dead ends, then ensure at least two loops.

    A leaf trapped by the glyph or border may have no second permitted exit.
    Such pockets remain; the analyzer excludes them from real dead ends.

    Args:
        width: Row stride for the flat cell arrays.
        walls: Connected DFS tree; open walls without closing existing paths.
        allowed_mask: Read-only opening permissions shared with DFS.
    """
    dirs = tuple(
        (dx + dy * width, wall_bit, back_bit)
        for dx, dy, wall_bit, back_bit in _DIRECTIONS
    )
    loops_added = 0

    # Pass 1: give each removable dead end another exit.
    # Opening only adds exits, so no earlier cell needs another pass.
    # DFS + row-major + N/E/S/W is what excludes fully open 3x3 areas here.
    # Changing the tree algorithm or either order needs a new argument.
    for cell in range(len(walls)):
        if walls[cell].bit_count() != 3:
            continue
        choices = allowed_mask[cell] & walls[cell]
        for offset, wall_bit, back_bit in dirs:
            if choices & wall_bit:
                walls[cell] &= ~wall_bit
                walls[cell + offset] &= ~back_bit
                loops_added += 1
                break

    # Pass 2: add any missing loops; each extra passage adds one.
    # Stop at two total loops: a fully open 3x3 needs four (12 - 9 + 1).
    if loops_added >= _MIN_LOOPS:
        return
    for cell, mask in enumerate(allowed_mask):
        choices = mask & walls[cell]
        # East and south cover each shared wall once.
        for offset, wall_bit, back_bit in dirs[1:3]:
            if choices & wall_bit:
                walls[cell] &= ~wall_bit
                walls[cell + offset] &= ~back_bit
                loops_added += 1
                if loops_added == _MIN_LOOPS:
                    return


# --- Find the solution in the completed maze ---


def _solve_bfs(
    width: int, walls: bytearray, start: int, end: int
) -> tuple[Coord, ...]:
    """Find a shortest path by BFS without changing the maze.

    Args:
        width: Row stride for the flat wall array.
        walls: Connected maze with closed outer borders.
        start: Entry's flat cell index.
        end: Exit's flat cell index.

    Returns:
        (x, y) coordinates in entry-to-exit order, including both endpoints.
    """
    # parent[cell] records where BFS first reached it; -1 means undiscovered.
    parent = [-1] * len(walls)
    parent[start] = start  # Prevent neighbours from queuing the entry again.
    queue = deque([start])
    dirs = tuple(
        (dx + dy * width, wall_bit) for dx, dy, wall_bit, _ in _DIRECTIONS
    )
    # FIFO explores by move count; first discovery gives a shortest path.
    while parent[end] < 0:
        cell = queue.popleft()
        cell_walls = walls[cell]
        for offset, wall_bit in dirs:
            neighbor = cell + offset
            # Closed border walls prevent reading an out-of-bounds parent.
            if not cell_walls & wall_bit and parent[neighbor] < 0:
                parent[neighbor] = cell
                queue.append(neighbor)

    # Reconstruct the route.
    route = [end]
    while route[-1] != start:
        route.append(parent[route[-1]])
    return tuple((cell % width, cell // width) for cell in reversed(route))
