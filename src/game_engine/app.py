"""Main application loop for the lightweight game engine."""

from __future__ import annotations

import io
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
        use_raw_input: bool = False,
    ) -> None:
        self.target_fps = target_fps
        self._custom_input_provider = input_provider is not None
        self.input_provider = input_provider or input
        self.output = output or print
        self.clear_function = clear_function
        self._scene_stack: List[Scene] = []
        self._running: bool = False
        self._raw_input_enabled = False

        if not self._custom_input_provider and use_raw_input:
            self.enable_raw_input()

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

    # -- Raw input helpers -----------------------------------------------
    def enable_raw_input(self) -> bool:
        """Switch to the raw input provider if the environment supports it."""

        if self._custom_input_provider:
            return False

        provider = self._create_raw_input_provider()
        if provider is None:
            self.disable_raw_input()
            return False

        self.input_provider = provider
        self._raw_input_enabled = True
        return True

    def disable_raw_input(self) -> None:
        if self._custom_input_provider:
            return

        self.input_provider = input
        self._raw_input_enabled = False

    def _stdin_is_tty(self) -> bool:
        stream = getattr(sys, "stdin", None)
        if stream is None or not hasattr(stream, "isatty"):
            return False
        try:
            return bool(stream.isatty())
        except io.UnsupportedOperation:
            return False

    def _create_raw_input_provider(self) -> Optional[InputProvider]:
        if not self._stdin_is_tty():
            return None

        if sys.platform == "win32":
            return self._create_windows_raw_input_provider()
        return self._create_posix_raw_input_provider()

    def _create_posix_raw_input_provider(self) -> Optional[InputProvider]:
        stream = getattr(sys, "stdin", None)
        if stream is None or not hasattr(stream, "fileno"):
            return None

        try:
            fd = stream.fileno()
        except (io.UnsupportedOperation, AttributeError, ValueError, OSError):
            return None

        def provider(prompt: str = "> ") -> str:
            import os
            import select
            import termios
            import tty

            stdout = getattr(sys, "stdout", None)
            if stdout is not None:
                stdout.write(prompt)
                stdout.flush()

            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                buffer: List[str] = []
                while True:
                    data = os.read(fd, 1)
                    if not data:
                        raise EOFError

                    char = data.decode("utf-8", "ignore")
                    if not char:
                        continue

                    if char in ("\r", "\n"):
                        if stdout is not None:
                            stdout.write("\n")
                            stdout.flush()
                        return "".join(buffer)

                    if char == "\x03":
                        raise KeyboardInterrupt

                    if char in ("\x7f", "\b"):
                        if buffer:
                            buffer.pop()
                            if stdout is not None:
                                stdout.write("\b \b")
                                stdout.flush()
                        continue

                    if char == "\x04":  # Ctrl-D
                        raise EOFError

                    if char == "\x1b":
                        sequence = [char]
                        while True:
                            ready, _, _ = select.select([fd], [], [], 0.0001)
                            if not ready:
                                break
                            extra = os.read(fd, 1)
                            if not extra:
                                break
                            decoded = extra.decode("utf-8", "ignore")
                            if not decoded:
                                break
                            sequence.append(decoded)
                            if decoded.isalpha() or decoded in "~":
                                break
                            if len(sequence) >= 6:
                                break
                        return "".join(sequence)

                    buffer.append(char)
                    if stdout is not None:
                        stdout.write(char)
                        stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return provider

    def _create_windows_raw_input_provider(self) -> Optional[InputProvider]:
        try:
            import msvcrt
        except ImportError:  # pragma: no cover - platform specific
            return None

        mapping = {
            "H": "\x1b[A",
            "P": "\x1b[B",
            "K": "\x1b[D",
            "M": "\x1b[C",
        }

        def provider(prompt: str = "> ") -> str:
            stdout = getattr(sys, "stdout", None)
            if stdout is not None:
                stdout.write(prompt)
                stdout.flush()

            buffer: List[str] = []
            while True:
                char = msvcrt.getwch()

                if char in ("\r", "\n"):
                    if stdout is not None:
                        stdout.write("\n")
                        stdout.flush()
                    return "".join(buffer)

                if char == "\x03":
                    raise KeyboardInterrupt

                if char in ("\b", "\x7f"):
                    if buffer:
                        buffer.pop()
                        if stdout is not None:
                            stdout.write("\b \b")
                            stdout.flush()
                    continue

                if char in ("\x00", "\xe0"):
                    code = msvcrt.getwch()
                    sequence = mapping.get(code)
                    if sequence is not None:
                        return sequence
                    continue

                if char == "\x1a":  # Ctrl-Z behaves like EOF in Windows terminals
                    raise EOFError

                if char == "\x1b":
                    return char

                buffer.append(char)
                if stdout is not None:
                    stdout.write(char)
                    stdout.flush()

        return provider

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
        self.display("[DEBUG] GameApp.run() gestartet")
        if not self._scene_stack:
            self.display("[DEBUG] Keine Szenen im Stack!")
            raise RuntimeError("No scenes have been pushed onto the app.")

        self._running = True
        prev_time = time.perf_counter()
        first_scene = self.current_scene()
        if first_scene is not None:
            self.display("[DEBUG] Erste Szene vorhanden, render() wird aufgerufen")
            first_scene.render()

        try:
            while self._running and self._scene_stack:
                scene = self.current_scene()
                if scene is None:
                    break

                proceed = scene.handle_input()
                if not self._running:
                    current = self.current_scene()
                    if current is not None:
                        current.render()
                    break

                if proceed is False:
                    # Skip update/render for this frame (useful for asynchronous
                    # input handling or when the scene wants to wait).
                    continue

                now = time.perf_counter()
                delta = now - prev_time
                prev_time = now

                scene = self.current_scene()
                if scene is None:
                    continue

                scene.update(delta)
                if not self._running:
                    current = self.current_scene()
                    if current is not None:
                        current.render()
                    break

                scene = self.current_scene()
                if scene is None:
                    continue

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
