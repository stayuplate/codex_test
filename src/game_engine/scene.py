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
    def __init__(self, name: str = "TextScene", prompt: str = "> "):
        super().__init__(name=name)
        self.prompt = prompt

    def render(self) -> None:
        print("[DEBUG] render() aufgerufen")
        # Bildschirm löschen (funktioniert in den meisten Terminals)
        print("\033[2J\033[H", end="")
        # Gibt den Text der Szene aus, falls get_display_text existiert
        if hasattr(self, "get_display_text"):
            print(self.get_display_text())
        else:
            print("[DEBUG] get_display_text nicht vorhanden")

    def handle_input(self) -> bool:
        print("[DEBUG] handle_input() aufgerufen")
        # Liest Benutzereingabe und verarbeitet sie, falls process_command existiert
        if hasattr(self, "process_command"):
            command = input("> ")
            print(f"[DEBUG] Eingabe erhalten: {command}")
            self.process_command(command)
            return True
        print("[DEBUG] process_command nicht vorhanden")
        return False

    def update(self, delta_time: float) -> None:
        # Standardmäßig keine Logik, kann von Kindklassen überschrieben werden
        pass
