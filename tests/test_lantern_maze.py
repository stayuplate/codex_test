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


class DummyApp:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def _open_move(scene, moves):
    for move in moves:
        dx, dy = move.delta
        candidate = (scene.player[0] + dx, scene.player[1] + dy)
        if scene._in_bounds(candidate) and not scene._is_wall(candidate):
            return move, candidate
    raise AssertionError("Expected at least one open neighboring tile")


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


def test_process_command_without_app_raises_runtime_error(lantern_maze_module):
    scene = lantern_maze_module.LanternMazeScene()

    with pytest.raises(RuntimeError, match=r"Scene is not attached to an application\."):
        scene.process_command("h")


def test_hint_without_app_raises_runtime_error(lantern_maze_module):
    scene = lantern_maze_module.LanternMazeScene()

    with pytest.raises(RuntimeError, match=r"Scene is not attached to an application\."):
        scene._hint()


def test_exploring_new_tile_awards_points(lantern_maze_module):
    scene = lantern_maze_module.LanternMazeScene(num_torches=0, num_traps=0, rng_seed=1)
    scene.app = DummyApp()
    move, target = _open_move(scene, lantern_maze_module.MOVES)
    scene._attempt_move(move)
    assert scene.player == target
    assert scene.score == scene.EXPLORATION_POINTS


def test_collecting_torch_grants_bonus_points(lantern_maze_module):
    scene = lantern_maze_module.LanternMazeScene(num_torches=1, num_traps=0, rng_seed=2)
    scene.app = DummyApp()
    move, target = _open_move(scene, lantern_maze_module.MOVES)
    scene._torches = {target}
    scene.total_torches = 1
    scene.score = 0
    scene._attempt_move(move)
    assert scene.player == target
    assert target not in scene._torches
    expected = scene.EXPLORATION_POINTS + scene.TORCH_POINTS
    assert scene.score == expected


def test_hint_guides_toward_torches_then_exit(lantern_maze_module):
    scene = lantern_maze_module.LanternMazeScene(num_torches=1, num_traps=0, rng_seed=4)
    scene.app = DummyApp()
    move, target = _open_move(scene, lantern_maze_module.MOVES)
    scene._torches = {target}
    scene.total_torches = 1
    scene._discovered = {scene.player}

    scene.process_command("h")
    direction = scene._direction_description((target[0] - scene.player[0], target[1] - scene.player[1]))
    assert direction in scene.message
    assert "light" in scene.message
    assert target in scene._discovered

    # Asking twice in the same turn should not change the message
    scene.process_command("h")
    assert scene.message == "The lantern's glow has nothing new to show you until you move."

    # After time passes and torches are gone, the hint should point to the exit
    scene._torches.clear()
    scene.turn_count += 1
    scene.process_command("h")
    assert "exit" in scene.message
    assert scene.exit in scene._discovered
