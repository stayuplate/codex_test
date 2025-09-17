from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from .app import GameApp


class Scene:
    def __init__(self, name: str = "Scene"):
        self.name = name
        self.app: Optional[GameApp] = None

    def on_enter(self) -> None:
        """Hook invoked when the scene is pushed onto a GameApp; override if needed."""
        pass

    def render(self) -> None:
        """Hook used by GameApp to draw the active scene; override in subclasses."""
        pass

    def on_exit(self) -> None:
        pass

    def handle_input(self) -> bool:
        return True

    def update(self, delta_time: float) -> None:
        pass

class TextScene(Scene):
    def __init__(
        self,
        name: str = "TextScene",
        prompt: str = "> ",
        color: str = "\033[96m",
        border: bool = True,
        icon: str = "🕹️",
    ):
        super().__init__(name=name)
        self.prompt = prompt
        self.color = color  # ANSI-Farbe für Szenentitel/Text
        self.border = border  # Rahmen um Szene
        self.icon = icon  # Icon für Szenentitel

    def render(self) -> None:
        # Bildschirm löschen (funktioniert in den meisten Terminals)
        print("\033[2J\033[H", end="")
        # Szenentitel mit Farbe und Icon
        title = f"{self.color}{self.icon} {self.name} {self.icon}\033[0m"
        if self.border:
            border_line = f"{self.color}" + "═" * (len(self.name) + 8) + "\033[0m"
            print(border_line)
            print(title)
            print(border_line)
        else:
            print(title)
        # Szenentext
        if hasattr(self, "get_display_text"):
            text = self.get_display_text()
            # Optional: Text farbig
            print(f"{self.color}{text}\033[0m")
        else:
            print(f"{self.color}[DEBUG] get_display_text nicht vorhanden\033[0m")

    def handle_input(self) -> bool:
        # Liest Benutzereingabe und verarbeitet sie, falls process_command existiert
        if hasattr(self, "process_command"):
            # Farbiges Prompt
            prompt = f"{self.color}{self.prompt}\033[0m "
            app = self.app
            if app is not None:
                user_input = app.get_input(prompt)
            else:
                user_input = input(prompt)
            self.process_command(user_input)
            return True
        print(
            f"{self.color}[DEBUG] process_command nicht vorhanden,"
            f" delegiere an Scene.handle_input()\033[0m"
        )
        return super().handle_input()

    def update(self, delta_time: float) -> None:
        # Standardmäßig keine Logik, kann von Kindklassen überschrieben werden
        pass
