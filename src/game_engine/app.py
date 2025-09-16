"""Main application loop for the lightweight game engine."""

from __future__ import annotations

import sys
import time
from typing import Callable, List, Optional

from .scene import Scene

InputProvider = Callable[[str], str]
OutputHandler = Callable[[str], None]
ClearFunction = Callable[[], None]


class GameApp:
    """Minimal application runner that manages a stack of scenes."""

    def __init__(
        self,
        *,
        target_fps: float = 0,
        input_provider: Optional[InputProvider] = None,
        output: Optional[OutputHandler] = None,
        clear_function: Optional[ClearFunction] = None,
    ) -> None:
        self.target_fps = target_fps
        self.input_provider = input_provider or input
        self.output = output or print
        self.clear_function = clear_function
        self._scene_stack: List[Scene] = []
        self._running: bool = False

    # -- Scene stack ----------------------------------------------------
    def push_scene(self, scene: Scene) -> None:
        scene.app = self
        self._scene_stack.append(scene)
        scene.on_enter()

    def pop_scene(self) -> Optional[Scene]:
        if not self._scene_stack:
            return None

        scene = self._scene_stack.pop()
        scene.on_exit()
        scene.app = None
        return scene

    def replace_scene(self, scene: Scene) -> None:
        self.pop_scene()
        self.push_scene(scene)

    def current_scene(self) -> Optional[Scene]:
        if not self._scene_stack:
            return None
        return self._scene_stack[-1]

    # -- IO helpers -----------------------------------------------------
    def display(self, message: str = "") -> None:
        self.output(message)

    def get_input(self, prompt: str = "> ") -> str:
        return self.input_provider(prompt)

    def clear(self) -> None:
        if self.clear_function is not None:
            self.clear_function()
        else:
            self._default_clear()

    def _default_clear(self) -> None:
        stream = getattr(sys, "stdout", None)
        if stream is not None and hasattr(stream, "isatty") and stream.isatty():
            stream.write("\033[2J\033[H")
            stream.flush()
        else:
            # Fallback that pushes the previous content off-screen
            self.output("\n" * 5)

    # -- Game loop ------------------------------------------------------
    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        print("[DEBUG] GameApp.run() gestartet")
        if not self._scene_stack:
            print("[DEBUG] Keine Szenen im Stack!")
            raise RuntimeError("No scenes have been pushed onto the app.")

        self._running = True
        prev_time = time.perf_counter()
        first_scene = self.current_scene()
        if first_scene is not None:
            print("[DEBUG] Erste Szene vorhanden, render() wird aufgerufen")
            first_scene.render()

        try:
            while self._running and self._scene_stack:
                scene = self.current_scene()
                if scene is None:
                    break

                proceed = scene.handle_input()
                if not self._running:
                    scene.render()
                    break

                if proceed is False:
                    # Skip update/render for this frame (useful for asynchronous
                    # input handling or when the scene wants to wait).
                    continue

                now = time.perf_counter()
                delta = now - prev_time
                prev_time = now

                scene.update(delta)
                if not self._running:
                    scene.render()
                    break

                scene.render()

                if self.target_fps and self.target_fps > 0:
                    elapsed = time.perf_counter() - now
                    desired = 1.0 / self.target_fps
                    sleep_time = desired - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except KeyboardInterrupt:
            self.display("\nGame interrupted by user.")
        finally:
            self._running = False
            self._close_all_scenes()

    def _close_all_scenes(self) -> None:
        while self._scene_stack:
            scene = self._scene_stack.pop()
            scene.on_exit()
            scene.app = None

