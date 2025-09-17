# AGENTS

Welcome to the lightweight **Game Engine** repository. This file explains how contributions should be structured and which conventions to follow when modifying the codebase.

## Repository layout

- `src/game_engine/`
  - Core engine modules. `GameApp` drives the main loop, `Scene`/`TextScene` provide lifecycle hooks, and `GameObject` is the base entity abstraction.
  - Changes here should preserve backwards compatibility for existing scenes in `examples/` and expectations encoded in `tests/`.
- `examples/`
  - Playable demos that double as living documentation. Scripts are meant to be executable via `python examples/<name>.py` and should remain terminal-friendly.
- `tests/`
  - Pytest-based regression tests that exercise the engine core and example scenes.

## General coding guidelines

- Target **Python 3.8+** and keep the code compatible with CPython. Avoid third-party dependencies unless absolutely required.
- Prefer explicit type hints and enable postponed evaluation via `from __future__ import annotations` for new modules placed in `src/` or `examples/`.
- Keep modules importable without side effects. Guard runtime/demo logic with `if __name__ == "__main__":`.
- Favour small, well-documented methods. Reuse existing hooks (`on_enter`, `handle_input`, `update`, `render`) rather than introducing bespoke control flow.
- When adding new data containers, consider `dataclasses.dataclass` for readability.
- Use `f"..."` strings for formatting and keep debug output optional (ideally routed through `GameApp.display`).

## Testing & quality checks

Before submitting changes you must run:

1. `python -m pytest`
   - Ensures all unit tests under `tests/` continue to pass. Add/adjust tests whenever you change behaviour.

Add new tests alongside features or bug fixes. Keep fixtures self-contained—tests import engine modules by adding `src/` to `sys.path` for you.

## Examples directory

- Preserve the top-level logic that injects `src/` into `sys.path` so the demos keep working without installation.
- Expose new demos via a `main()` function plus an argument parser in the style used by `first_game.py` and `lantern_maze.py`.
- Stick to terminal-friendly rendering (ANSI colours are fine) and avoid heavy dependencies.

## Working on core engine modules

- Maintain the scene stack invariants: `push_scene` must call `on_enter`, `pop_scene` must call `on_exit`, and `replace_scene` should act atomically.
- Any new scene subclass should set `self.app` when attached and clear it on exit; reuse the helper logic already in `GameApp`.
- Keep the game loop responsive: avoid long blocking calls; prefer cooperative patterns where scenes decide whether to skip updates by returning `False` from `handle_input`.

## Documentation

- Update `README.md` or example docstrings when you add user-facing functionality.
- Inline documentation should focus on explaining *why* decisions were made, especially around scene lifecycle and input handling.

Following these guidelines will help keep the engine consistent, tested, and easy to extend. Happy hacking!
