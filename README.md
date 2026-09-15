*This project has been created as part of the 42 curriculum by jungblee, hyunlee.*

# A-Maze-ing

## Description

A Python program that reads a configuration file, generates a maze, saves its
walls and shortest path, and displays it in a MiniLibX window. The `mazegen`
package can also be used on its own, without graphics or file handling.

- `PERFECT=False`: the default mode; adds loops and reduces dead ends.
- `PERFECT=True`: generates a maze with no loops and exactly one path between
  any two walkable cells.

## Instructions

### Install and run

You need Ubuntu x86-64, Python 3.10 or later, `make`, and [uv][uv-install].
The window requires an X11 display and a working Vulkan driver. Use XWayland
on a Wayland desktop. Required system libraries are XCB, XCB keysyms, Vulkan,
zlib, and libbsd.

From the repository root:

~~~sh
make install
make run
~~~

`make install` prepares `.venv` and the Python dependencies using `uv.lock`.
MLX comes from the bundled Ubuntu wheel. Install system libraries and graphics
drivers separately.

To run the program directly or use another configuration file:

~~~sh
source .venv/bin/activate
python3 a_maze_ing.py config.txt
~~~

Replace `config.txt` with your file path. It is the only command-line argument.
The program writes the maze to `OUTPUT_FILE`, then opens the window.
An existing output file is overwritten.

### Controls and development commands

| Key | Action |
| --- | --- |
| `R` | Generate, save, and display a new maze |
| `P` | Show or hide the shortest path |
| `C` | Switch wall colours |
| `Escape` / close button | Quit |

The entry is cyan, the exit is coral, the path is amber, and the `42` pattern
is purple. Cells use a fixed 16-pixel spacing, so large mazes may extend beyond
the screen.

| Command | Action |
| --- | --- |
| `make debug` | Run with Python's `pdb` debugger |
| `make lint` | Run flake8 and mypy with the subject's required options |
| `make lint-strict` | Run flake8 and mypy in strict mode |
| `make package` | Rebuild the submission wheel from source in the repository root |
| `make clean` | Remove Python/mypy caches and intermediate build files |

`make clean` keeps the virtual environment, output maze, and submission wheel.

## Configuration

The supplied [config.txt](config.txt) contains:

~~~ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
~~~

| Key | Required | Value |
| --- | --- | --- |
| `WIDTH`, `HEIGHT` | Yes | Positive integers: columns and rows |
| `ENTRY`, `EXIT` | Yes | Distinct entry and exit coordinates, `x,y` |
| `OUTPUT_FILE` | Yes | Output file path |
| `PERFECT` | Yes | Exactly `True` or `False` |
| `SEED` | No | An integer for reproducible generation |

Coordinates start at `(0, 0)` in the top-left corner. x increases to the right;
y increases downwards. Entry and exit must be inside the maze and outside the
closed `42` cells. Default mode rejects sizes where
`(WIDTH - 1) * (HEIGHT - 1) < 2`, since they cannot contain two independent loops.
If the maze is too small for the pattern, it is generated without `42` and an
error message is printed.

Write one `KEY=VALUE` pair per line. Blank lines and lines starting with `#`
are ignored. Surrounding whitespace is allowed; key names are case-sensitive.
Unknown keys are rejected, and the last value wins for duplicate keys.
Inline comments are not supported. Relative paths are resolved from the
directory where the program is run.

Without `SEED`, each run starts a new random stream. With a seed, the same
configuration, code, and Python environment reproduce the generation sequence.
`R` continues that stream rather than resetting it. An empty or non-integer
seed is an error.

## Generation algorithm

**Randomized depth-first search (DFS)** connects unvisited neighbours.
When there is nowhere left to go, it backtracks to try another neighbour.
An explicit stack avoids Python's recursion-depth limit.

The result is a tree connecting all walkable cells. Perfect mode stops there.
Default mode opens extra walls at dead ends and ensures at least two
independent loops. **Breadth-first search (BFS)** then finds a shortest path
from entry to exit.

We chose DFS because it needs only the grid and a stack, without a full edge
list or a separate disjoint-set structure. Generation and pathfinding use
time and memory proportional to the number of cells. `mazegen/` owns generation;
`a_maze_ing.py` handles configuration, files, and display.

## Output format

Each cell is stored as one hexadecimal digit. The wall bit values are north
`1`, east `2`, south `4`, and west `8`: **1 means closed; 0 means open**.
For example, `A` means the east and west walls are closed.

The file contains one line per maze row, a blank line, then the entry, exit,
and shortest path on three separate lines. The path uses `N`, `E`, `S`, and
`W`. Every line ends with a newline. A two-cell perfect maze looks like this:

~~~text
D7

0,0
1,0
E
~~~

## Reusing the generator

The root-level `mazegen-1.0.0-py3-none-any.whl` contains the generator and its
documentation. It does not need MLX or image assets. In another project's
virtual environment, copy the wheel into your current directory and install it:

~~~sh
python3 -m pip install ./mazegen-1.0.0-py3-none-any.whl
~~~

~~~python
from random import Random

from mazegen import MazeGenerator

rng = Random(42)
maze = MazeGenerator(25, 17, (0, 0), (24, 16), rng=rng, perfect=False)

print(maze.walls[0][0])
print(maze.entry, maze.exit)
print(maze.path)
~~~

The first four arguments are width, height, entry coordinates, and exit
coordinates. `rng` is required; `perfect` defaults to `False`. Passing the same
`rng` to another generation continues the random stream.

`walls[y][x]` is the wall code described above. `path` is a tuple of `(x, y)`
coordinates, including both endpoints. See the [package guide](mazegen/README.md)
for the full API.

## Team and project management

- `hyunlee`: maze generation, shortest-path solving, and the generator API.
- `jungblee`: configuration, file output, MLX display, and packaging.

Our initial plan was to agree on the wall and path formats, implement the
generator and app separately, then integrate them. After comparing algorithms
and display designs, we simplified the submission around one generator package
and one application file.

The small interface of wall codes and coordinates made it possible to test
generation and rendering separately. We could improve by clarifying requirements
earlier: seed behaviour and the `42` placement rules for small mazes both needed
later review.

We use Jujutsu/Git for version control, uv for environments, and setuptools for
packaging. Checks use flake8, mypy, separate tests, and the supplied maze analyzer.

## Resources

- [A-Maze-ing v2.3 subject][subject] and its accompanying `maze_analyzer.py`.
- [MIT DFS lecture][dfs] and [MIT BFS lecture][bfs]: graph traversal.
- [Python random][random]: seeds and random number generators.
- [MiniLibX documentation locations and Python API guide](third_party/mlx/README.md).
- [uv project guide][uv-project] and [Python packaging guide][packaging].

AI was used for interpreting requirements, comparing algorithms, drafting and
refactoring `mazegen` and `a_maze_ing.py`, writing tests, checking packaging,
and writing documentation.

## License

Project code uses the [Blue Oak Model License 1.0.0](LICENSE.md).
Bundled MiniLibX retains its [separate MIT license](third_party/mlx/LICENSE.md).

[subject]: https://cdn.intra.42.fr/pdf/pdf/224851/en.subject.pdf
[uv-install]: https://docs.astral.sh/uv/getting-started/installation/
[uv-project]: https://docs.astral.sh/uv/guides/projects/
[packaging]: https://packaging.python.org/en/latest/tutorials/packaging-projects/
[random]: https://docs.python.org/3/library/random.html
[dfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-14-depth-first-search-dfs-topological-sort/
[bfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-13-breadth-first-search-bfs/
