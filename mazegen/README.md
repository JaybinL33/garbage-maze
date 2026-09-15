# mazegen

A maze generator for Python 3.10 or later, using only the standard library.
It does not read configuration files, write files, or depend on MLX.
Calling `MazeGenerator(...)` generates the maze and finds a shortest path.

The [Blue Oak Model License 1.0.0](https://blueoakcouncil.org/license/1.0.0)
allows reuse, modification, and redistribution. When redistributing, provide
the license text or its official link. It does not require publishing source
code or marking changes. It includes a patent grant within the contributors'
authority, not a guarantee against third-party patent claims.
The full license is included in the wheel.

## Install and use

Run this in a Python virtual environment, from the directory containing the wheel:

~~~sh
python3 -m pip install ./mazegen-1.0.0-py3-none-any.whl
~~~

~~~python
from random import Random

from mazegen import EAST_BIT, MazeGenerator

rng = Random(42)
maze = MazeGenerator(25, 17, (0, 0), (24, 16), rng=rng, perfect=False)

print(maze.walls[0][0])
print(maze.entry, maze.exit)
print(maze.path)
print(bool(maze.walls[0][0] & EAST_BIT))
~~~

## Parameters

| Name | Meaning |
| --- | --- |
| `width`, `height` | Positive integers: columns and rows |
| `entry_cell`, `exit_cell` | Distinct entry and exit coordinates, `(x, y)` |
| `rng` | Required keyword argument: a caller-owned `random.Random` instance |
| `perfect` | Keyword argument, default `False`; `True` generates a maze without loops |

A fresh `Random(42)` reproduces the same maze for the same dimensions, endpoints,
mode, code, and Python environment. Reusing the `rng` object continues its random
stream. Use `Random()` to start without a fixed seed. Separate generations are
not guaranteed to produce different mazes.

Endpoints must be within bounds and must not overlap the closed `42` cells.
Default mode requires at least two independent loops, so it rejects sizes where
`(width - 1) * (height - 1) < 2`. Invalid dimensions or coordinates raise
`ValueError`.

## Reading the result

- `walls: tuple[bytes, ...]`: wall codes, accessed as `walls[y][x]`.
- `entry`, `exit`: the endpoint coordinates, `(x, y)`.
- `path: tuple[tuple[int, int], ...]`: a shortest path including both endpoints.

Wall bits are `NORTH_BIT=1`, `EAST_BIT=2`, `SOUTH_BIT=4`, and `WEST_BIT=8`.
**A set bit means a wall; a cleared bit means a passage.**
`ALL_WALLS=15` identifies a fully closed `42` cell in the generated result.
These constants and the `Coord` type alias can also be imported from `mazegen`.
`Coord` means `tuple[int, int]`: an `(x, y)` coordinate, not the flat integer
cell index used during generation.

Wall rows and the path are immutable values, but assigning new values to the
object's attributes is not prevented. Treat the result as read-only and create
another instance when you need a new maze.

## Algorithm and limits

Iterative randomized DFS connects all walkable cells. With `perfect=True`,
the result remains a tree with exactly one path between any two walkable cells.
Default mode opens walls at dead ends, then adds more passages if needed to
reach two independent loops. BFS finds a shortest path through the result.

Preventing fully open `3x3` areas depends on DFS together with the current
row-major braiding pass and north/east/south/west choice order. Recheck this
property before changing either algorithm or order. Small pockets forced by
the `42` pattern remain: zero `real dead-ends` in the supplied analyzer does
not mean every cell has at least two passages. Two independent loops also do
not guarantee two independent paths between every pair of cells.

The fixed `7x5` pattern starts at
`((width - 7) // 2, (height - 5) // 2)`.
Preserving connectivity needs at least `8x6`. At exactly `8x6`, the pattern
occupies a corner and is placed only in perfect mode. Default mode needs at
least `8x7` or `9x6`. When it does not fit, generation proceeds without it.
The library does not print warnings; the caller handles any user-facing message.
