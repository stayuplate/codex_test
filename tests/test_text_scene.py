"""Tests for TextScene input handling."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from game_engine.scene import TextScene


class FakeGameApp:
    """Stubbed GameApp collecting prompts and returning scripted commands."""

    def __init__(self, scripted_commands):
        self.scripted_commands = list(scripted_commands)
        self.prompts = []

    def get_input(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.scripted_commands:
            raise AssertionError("No scripted commands remaining for get_input")
        return self.scripted_commands.pop(0)


class RecordingTextScene(TextScene):
    """TextScene subclass that records commands passed to process_command."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_commands = []

    def get_display_text(self) -> str:
        return "Recording scene display"

    def process_command(self, command: str) -> None:
        self.processed_commands.append(command)


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


def test_text_scene_handle_input_with_fake_app():
    """TextScene handle_input uses GameApp stub and forwards command."""

    fake_app = FakeGameApp(scripted_commands=["look around"])
    scene = RecordingTextScene(name="CmdScene")
    scene.app = fake_app

    result = scene.handle_input()

    expected_prompt = f"{scene.color}{scene.prompt}\033[0m "
    assert fake_app.prompts == [expected_prompt]
    assert scene.processed_commands == ["look around"]
    assert result is True


def test_text_scene_render_uses_app_display(capsys):
    output_messages = []

    class DisplayingApp:
        def display(self, message: str) -> None:
            output_messages.append(message)

    scene = SimpleTextScene(name="RenderScene")
    scene.app = DisplayingApp()

    scene.render()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert output_messages[0] == "\033[2J\033[H"
    assert output_messages[-1] == f"{scene.color}{scene.get_display_text()}\033[0m"
    assert all(isinstance(message, str) for message in output_messages)
