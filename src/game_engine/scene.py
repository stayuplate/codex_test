# scene.py
# Platzhalter für Scene-Klasse oder verwandte Logik



class Scene:
    def __init__(self, name: str = "Scene"):
        self.name = name

    def on_exit(self) -> None:
        pass

    def handle_input(self) -> bool:
        return True

    def update(self, delta_time: float) -> None:
        pass

class TextScene(Scene):
    def __init__(self, name: str = "TextScene", prompt: str = "> ", color: str = "\033[96m", border: bool = True, icon: str = "🕹️"):
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
            user_input = input(f"{self.color}{self.prompt}\033[0m ")
            self.process_command(user_input)
            return True
        print(f"{self.color}[DEBUG] process_command nicht vorhanden\033[0m")
        return False

    def update(self, delta_time: float) -> None:
        # Standardmäßig keine Logik, kann von Kindklassen überschrieben werden
        pass
