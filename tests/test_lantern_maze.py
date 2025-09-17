import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def lantern_maze_module():
    module_name = "tests.examples.lantern_maze"
    module_path = Path(__file__).resolve().parents[1] / "examples" / "lantern_maze.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load lantern_maze module for testing.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(module_name, None)


@pytest.mark.parametrize(
    "blueprint",
    [
        ("###", "#E#", "###"),
        ("###", "#P#", "###"),
    ],
    ids=["missing-start", "missing-exit"],
)
def test_missing_required_tiles_raise_value_error(monkeypatch, lantern_maze_module, blueprint):
    monkeypatch.setattr(lantern_maze_module, "MAP_BLUEPRINT", blueprint)
    with pytest.raises(ValueError, match=r"Map must define both a start \(P\) and exit \(E\) tile\."):
        lantern_maze_module.LanternMazeScene()
