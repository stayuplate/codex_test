"""Crystal Collector – the first playable demo built with the engine.

Run the script directly to start the game:

.. code-block:: bash

    python examples/first_game.py

Use the WASD keys to move around the board and collect all crystals before you
run out of energy.  Hazards will end your run instantly, so plan a safe path!
Rest near a safe spot to recover, sip energy wells for a boost, and keep an eye
out for shimmering portals that zip you across the cavern.
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
        self.energy_wells: Set[Position] = set()
        self.teleporters: Optional[Tuple[Position, Position]] = None
        self.energy_remaining: int = self.starting_energy
        self.turn_count: int = 0
        self.combo: int = 0
        self.best_combo: int = 0
        self.message: str = "Collect all crystals before your energy runs out!"

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        self.reset_board()

    # -- Game setup ------------------------------------------------------
    def reset_board(self) -> None:
        self.turn_count = 0
        self.player = (self.width // 2, self.height // 2)
        self.energy_remaining = self.starting_energy
        self.combo = 0
        self.best_combo = 0

        forbidden = {self.player}
        self.crystals = self._spawn_positions(self.total_crystals, forbidden)
        forbidden = forbidden | self.crystals
        available_tiles = self.width * self.height - len(forbidden)

        well_target = max(1, self.total_crystals // 3)
        well_count = min(well_target, available_tiles)
        if well_count:
            self.energy_wells = self._spawn_positions(well_count, forbidden)
            forbidden = forbidden | self.energy_wells
        else:
            self.energy_wells = set()

        teleporter = self._spawn_teleporters(forbidden)
        self.teleporters = teleporter
        if teleporter is not None:
            forbidden = forbidden | set(teleporter)

        available_tiles = self.width * self.height - len(forbidden)
        hazard_target = max(1, self.total_crystals // 2)
        hazard_count = min(hazard_target, available_tiles)
        if hazard_count == 0:
            self.hazards = set()
        else:
            self.hazards = self._spawn_positions(hazard_count, forbidden)

        self.message = (
            "Collect all crystals, sip energy wells (E) when tired, and try the shimmering portals (O)!"
        )

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

    def _spawn_teleporters(self, forbidden: Iterable[Position]) -> Optional[Tuple[Position, Position]]:
        forbidden_set = set(forbidden)
        available_tiles = self.width * self.height - len(forbidden_set)
        if available_tiles < 2:
            return None

        first = next(iter(self._spawn_positions(1, forbidden_set)))
        forbidden_set.add(first)
        second = next(iter(self._spawn_positions(1, forbidden_set)))
        return (first, second)

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
                elif position in self.energy_wells:
                    row.append("E")
                elif self.teleporters and position in self.teleporters:
                    row.append("O")
                else:
                    row.append(".")
            row.append("|")
            rows.append("".join(row))
        rows.append(border)
        rows.append(
            f"Energy: {self.energy_remaining:>2}   Crystals left: {len(self.crystals):>2}   Moves: {self.turn_count}"
        )
        rows.append(
            f"Energy wells: {len(self.energy_wells):>2}   Best combo: {self.best_combo:>2}"
        )
        rows.append(self.message)
        rows.append("Controls: W/A/S/D to move, Rest to recover, Scan for hints, R to restart, Q to quit.")
        rows.append("Legend: P=Player, *=Crystal, X=Hazard, E=Energy well, O=Portal")
        return "\n".join(rows)

    # -- Input handling --------------------------------------------------
    def process_command(self, command: str) -> None:
        command = command.strip().lower()
        if not command:
            self.message = "Use W/A/S/D to move, Rest to recover, Scan for hints, R to restart, or Q to quit."
            return

        if command in {"q", "quit", "exit"}:
            self.message = "Thanks for playing!"
            self.app.stop()
            return

        if command in {"r", "restart"}:
            self.reset_board()
            self.message = "The board has been reset."
            return

        if command in {"rest", "wait"}:
            self._rest()
            return

        if command in {"scan", "look"}:
            self.message = self._scan_report()
            return

        # Accept commands like "north" or "w" – only the first character matters.
        direction = command[0]
        mapping = {"w": MOVES[0], "a": MOVES[1], "s": MOVES[2], "d": MOVES[3]}
        move = mapping.get(direction)
        if move is None:
            self.message = (
                "Unknown command. Try W/A/S/D to move, Rest to recover, Scan for hints, R to restart, or Q to quit."
            )
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

        portal_message: Optional[str] = None
        if self.teleporters and self.player in self.teleporters:
            destination = self.teleporters[1] if self.player == self.teleporters[0] else self.teleporters[0]
            self.player = destination
            portal_message = "A shimmering portal warps you across the cavern!"

        messages: List[str] = []
        if portal_message is not None:
            messages.append(portal_message)

        if self.player in self.hazards:
            messages.append("Oh no! You stepped on a hazard. Game over.")
            self.app.stop()
            self.message = " ".join(messages)
            return

        if self.player in self.energy_wells:
            self.energy_wells.remove(self.player)
            energy_boost = self.rng.randint(2, 4)
            before = self.energy_remaining
            self.energy_remaining = min(self.starting_energy, self.energy_remaining + energy_boost)
            gained = self.energy_remaining - before
            if gained > 0:
                messages.append(f"You sip from an energy well and regain {gained} energy.")
            else:
                messages.append("The energy well sputters—you already feel fully charged.")

        if self.player in self.crystals:
            self.crystals.remove(self.player)
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            if not self.crystals:
                completion = (
                    f"You collected all the crystals in {self.turn_count} moves with a combo streak of {self.best_combo}!"
                )
                if portal_message:
                    completion = f"{portal_message} {completion}"
                if self.energy_remaining > 0:
                    completion += f" Energy to spare: {self.energy_remaining}."
                self.message = completion
                self.app.stop()
                return
            if self.combo >= 2:
                messages.append(f"Combo x{self.combo}! Keep chaining those crystals.")
            else:
                messages.append(self._encouragement())
        else:
            self.combo = 0
            if portal_message is None:
                messages.append(f"You move {move.label.lower()}.")

        if self.energy_remaining <= 0:
            messages.append("You ran out of energy. Game over.")
            self.app.stop()
        elif self.energy_remaining <= 2:
            messages.append("Warning: your energy is running dangerously low!")

        self.message = " ".join(messages)

    def _encouragement(self) -> str:
        phrases = (
            "Great job! Another crystal secured.",
            "Nice move! Keep an eye on those hazards.",
            "Crystal collected! You're on a roll.",
            "Well done, adventurer!",
        )
        return self.rng.choice(phrases)

    def _rest(self) -> None:
        if self.energy_remaining >= self.starting_energy:
            self.message = "You're already brimming with energy. No need to rest."
            return

        self.turn_count += 1
        potential_gain = min(2, self.starting_energy - self.energy_remaining)
        self.energy_remaining += potential_gain
        self.combo = 0
        if potential_gain == 0:
            base_message = "You take a breather, but feel just as energised as before."
        else:
            base_message = f"You rest for a moment and regain {potential_gain} energy."

        if self._move_hazard():
            self.message = f"{base_message} A nearby hazard slithers to a new position!"
        else:
            self.message = base_message

    def _move_hazard(self) -> bool:
        if not self.hazards:
            return False

        hazard = self.rng.choice(tuple(self.hazards))
        self.hazards.remove(hazard)

        forbidden: Set[Position] = {self.player} | self.crystals | self.hazards | self.energy_wells
        if self.teleporters:
            forbidden = forbidden | set(self.teleporters)
        forbidden.add(hazard)

        available_tiles = self.width * self.height - len(forbidden)
        if available_tiles <= 0:
            self.hazards.add(hazard)
            return False

        new_position = next(iter(self._spawn_positions(1, forbidden)))
        self.hazards.add(new_position)
        return True

    def _scan_report(self) -> str:
        def nearest_distance(positions: Set[Position]) -> Optional[int]:
            if not positions:
                return None
            return min(abs(px - self.player[0]) + abs(py - self.player[1]) for px, py in positions)

        parts: List[str] = []
        crystal_distance = nearest_distance(self.crystals)
        if crystal_distance is None:
            parts.append("No crystals detected – you're almost done!")
        else:
            parts.append(f"Nearest crystal is {crystal_distance} steps away.")

        hazard_distance = nearest_distance(self.hazards)
        if hazard_distance is None:
            parts.append("Hazard scanners show the path ahead is clear.")
        else:
            parts.append(f"Closest hazard lurks {hazard_distance} steps away.")

        well_distance = nearest_distance(self.energy_wells)
        if well_distance is None:
            parts.append("No fresh energy wells within range.")
        else:
            parts.append(f"Energy well within {well_distance} steps detected.")

        if self.teleporters:
            parts.append("Portals hum nearby – step on one (O) to warp across the cave.")

        return "Scan results: " + " ".join(parts)


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
