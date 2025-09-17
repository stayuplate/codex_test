"""Tests for the GameApp loop and scene replacement behavior."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from game_engine.app import GameApp
from game_engine.scene import Scene


class RecordingScene(Scene):
    """Base scene that records lifecycle events to a shared list."""

    def __init__(self, name, events):
        super().__init__(name=name)
        self._events = events

    def _record(self, message: str) -> None:
        self._events.append(message)

    def render(self) -> None:  # pragma: no cover - overridden where needed
        self._record(f"{self.name}.render")


class ReplacementScene(RecordingScene):
    """Scene that can replace itself during input or update."""

    def __init__(self, events, replace_during: str, new_scene_factory):
        super().__init__(name="old", events=events)
        self._replace_during = replace_during
        self._new_scene_factory = new_scene_factory

    def handle_input(self) -> bool:
        self._record("old.handle_input")
        if self._replace_during == "handle_input":
            self.app.replace_scene(self._new_scene_factory())
        return True

    def update(self, delta_time: float) -> None:
        self._record("old.update")
        if self._replace_during == "update":
            self.app.replace_scene(self._new_scene_factory())


class FinalScene(RecordingScene):
    """Scene pushed as a replacement that stops the app during update."""

    def handle_input(self) -> bool:
        self._record("new.handle_input")
        return True

    def update(self, delta_time: float) -> None:
        self._record("new.update")
        # Halt the loop so the test can make assertions.
        self.app.stop()

    def render(self) -> None:
        self._record("new.render")


def _make_final_scene(events):
    return FinalScene(name="new", events=events)


def test_scene_replacement_uses_latest_scene_for_updates_and_rendering():
    events = []
    app = GameApp()

    def new_scene_factory():
        return _make_final_scene(events)

    app.push_scene(ReplacementScene(events, "handle_input", new_scene_factory))
    app.run()

    # Initial render of the original scene is expected before the loop starts.
    assert events[0] == "old.render"
    assert "old.update" not in events
    assert events.count("new.update") == 1
    assert events[-1] == "new.render"


def test_scene_replacement_during_update_renders_new_scene_and_updates_next_frame():
    events = []
    app = GameApp()

    def new_scene_factory():
        return _make_final_scene(events)

    app.push_scene(ReplacementScene(events, "update", new_scene_factory))
    app.run()

    # The original scene should render once before being replaced.
    assert events[0] == "old.render"
    assert events.count("old.update") == 1
    # After replacement the new scene should render and eventually update/stop the app.
    assert events.count("new.render") >= 2
    assert events.count("new.update") == 1
    assert events[-1] == "new.render"


def test_game_app_respects_injected_output(capsys):
    messages = []

    app = GameApp(output=messages.append)

    class StoppingScene(Scene):
        def __init__(self):
            super().__init__(name="Stopper")
            self.render_calls = 0

        def render(self) -> None:
            self.render_calls += 1
            app_ref = getattr(self, "app", None)
            if app_ref is not None:
                app_ref.display(f"render-{self.render_calls}")
            else:  # pragma: no cover - fallback when no app is attached
                print(f"render-{self.render_calls}")

        def handle_input(self) -> bool:
            app_ref = getattr(self, "app", None)
            if app_ref is not None:
                app_ref.stop()
            return False

    app.push_scene(StoppingScene())
    app.run()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert messages[0] == "[DEBUG] GameApp.run() gestartet"
    assert "[DEBUG] Erste Szene vorhanden, render() wird aufgerufen" in messages
    assert messages.count("render-1") == 1
    assert messages.count("render-2") == 1
