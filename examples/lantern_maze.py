"""Lantern Maze – a fog-of-war exploration puzzle built with the engine.

Run the script directly to start the game:

.. code-block:: bash

    python examples/lantern_maze.py

Guide the wanderer through a mysterious maze while capturing floating lights
("torches").  The exit only opens once every light has been collected.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

# Ensure the ``src`` directory is importable when running the script directly.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from game_engine import GameApp, TextScene

Position = Tuple[int, int]


@dataclass(frozen=True)
class Move:
    label: str
    delta: Position


MOVES: Sequence[Move] = (
    Move("north", (0, -1)),
    Move("west", (-1, 0)),
    Move("south", (0, 1)),
    Move("east", (1, 0)),
)


class LanternMazeScene(TextScene):
    """Turn-based maze exploration with fog of war.

    The player carries a lantern that illuminates tiles in a limited radius.
    Collect all luminous wisps (``*``) before visiting the exit.
    """

    MAP_BLUEPRINT: Sequence[str] = (
        "#################",
        "#P....#..*..#...#",
        "###.#.#.###.#.#.#",
        "#...#...#...#.#.#",
        "#.#.###.#.###.#.#",
        "#.#.....#...#...#",
        "#.#.#####.#.###.#",
        "#.#.....#.#...#E#",
        "#.###.#.#.###.#.#",
        "#.....#...#..*..#",
        "#################",
    )

    def __init__(self, *, view_radius: int = 2) -> None:
        super().__init__(name="LanternMaze", prompt="Action > ")
        if view_radius < 1:
            raise ValueError("view_radius must be at least 1.")

        self.view_radius = view_radius

        self.width = len(self.MAP_BLUEPRINT[0])
        self.height = len(self.MAP_BLUEPRINT)
        self._layout: List[List[str]] = []
        self.start: Optional[Position] = None
        self.exit: Optional[Position] = None
        self._torches_initial: Set[Position] = set()

        for y, row in enumerate(self.MAP_BLUEPRINT):
            if len(row) != self.width:
                raise ValueError("All rows of the map must have the same width.")
            row_tiles: List[str] = []
            for x, tile in enumerate(row):
                if tile == "#":
                    row_tiles.append("#")
                else:
                    row_tiles.append(".")
                    if tile == "P":
                        self.start = (x, y)
                    elif tile == "E":
                        self.exit = (x, y)
                    elif tile == "*":
                        self._torches_initial.add((x, y))
            self._layout.append(row_tiles)

        if self.start is None or self.exit is None:
            raise ValueError("Map must define both a start (P) and exit (E) tile.")

        self.total_torches = len(self._torches_initial)

        self.player: Position = self.start
        self._torches: Set[Position] = set(self._torches_initial)
        self._discovered: Set[Position] = set()
        self._visited: Set[Position] = set()
        self.turn_count: int = 0
        self.message: str = "Collect every wandering light to open the exit."

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        self.reset_world()

    # -- Setup -----------------------------------------------------------
    def reset_world(self) -> None:
        self.player = self.start  # type: ignore[assignment]
        self._torches = set(self._torches_initial)
        self._discovered = set()
        self._visited = {self.player}
        self.turn_count = 0
        self.message = "Collect every wandering light to open the exit."
        self._reveal_area(self.player)

    # -- Helpers ---------------------------------------------------------
    def _in_bounds(self, position: Position) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_wall(self, position: Position) -> bool:
        x, y = position
        return self._layout[y][x] == "#"

    def _reveal_area(self, center: Position) -> None:
        cx, cy = center
        for dy in range(-self.view_radius, self.view_radius + 1):
            for dx in range(-self.view_radius, self.view_radius + 1):
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds((nx, ny)):
                    continue
                if max(abs(dx), abs(dy)) <= self.view_radius:
                    self._discovered.add((nx, ny))

    def _describe_torches(self) -> str:
        # Farben
        YELLOW = "\033[93m"
        RESET = "\033[0m"
        remaining = len(self._torches)
        captured = self.total_torches - remaining
        bar_length = max(10, self.total_torches * 3)
        if self.total_torches == 0:
            return f"{YELLOW}No lights required to leave.{RESET}"
        ratio = captured / self.total_torches
        lit = int(ratio * bar_length)
        bar = f"{YELLOW}" + "🕯️" * lit + f"{RESET}" + "." * (bar_length - lit)
        return f"{YELLOW}Lights: [{bar}] {captured}/{self.total_torches} captured{RESET}"

    def _format_tile(self, position: Position) -> str:
        # Farben
        PLAYER = "\033[96m"  # Cyan
        TORCH = "\033[93m"   # Gelb
        EXIT = "\033[92m"    # Grün
        EXIT_LOCKED = "\033[91m" # Rot
        WALL = "\033[90m"    # Dunkelgrau
        VISITED = "\033[37m" # Hellgrau
        RESET = "\033[0m"
        if position not in self._discovered:
            return " "
        if position == self.player:
            return f"{PLAYER}🧑‍🦯{RESET}"
        if position in self._torches:
            return f"{TORCH}🕯️{RESET}"
        if position == self.exit:
            if self._torches:
                return f"{EXIT_LOCKED}🔒{RESET}"
            return f"{EXIT}🚪{RESET}"
        if self._is_wall(position):
            return f"{WALL}⬛{RESET}"
        if position in self._visited:
            return f"{VISITED}·{RESET}"
        return " "

    # -- Rendering -------------------------------------------------------
    def get_display_text(self) -> str:
        # Farben
        TITLE = "\033[95m"
        RESET = "\033[0m"
        # ASCII-Banner
        banner = (
            f"{TITLE} _                _                 _   _                 \n"
            f"| |    __ _ _ __   __| | ___  _ __ __ _| |_(_) ___  _ __  ___ \n"
            f"| |   / _` | '_ \ / _` |/ _ \| '__/ _` | __| |/ _ \| '_ \/ __|\n"
            f"| |__| (_| | | | | (_| | (_) | | | (_| | |_| | (_) | | | \__ \\\n"
            f"|_____\__,_|_| |_|\__,_|\___/|_|  \__,_|\__|_|\___/|_| |_|___/\n"
            f"{RESET}"
        )
        border = "+" + "-" * self.width + "+"
        rows: List[str] = [banner, border]
        for y in range(self.height):
            row_tiles = [self._format_tile((x, y)) for x in range(self.width)]
            rows.append("|" + "".join(row_tiles) + "|")
        rows.append(border)
        rows.append(self._describe_torches())
        # Farbige Statuszeile
        rows.append(f"\033[94mTurns taken: {self.turn_count}{RESET}")
        rows.append(f"\033[92m{self.message}{RESET}")
        rows.append("\033[90mCommands: W/A/S/D to move, R to restart, Q to quit.\033[0m")
        return "\n".join(rows)

    # -- Input handling --------------------------------------------------
    def process_command(self, command: str) -> None:
        if self.app is None:
            raise RuntimeError("Scene is not attached to an application.")

        command = command.strip().lower()
        if not command:
            self.message = "Use W/A/S/D to move, R to restart, or Q to quit."
            return

        if command in {"q", "quit", "exit"}:
            self.message = "The lantern fades as you depart the maze."
            self.app.stop()
            return

        if command in {"r", "restart"}:
            self.reset_world()
            self.message = "You reignite your lantern at the maze entrance."
            return

        move = None
        if command in {"w", "a", "s", "d"}:
            mapping = {"w": MOVES[0], "a": MOVES[1], "s": MOVES[2], "d": MOVES[3]}
            move = mapping[command]
        else:
            for candidate in MOVES:
                if command.startswith(candidate.label[0]):
                    move = candidate
                    break
        if move is None:
            self.message = "Unknown command. Use W, A, S, D to move, R to restart, or Q to quit."
            return

        self._attempt_move(move)

    # -- Game logic ------------------------------------------------------
    def _attempt_move(self, move: Move) -> None:
        if self.app is None:
            return

        dx, dy = move.delta
        new_position = (self.player[0] + dx, self.player[1] + dy)

        if not self._in_bounds(new_position) or self._is_wall(new_position):
            self.message = "Your lantern reveals a solid wall in that direction."
            return

        self.player = new_position
        self.turn_count += 1
        self._visited.add(new_position)
        self._reveal_area(new_position)

        if new_position in self._torches:
            self._torches.remove(new_position)
            if self._torches:
                self.message = "You capture a wandering light! The gate grows brighter."
            else:
                self.message = "The final light joins your lantern. The exit radiates vividly!"
            return

        if new_position == self.exit:
            if self._torches:
                self.message = "The crystalline gate remains sealed. Collect every light first."
            else:
                self.message = f"You escape the maze in {self.turn_count} turns!"
                self.app.stop()
            return

        self.message = f"You move {move.label}."

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore the glowing Lantern Maze.")
    parser.add_argument(
        "--view-radius",
        type=int,
        default=2,
        help="How far the lantern illuminates around the player (default: 2).",
    )
    return parser

def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    scene = LanternMazeScene(view_radius=args.view_radius)
    app = GameApp()
    app.push_scene(scene)
    app.run()

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

