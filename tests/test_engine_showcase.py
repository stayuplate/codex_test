"""Tests for the Engine Showcase demo."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_PATH = PROJECT_ROOT / "examples" / "engine_showcase.py"


def _load_showcase_module():
    module_name = "examples.engine_showcase"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, SHOWCASE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_showcase_update_generates_ticks():
    showcase_module = _load_showcase_module()
    scene = showcase_module.ShowcaseScene(use_raw_input=False)

    scene.on_enter()
    # Run the update long enough to accumulate multiple spinner frames.
    scene.update(2.0)

    assert scene.tick_count > 0
    assert scene.boost_level == 1


def test_showcase_history_limits_entries():
    showcase_module = _load_showcase_module()
    scene = showcase_module.ShowcaseScene(use_raw_input=False)

    for index in range(10):
        scene.record_action(f"entry {index}")

    assert len(scene.history) == scene.HISTORY_SIZE
    assert scene.history[0].endswith("entry 5")
