"""Lantern Maze – a fog-of-war exploration puzzle built with the engine.

Run the script directly to start the game:

.. code-block:: bash

    python examples/lantern_maze.py

Guide the wanderer through a mysterious maze while capturing floating lights
("torches").  Earn points for exploring new territory, collect every light to
unlock the exit, and ask your lantern for a hint (press ``H``) when you feel
lost.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

import random

# Ensure the ``src`` directory is importable when running the script directly.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from game_engine import GameApp, TextScene

Position = Tuple[int, int]


# Labyrinth-Definition (einfach lösbar Pfad von P zu E)
_RAW_MAP: Sequence[str] = [
"######################",
"#P...##......##......#",
"#....##.##..##.##....#",
"#....#....##..#..#...#",
"#..###.##.##.##.##.##",
"#..#....#....#....#..#",
"#..#.##.##.##.#.##.#.#",
"#..#.#.......#.#..#..#",
"#..#.#.#######.##.###.#",
"#..#.#.#.....#....#..#",
"#..#.#.#.###.####.#..#",
"#..#...#.#.#......#..#",
"#.#####.#.#.#########.#",
"#.#.....#.#....##.....#",
"#.#.#####.####.###.##.#",
"#.#.....#.......#.....#",
"#.#######.#####.#.####.#",
"#.......#.....#.#....#.#",
"#.#####.###.#.#.###.#..#",
"#.#...#...#.#.#...#.#..#",
"#.###.###.#.#.###.#.#..#",
"#.............#.....#..#",
"#...........E........#",
]
MAP_BLUEPRINT: Sequence[str] = tuple(row.ljust(22, '#')[:22] for row in _RAW_MAP)



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


ARROW_KEY_MAPPING = {
    "\x1b[A": MOVES[0],  # Up arrow -> north (ANSI escape)
    "\x1bOA": MOVES[0],
    "\x1b[D": MOVES[1],  # Left arrow -> west
    "\x1bOD": MOVES[1],
    "\x1b[B": MOVES[2],  # Down arrow -> south
    "\x1bOB": MOVES[2],
    "\x1b[C": MOVES[3],  # Right arrow -> east
    "\x1bOC": MOVES[3],
}

MOVE_HELP_TEXT = (
    "Use W/A/S/D or the arrow keys to move, H for a hint, R to restart, or Q to quit."
)


class LanternMazeScene(TextScene):
    EXPLORATION_POINTS = 2
    TORCH_POINTS = 35
    TRAP_PENALTY = 10
    EXIT_BONUS = 75

    def __init__(
        self,
        *,
        view_radius: int = 2,
        num_torches: int = 2,
        num_traps: int = 2,
        rng_seed: Optional[int] = None,
    ) -> None:
        super().__init__(
            name="Lantern Maze",
            prompt="Move:",
            color="\033[95m",  # Lila
            border=True,
            icon="\U0001F56F",  # Laterne-Emoji
        )
        self._last_move = None
        self.view_radius = view_radius
        self.num_torches = num_torches
        self.num_traps = num_traps
        self.width = len(MAP_BLUEPRINT[0])
        self.height = len(MAP_BLUEPRINT)
        self._layout = []
        self.start = None
        self.exit = None
        self._floor_positions = []
        for y, row in enumerate(MAP_BLUEPRINT):
            if len(row) != self.width:
                raise ValueError("All rows of the map must have the same width.")
            row_tiles = []
            for x, tile in enumerate(row):
                if tile == "#":
                    row_tiles.append("#")
                else:
                    row_tiles.append(".")
                    if tile == "P":
                        self.start = (x, y)
                    elif tile == "E":
                        self.exit = (x, y)
            self._layout.append(row_tiles)
        if self.start is None or self.exit is None:
            raise ValueError("Map must define both a start (P) and exit (E) tile.")
        # Erreichbare Felder berechnen (Flood-Fill/BFS)
        from collections import deque

        def reachable_from(start):
            visited = set()
            queue = deque([start])
            while queue:
                pos = queue.popleft()
                if pos in visited:
                    continue
                visited.add(pos)
                x, y = pos
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self._layout[ny][nx] == "#":
                            continue
                        npos = (nx, ny)
                        if npos not in visited:
                            queue.append(npos)
            return visited

        reachable = reachable_from(self.start)
        self._reachable_positions = reachable - {self.start, self.exit}
        if self.exit not in reachable:
            raise ValueError("Exit is not reachable from start! Please check the map layout.")
        self.total_torches = num_torches
        # Initialisiere total_traps im Konstruktor
        self.total_traps = num_traps
        self.player = self.start
        self._torches = set()
        self._traps = set()
        self._discovered = set()
        self._visited = set()
        self.turn_count = 0
        self.message = "Collect every wandering light to open the exit."
        self._ambient_messages = (
            "A chill breeze twirls the lantern's flame.",
            "Distant chimes echo through the labyrinth.",
            "Faint footprints glow briefly on the floor before fading.",
            "You sense the maze shifting ever so slightly around you.",
            "The stone walls pulse with a low, otherworldly hum.",
        )
        self._random = random.Random(rng_seed)
        self.score = 0
        self._last_hint_turn: Optional[int] = None
        self.reset_world()

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        self.reset_world()

    # -- Setup -----------------------------------------------------------
    def reset_world(self) -> None:
        self.player = self.start  # type: ignore[assignment]
        # Zufällige Torches und Fallen
        available = list(self._reachable_positions)
        if len(available) < self.total_torches + self.total_traps:
            raise ValueError("Not enough reachable positions for torches and traps!")

        # Intelligent placement: traps prefer dead-ends, torches at moderate distance
        dead_ends = list(self._find_dead_ends())
        traps = set()
        torches = set()

        # Place traps in dead-ends first
        self._random.shuffle(dead_ends)
        for pos in dead_ends:
            if len(traps) >= self.total_traps:
                break
            if pos in available:
                traps.add(pos)

        # Fill remaining traps randomly from available
        remaining_trap_slots = self.total_traps - len(traps)
        if remaining_trap_slots > 0:
            pool = [p for p in available if p not in traps and p != self.start and p != self.exit]
            if remaining_trap_slots > len(pool):
                raise ValueError("Not enough positions to place traps after filtering")
            traps.update(self._random.sample(pool, remaining_trap_slots))

        # Place torches at moderate distance from start (not adjacent, not too far)
        pool = [p for p in available if p not in traps and p != self.start and p != self.exit]
        pool.sort(key=lambda p: abs(p[0]-self.start[0]) + abs(p[1]-self.start[1]))
        mid = len(pool) // 2
        # choose positions around the middle of sorted-by-distance list
        spread = max(1, len(pool)//8)
        choices = pool[max(0, mid-spread): min(len(pool), mid+spread)]
        if len(choices) < self.total_torches:
            choices = pool
        torches.update(self._random.sample(choices, self.total_torches))

        self._traps = traps
        self._torches = torches
        self._discovered = set()
        self._visited = {self.player}
        self.turn_count = 0
        self.message = "Collect every wandering light to open the exit."
        self.score = 0
        self._last_hint_turn = None
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

    def _neighbors(self, position: Position) -> List[Position]:
        x, y = position
        neigh = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self._layout[ny][nx] != '#':
                    neigh.append((nx, ny))
        return neigh

    def _distance(self, a: Position, b: Position) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_dead_ends(self) -> Set[Position]:
        dead = set()
        for y in range(self.height):
            for x in range(self.width):
                if self._layout[y][x] == '#':
                    continue
                pos = (x, y)
                if pos == self.start or pos == self.exit:
                    continue
                if len(self._neighbors(pos)) <= 1:
                    dead.add(pos)
        return dead

    def _describe_torches(self) -> str:
        # Farbverlauf für Fortschrittsbalken
        COLORS = ["\033[93m", "\033[95m", "\033[92m", "\033[96m", "\033[91m"]
        RESET = "\033[0m"
        remaining = len(self._torches)
        captured = self.total_torches - remaining
        bar_length = max(10, self.total_torches * 3)
        if self.total_torches == 0:
            return f"\033[93mNo lights required to leave.{RESET}"
        ratio = captured / self.total_torches
        lit = int(ratio * bar_length)
        bar = ""
        for i in range(bar_length):
            color = COLORS[i % len(COLORS)]
            if i < lit:
                bar += f"{color}*{RESET}"
            else:
                bar += "."
        return f"\033[93mLights: [{bar}] {captured}/{self.total_torches} captured{RESET}"

    def _direction_description(self, delta: Position) -> str:
        dx, dy = delta
        parts: List[str] = []
        if dy < 0:
            parts.append("north")
        elif dy > 0:
            parts.append("south")
        if dx > 0:
            parts.append("east")
        elif dx < 0:
            parts.append("west")
        if not parts:
            return "here"
        return "-".join(parts)

    def _hint(self) -> None:
        if self.app is None:
            raise RuntimeError("Scene is not attached to an application.")

        if self._last_hint_turn is not None and self.turn_count == self._last_hint_turn:
            self.message = "The lantern's glow has nothing new to show you until you move."
            return

        if self._torches:
            target_pool = self._torches
            target_label = "a remaining light"
        else:
            target_pool = {self.exit}
            target_label = "the exit"

        if not target_pool:
            self.message = "The maze is quiet; there is nothing more to seek."
            return

        nearest = min(target_pool, key=lambda pos: self._distance(self.player, pos))
        direction = self._direction_description((nearest[0] - self.player[0], nearest[1] - self.player[1]))
        self._reveal_area(nearest)
        self._last_hint_turn = self.turn_count

        if direction == "here":
            self.message = f"Your lantern hums—you are already standing atop {target_label}."
        else:
            self.message = f"A faint whisper guides you {direction} toward {target_label}."

    def _format_tile(self, position: Position) -> str:
        PLAYER = "\033[96m\033[1m◉\033[0m"
        TORCH_COLORS = ["\033[93m", "\033[95m", "\033[92m", "\033[96m", "\033[91m"]
        TRAP_COLORS = ["\033[91m", "\033[95m", "\033[94m"]
        EXIT = "\033[92m◈\033[0m"
        EXIT_LOCKED = "\033[91m◈\033[0m"
        WALL = "\033[90m▓\033[0m"
        VISITED = "\033[37m·\033[0m"
        RESET = "\033[0m"
        if position not in self._discovered:
            return " "
        if position == self.player:
            return PLAYER
        if position in self._torches:
            idx = sorted(self._torches).index(position) % len(TORCH_COLORS)
            return f"{TORCH_COLORS[idx]}★{RESET}"
        if position in self._traps:
            idx = sorted(self._traps).index(position) % len(TRAP_COLORS)
            return f"{TRAP_COLORS[idx]}✖{RESET}"
        if position == self.exit:
            if self._torches:
                return EXIT_LOCKED
            return EXIT
        if self._is_wall(position):
            return WALL
        if position in self._visited:
            return VISITED
        return " "

    # -- Rendering -------------------------------------------------------
    def get_display_text(self) -> str:
        # Farben
        TITLE = "\033[95m"
        RESET = "\033[0m"
        BORDER = "\033[94m"  # Blau
        BANNER_BG = "\033[44m\033[97m"  # Weiß auf Blau
        STATUS = "\033[96m"  # Hellblau
        MSG = "\033[92m"    # Grün
        CMD = "\033[90m"    # Grau

        # ASCII-Banner mit Hintergrund (bleibt)
        banner = (
            f"{BANNER_BG} _                _                 _   _                 {RESET}\n"
            f"{BANNER_BG}| |    __ _ _ __   __| | ___  _ __ __ _| |_(_) ___  _ __  ___ {RESET}\n"
            f"{BANNER_BG}| |   / _` | '_ \\ / _` |/ _ \\| '__/ _` | __| |/ _ \\| '_ \\ / __|{RESET}\n"
            f"{BANNER_BG}| |__| (_| | | | | (_| | (_) | | | (_| | |_| | (_) | | | \\__ \\{RESET}\n"
            f"{BANNER_BG}|_____\\__,_|_| |_|\\__,_|\\___/|_|  \\__,_|\\__|_|\\___/|_| |_|___/{RESET}\n"
        )
        border = f"{BORDER}+{'-' * (self.width*2)}+{RESET}"
        rows = [banner, border]
        for y in range(self.height):
            row_tiles = [self._format_tile((x, y))*2 for x in range(self.width)]
            rows.append(f"{BORDER}|{RESET}" + "".join(row_tiles) + f"{BORDER}|{RESET}")
        rows.append(border)
        rows.append(self._describe_torches())
        # Farbige Statuszeile
        rows.append(f"{STATUS}Turns taken: {self.turn_count}    Score: {self.score}{RESET}")
        rows.append(f"{MSG}{self.message}{RESET}")
        rows.append(
            f"{CMD}Commands: W/A/S/D or arrow keys to move, H for a hint, R to restart, Q to quit.{RESET}"
        )
        return "\n".join(rows)

    # Kompass entfernt

    # -- Input handling --------------------------------------------------
    def process_command(self, command: str) -> None:
        if self.app is None:
            raise RuntimeError("Scene is not attached to an application.")

        raw_command = command
        command = command.strip().lower()
        if not command:
            self.message = MOVE_HELP_TEXT
            return

        if command in {"q", "quit", "exit"}:
            self.message = "The lantern fades as you depart the maze."
            self.app.stop()
            return

        if command in {"r", "restart"}:
            self.reset_world()
            self.message = "You reignite your lantern at the maze entrance."
            return

        if command in {"h", "hint", "?"}:
            self._hint()
            return

        move = None
        if raw_command in ARROW_KEY_MAPPING:
            move = ARROW_KEY_MAPPING[raw_command]
        elif command in {"w", "a", "s", "d"}:
            mapping = {"w": MOVES[0], "a": MOVES[1], "s": MOVES[2], "d": MOVES[3]}
            move = mapping[command]
        else:
            for candidate in MOVES:
                if command.startswith(candidate.label[0]):
                    move = candidate
                    break
        if move is None:
            self.message = f"Unknown command. {MOVE_HELP_TEXT}"
            return

        self._attempt_move(move)

    # -- Game logic ------------------------------------------------------
    def _attempt_move(self, move: Move) -> None:
        if self.app is None:
            return

        dx, dy = move.delta
        new_position = (self.player[0] + dx, self.player[1] + dy)

        # Kompass-Logik
        self._last_move = move.label

        if not self._in_bounds(new_position) or self._is_wall(new_position):
            self.message = "Your lantern reveals a solid wall in that direction."
            return

        self.player = new_position
        self.turn_count += 1
        first_visit = new_position not in self._visited
        self._visited.add(new_position)
        self._reveal_area(new_position)
        if first_visit:
            self.score += self.EXPLORATION_POINTS

        if new_position in self._traps:
            trap_msgs = [
                "A hidden trap! You are sent back to the entrance.",
                "Oops! A pitfall opens beneath you!",
                "You step on a trap and are whisked away!",
                "A magical glyph teleports you to the start!",
                "You triggered a snare! Back to the entrance."
            ]
            self.score = max(0, self.score - self.TRAP_PENALTY)
            self.message = self._random.choice(trap_msgs)
            self.player = self.start
            self._visited.add(self.player)
            self._reveal_area(self.player)
            return

        if new_position in self._torches:
            torch_msgs = [
                "You capture a wandering light! The gate grows brighter.",
                "A torch flares and joins your lantern!",
                "The wisp dances into your lantern.",
                "A glowing spark is absorbed by your lantern!",
                "You snatch a light! The maze shimmers."
            ]
            self._torches.remove(new_position)
            # Funkenregen-Animation (kurz in der Statuszeile)
            import time
            if sys.stdout.isatty():
                sparks = ["✨", "❇️", "❈", "✴️", "✳️"]
                for s in sparks:
                    print(f"\033[93m{s*8}\033[0m", end="\r", flush=True)
                    time.sleep(0.07)
                print(" "*16, end="\r", flush=True)
            self.score += self.TORCH_POINTS
            if self._torches:
                self.message = self._random.choice(torch_msgs)
            else:
                self.message = "The final light joins your lantern. The exit radiates vividly!"
            return

        if new_position == self.exit:
            if self._torches:
                self.message = "The crystalline gate remains sealed. Collect every light first."
            else:
                self.score += self.EXIT_BONUS
                self.message = (
                    f"You escape the maze in {self.turn_count} turns with a score of {self.score}!"
                )
                self.app.stop()
            return

        base = f"You move {move.label}."
        if first_visit and self._ambient_messages and self.turn_count % 3 == 0:
            ambient = self._random.choice(self._ambient_messages)
            self.message = f"{base} {ambient}"
        else:
            self.message = base

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore the glowing Lantern Maze.")
    parser.add_argument(
        "--view-radius",
        type=int,
        default=2,
        help="How far the lantern illuminates around the player (default: 2).",
    )
    parser.add_argument(
        "--torches",
        type=int,
        default=2,
        help="Number of torches to collect (default: 2).",
    )
    parser.add_argument(
        "--traps",
        type=int,
        default=2,
        help="Number of traps in the maze (default: 2).",
    )
    return parser

def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    scene = LanternMazeScene(view_radius=args.view_radius, num_torches=args.torches, num_traps=args.traps)
    app = GameApp(use_raw_input=True)
    app.push_scene(scene)
    app.run()

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

