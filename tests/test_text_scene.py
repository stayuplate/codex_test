"""Tests for TextScene input handling."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from game_engine.scene import TextScene


class SimpleTextScene(TextScene):
    """Minimal TextScene subclass without process_command."""

    def get_display_text(self) -> str:
        return "Simple display text"


def test_text_scene_handle_input_without_process_command(capsys):
    """TextScene without process_command should still proceed."""

    scene = SimpleTextScene(name="NoCmdScene")

    result = scene.handle_input()
    captured = capsys.readouterr().out

    assert "[DEBUG] process_command nicht vorhanden" in captured
    assert result is True
