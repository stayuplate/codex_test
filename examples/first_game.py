"""Crystal Collector – the first playable demo built with the engine.

Run the script directly to start the game:

.. code-block:: bash

    python examples/first_game.py

Use the WASD keys to move around the board and collect all crystals before you
run out of energy.  Hazards will end your run instantly, so plan a safe path!
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

# Ensure the ``src`` directory is importable when running the script directly.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from game_engine import GameApp, TextScene

Position = Tuple[int, int]


@dataclass
class Move:
    label: str
    delta: Position


MOVES: Sequence[Move] = (
    Move("Up", (0, -1)),
    Move("Left", (-1, 0)),
    Move("Down", (0, 1)),
    Move("Right", (1, 0)),
)


class CrystalCollectorScene(TextScene):
    """A small turn-based grid adventure.

    The player starts in the middle of the board and must collect every crystal
    before running out of energy.  Hazards (``X``) end the game immediately when
    stepped on.
    """

    def __init__(
        self,
        *,
        width: int = 6,
        height: int = 6,
        crystals: int = 5,
        energy: int = 18,
        seed: Optional[int] = None,
    ) -> None:
        print("[DEBUG] CrystalCollectorScene.__init__ wird aufgerufen")
        super().__init__(name="CrystalCollector")
        if width < 3 or height < 3:
            raise ValueError("The board must be at least 3x3 in size.")

        max_items = width * height - 1
        if crystals < 1 or crystals > max_items:
            raise ValueError("Number of crystals must be between 1 and the number of available tiles.")

        self.width = width
        self.height = height
        self.total_crystals = crystals
        self.starting_energy = max(1, energy)
        self.rng = random.Random(seed)

        self.player: Position = (0, 0)
        self.crystals: Set[Position] = set()
        self.hazards: Set[Position] = set()
        self.energy_remaining: int = self.starting_energy
        self.turn_count: int = 0
        self.message: str = "Collect all crystals before your energy runs out!"

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        self.reset_board()

    # -- Game setup ------------------------------------------------------
    def reset_board(self) -> None:
        self.turn_count = 0
        self.player = (self.width // 2, self.height // 2)
        self.energy_remaining = self.starting_energy

        forbidden = {self.player}
        self.crystals = self._spawn_positions(self.total_crystals, forbidden)
        forbidden = forbidden | self.crystals
        available_tiles = self.width * self.height - len(forbidden)
        hazard_target = max(1, self.total_crystals // 2)
        hazard_count = min(hazard_target, available_tiles)
        if hazard_count == 0:
            self.hazards = set()
        else:
            self.hazards = self._spawn_positions(hazard_count, forbidden)

        self.message = "Collect all crystals before your energy runs out!"

    def _spawn_positions(self, count: int, forbidden: Iterable[Position]) -> Set[Position]:
        forbidden_set = set(forbidden)
        available_tiles = self.width * self.height - len(forbidden_set)
        if count > available_tiles:
            raise ValueError("Not enough free tiles to place all objects.")

        positions: Set[Position] = set()
        while len(positions) < count:
            pos = (self.rng.randrange(self.width), self.rng.randrange(self.height))
            if pos in forbidden_set or pos in positions:
                continue
            positions.add(pos)
        return positions

    # -- Rendering -------------------------------------------------------
    def get_display_text(self) -> str:
        border = "+" + "-" * self.width + "+"
        rows: List[str] = [border]
        for y in range(self.height):
            row = ["|"]
            for x in range(self.width):
                position = (x, y)
                if position == self.player:
                    row.append("P")
                elif position in self.crystals:
                    row.append("*")
                elif position in self.hazards:
                    row.append("X")
                else:
                    row.append(".")
            row.append("|")
            rows.append("".join(row))
        rows.append(border)
        rows.append(
            f"Energy: {self.energy_remaining:>2}   Crystals left: {len(self.crystals):>2}   Moves: {self.turn_count}"
        )
        rows.append(self.message)
        rows.append("Controls: W/A/S/D to move, R to restart, Q to quit.")
        rows.append("Legend: P=Player, *=Crystal, X=Hazard")
        return "\n".join(rows)

    # -- Input handling --------------------------------------------------
    def process_command(self, command: str) -> None:
        command = command.strip().lower()
        if not command:
            self.message = "Use W/A/S/D to move, R to restart, or Q to quit."
            return

        if command in {"q", "quit", "exit"}:
            self.message = "Thanks for playing!"
            self.app.stop()
            return

        if command in {"r", "restart"}:
            self.reset_board()
            self.message = "The board has been reset."
            return

        # Accept commands like "north" or "w" – only the first character matters.
        direction = command[0]
        mapping = {"w": MOVES[0], "a": MOVES[1], "s": MOVES[2], "d": MOVES[3]}
        move = mapping.get(direction)
        if move is None:
            self.message = "Unknown command. Use W, A, S, D to move, R to restart, or Q to quit."
            return

        self._apply_move(move)

    # -- Game logic ------------------------------------------------------
    def _apply_move(self, move: Move) -> None:
        dx, dy = move.delta
        new_x = max(0, min(self.width - 1, self.player[0] + dx))
        new_y = max(0, min(self.height - 1, self.player[1] + dy))
        new_position = (new_x, new_y)

        if new_position == self.player:
            self.message = "You bump into the edge of the world."
            return

        self.player = new_position
        self.turn_count += 1
        self.energy_remaining -= 1

        if new_position in self.hazards:
            self.message = "Oh no! You stepped on a hazard. Game over."
            self.app.stop()
            return

        if new_position in self.crystals:
            self.crystals.remove(new_position)
            if not self.crystals:
                self.message = f"You collected all the crystals in {self.turn_count} moves!"
                self.app.stop()
                return
            self.message = self._encouragement()
        else:
            self.message = f"You move {move.label.lower()}."

        if self.energy_remaining <= 0:
            self.message = "You ran out of energy. Game over."
            self.app.stop()

    def _encouragement(self) -> str:
        phrases = (
            "Great job! Another crystal secured.",
            "Nice move! Keep an eye on those hazards.",
            "Crystal collected! You're on a roll.",
            "Well done, adventurer!",
        )
        return self.rng.choice(phrases)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play the Crystal Collector demo.")
    parser.add_argument("--width", type=int, default=6, help="Width of the board (default: 6).")
    parser.add_argument("--height", type=int, default=6, help="Height of the board (default: 6).")
    parser.add_argument(
        "--crystals",
        type=int,
        default=5,
        help="Number of crystals to place on the board (default: 5).",
    )
    parser.add_argument(
        "--energy",
        type=int,
        default=18,
        help="How much energy the player starts with (default: 18 moves).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible layouts.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    scene = CrystalCollectorScene(
        width=args.width,
        height=args.height,
        crystals=args.crystals,
        energy=args.energy,
        seed=args.seed,
    )
    app = GameApp()
    app.push_scene(scene)
    app.run()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
