UV ?= uv

.PHONY: install run debug clean lint lint-strict package

install:
	$(UV) sync --locked

run:
	$(UV) run --locked python a_maze_ing.py config.txt

debug:
	$(UV) run --locked python -m pdb a_maze_ing.py config.txt

clean:
	rm -rf __pycache__ mazegen/__pycache__ .mypy_cache build mazegen.egg-info

lint:
	$(UV) run --locked flake8 .
	$(UV) run --locked mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) run --locked flake8 .
	$(UV) run --locked mypy . --strict

package:
	$(UV) build --no-sources --wheel --out-dir .
