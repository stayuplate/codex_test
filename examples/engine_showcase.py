"""Engine Showcase – demonstrates recent improvements to the text engine.

Run the script directly to experience the demo::

    python examples/engine_showcase.py

The showcase walks through scene transitions, real-time updates, and the
improved raw-input handling.  Use the on-screen commands (including the arrow
keys when supported) to explore each feature.
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

# Ensure the ``src`` directory is importable when running the script directly.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from game_engine import GameApp, TextScene

SpinnerFrame = str


@dataclass(frozen=True)
class ShowcaseSummary:
    """Data object returned when the showcase transitions to the summary scene."""

    total_ticks: int
    boost_level: int
    raw_input_enabled: bool
    recent_actions: Iterable[str]
    elapsed_seconds: float


class TitleScene(TextScene):
    """Intro scene that explains the showcase controls."""

    def __init__(self, *, use_raw_input: bool) -> None:
        super().__init__(
            name="Engine Showcase", prompt="Start?", color="\033[94m", icon="⚙️"
        )
        self._use_raw_input = use_raw_input
        self.message = "Type 'start' to open the dashboard or 'quit' to exit."

    def get_display_text(self) -> str:  # pragma: no cover - exercised via render
        lines = [
            "Welcome to the engine showcase!",
            "",
            "This demo highlights improvements to the text renderer,",
            "scene stack management, and optional raw-input handling.",
            "",
            "Commands:",
            "  start  – switch to the live dashboard",
            "  quit   – leave the showcase",
        ]
        if self._use_raw_input:
            lines.extend(
                [
                    "",
                    "Tip: Raw input will be enabled in the dashboard so",
                    "     arrow keys and single-key shortcuts respond",
                    "     instantly.",
                ]
            )
        return "\n".join(lines)

    def process_command(self, command: str) -> None:
        normalized = command.strip().lower()
        if normalized in {"", "start", "s"}:
            if self.app is not None:
                self.app.replace_scene(ShowcaseScene(use_raw_input=self._use_raw_input))
            return

        if normalized in {"quit", "q", "exit"}:
            if self.app is not None:
                self.app.stop()
            return

        self.message = "Unknown command. Type 'start' or 'quit'."


class ShowcaseScene(TextScene):
    """Live dashboard that demonstrates multiple engine improvements."""

    HISTORY_SIZE = 5
    SPINNER_FRAMES: tuple[SpinnerFrame, ...] = (
        "⠋",
        "⠙",
        "⠹",
        "⠸",
        "⠼",
        "⠴",
        "⠦",
        "⠧",
        "⠇",
        "⠏",
    )

    def __init__(self, *, use_raw_input: bool) -> None:
        super().__init__(
            name="Live Dashboard",
            prompt="Command:",
            color="\033[92m",
            icon="🚀",
        )
        self._use_raw_input = use_raw_input
        self._raw_input_enabled = False
        self._spinner_cycle = itertools.cycle(self.SPINNER_FRAMES)
        self._current_spinner = next(self._spinner_cycle)
        self._elapsed_for_frame = 0.0
        self._total_elapsed = 0.0
        self._tick_count = 0
        self._boost = 1
        self._history: List[str] = []
        self._last_command: Optional[str] = None
        self.message = "Use boost/slow, pause, finish, or quit."
        self._start_time: Optional[float] = None

    # -- Properties for tests -------------------------------------------
    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def boost_level(self) -> int:
        return self._boost

    @property
    def history(self) -> List[str]:
        return list(self._history)

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        self._start_time = time.perf_counter()
        if self.app is not None and self._use_raw_input:
            self._raw_input_enabled = self.app.enable_raw_input()
        self.record_action("Dashboard initialised.")

    def on_exit(self) -> None:
        if self.app is not None and self._raw_input_enabled:
            self.app.disable_raw_input()
        self.record_action("Dashboard closed.")

    # -- Helpers ---------------------------------------------------------
    def record_action(self, entry: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self._history.append(f"[{timestamp}] {entry}")
        if len(self._history) > self.HISTORY_SIZE:
            self._history = self._history[-self.HISTORY_SIZE :]

    def _set_boost(self, delta: int) -> None:
        new_boost = max(1, min(5, self._boost + delta))
        if new_boost != self._boost:
            self._boost = new_boost
            self.record_action(f"Boost changed to x{self._boost}.")

    # -- Game loop -------------------------------------------------------
    def update(self, delta_time: float) -> None:
        scaled = delta_time * self._boost
        self._total_elapsed += scaled
        self._elapsed_for_frame += scaled
        frame_time = 0.35
        while self._elapsed_for_frame >= frame_time:
            self._elapsed_for_frame -= frame_time
            self._current_spinner = next(self._spinner_cycle)
            self._tick_count += 1

    def get_display_text(self) -> str:  # pragma: no cover - exercised via render
        total = self._total_elapsed
        elapsed_str = f"{total:05.2f} s"
        summary = [
            f"Spinner: {self._current_spinner}",
            f"Ticks:   {self._tick_count}",
            f"Boost:   x{self._boost}",
            f"Runtime: {elapsed_str}",
            "",
            "Recent actions:",
        ]
        if self._history:
            summary.extend(self._history)
        else:
            summary.append("  (no actions recorded yet)")
        summary.extend(
            [
                "",
                "Commands:",
                "  boost / + / ↑   – speed up the animation",
                "  slow  / - / ↓   – reduce the animation speed",
                "  pause           – push a pause scene onto the stack",
                "  finish          – jump to the summary scene",
                "  quit            – stop the showcase",
            ]
        )
        return "\n".join(summary)

    def process_command(self, command: str) -> None:
        self._last_command = command
        normalized = command.strip().lower()
        if not normalized:
            self.record_action("Tick acknowledged.")
            self.message = "Animation continues. Try 'boost' or 'pause'."
            return

        if normalized in {"boost", "+"} or command in {"\x1b[A", "\x1bOA"}:
            self._set_boost(+1)
            self.message = "Boost increased."
            return

        if normalized in {"slow", "-"} or command in {"\x1b[B", "\x1bOB"}:
            self._set_boost(-1)
            self.message = "Boost decreased."
            return

        if normalized in {"pause", "p"}:
            if self.app is not None:
                self.app.push_scene(PauseScene(parent=self))
            return

        if normalized in {"finish", "f"}:
            if self.app is not None:
                summary = self.build_summary()
                self.app.replace_scene(
                    SummaryScene(summary=summary, use_raw_input=self._use_raw_input)
                )
            return

        if normalized in {"quit", "q", "exit"}:
            if self.app is not None:
                self.app.stop()
            return

        self.message = "Unknown command. Try boost, slow, pause, finish, or quit."

    # -- Summary ---------------------------------------------------------
    def build_summary(self) -> ShowcaseSummary:
        elapsed = 0.0
        if self._start_time is not None:
            elapsed = time.perf_counter() - self._start_time
        return ShowcaseSummary(
            total_ticks=self._tick_count,
            boost_level=self._boost,
            raw_input_enabled=self._raw_input_enabled,
            recent_actions=list(self._history),
            elapsed_seconds=elapsed,
        )


class PauseScene(TextScene):
    """Scene stacked on top of the dashboard to demonstrate pausing."""

    def __init__(self, *, parent: ShowcaseScene) -> None:
        super().__init__(
            name="Paused", prompt="Resume?", color="\033[93m", icon="⏸️"
        )
        self._parent = parent
        self.message = "Type 'resume' to continue or 'quit' to exit the app."

    def get_display_text(self) -> str:  # pragma: no cover - exercised via render
        summary = self._parent.build_summary()
        lines = [
            "The dashboard is paused.",
            "",
            f"Ticks completed: {summary.total_ticks}",
            f"Current boost:   x{summary.boost_level}",
            "",
            "Commands:",
            "  resume / r – pop this scene and return",
            "  quit       – stop the showcase",
        ]
        return "\n".join(lines)

    def process_command(self, command: str) -> None:
        normalized = command.strip().lower()
        if normalized in {"", "resume", "r", "continue"}:
            if self.app is not None:
                self.app.pop_scene()
            self._parent.message = "Resumed from pause."
            self._parent.record_action("Resumed from pause scene.")
            return

        if normalized in {"quit", "q", "exit"}:
            if self.app is not None:
                self.app.stop()
            return

        self.message = "Unknown command. Type 'resume' or 'quit'."


class SummaryScene(TextScene):
    """Final scene that presents the collected statistics."""

    def __init__(self, *, summary: ShowcaseSummary, use_raw_input: bool) -> None:
        super().__init__(
            name="Showcase Summary",
            prompt="Next:",
            color="\033[96m",
            icon="📊",
        )
        self._summary = summary
        self._use_raw_input = use_raw_input
        self.message = "Type 'restart' to replay, 'menu' for the intro, or 'quit'."

    def get_display_text(self) -> str:  # pragma: no cover - exercised via render
        actions = list(self._summary.recent_actions)
        lines = [
            "Showcase complete!",
            "",
            f"Ticks performed: {self._summary.total_ticks}",
            f"Boost level:    x{self._summary.boost_level}",
            f"Raw input used: {'yes' if self._summary.raw_input_enabled else 'no'}",
            f"Elapsed time:   {self._summary.elapsed_seconds:0.2f} s",
            "",
            "Recent actions:",
        ]
        if actions:
            lines.extend(actions)
        else:
            lines.append("  (no logged actions)")
        lines.extend(
            [
                "",
                "Commands:",
                "  restart – replay the dashboard immediately",
                "  menu    – jump back to the intro scene",
                "  quit    – close the showcase",
            ]
        )
        return "\n".join(lines)

    def process_command(self, command: str) -> None:
        normalized = command.strip().lower()
        if normalized in {"restart", "r"}:
            if self.app is not None:
                self.app.replace_scene(ShowcaseScene(use_raw_input=self._use_raw_input))
            return

        if normalized in {"menu", "m"}:
            if self.app is not None:
                self.app.replace_scene(TitleScene(use_raw_input=self._use_raw_input))
            return

        if normalized in {"quit", "q", "exit"}:
            if self.app is not None:
                self.app.stop()
            return

        self.message = "Unknown command. Type restart, menu, or quit."


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Engine Showcase demo")
    parser.add_argument(
        "--fps",
        type=float,
        default=12.0,
        help="Target frames per second for the dashboard animation.",
    )
    parser.add_argument(
        "--no-raw-input",
        action="store_true",
        help="Disable raw-input mode even when the terminal supports it.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    app = GameApp(target_fps=args.fps, use_raw_input=not args.no_raw_input)
    app.push_scene(TitleScene(use_raw_input=not args.no_raw_input))
    app.run()
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
