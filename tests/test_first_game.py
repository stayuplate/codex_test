"""Tests for the Crystal Collector example game."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIRST_GAME_PATH = PROJECT_ROOT / "examples" / "first_game.py"


def _load_first_game_module():
    module_name = "examples.first_game"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, FIRST_GAME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_dense_crystal_layout_initializes():
    first_game = _load_first_game_module()
    scene = first_game.CrystalCollectorScene(width=3, height=3, crystals=8, energy=5, seed=123)

    # Ensure the board can be reset without triggering placement errors.
    scene.reset_board()

    assert len(scene.crystals) == 8
    assert len(scene.hazards) == 0
