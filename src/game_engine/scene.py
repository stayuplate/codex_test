"""Scene implementations for the lightweight game engine."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .game_object import GameObject


class Scene:
    """Base class representing a collection of game objects.

    Scenes are responsible for orchestrating the update and render flow of their
    game objects.  They can also respond to user input by overriding
    :meth:`handle_input`.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self.app = None  # Assigned when the scene is pushed onto a GameApp
        self._objects: List[GameObject] = []

    # -- Scene lifecycle -------------------------------------------------
    def on_enter(self) -> None:
        """Hook that is invoked when the scene becomes active."""

    def on_exit(self) -> None:
        """Hook that is invoked when the scene is removed from the stack."""

    # -- Input handling --------------------------------------------------
    def handle_input(self) -> bool:
        """Handle user input.

        Returning ``False`` will skip the rest of the frame (``update`` and
        ``render``).  The default implementation simply continues with the
        frame.
        """

        return True

    # -- Game loop -------------------------------------------------------
    def update(self, delta_time: float) -> None:
        """Update all active game objects."""

        for obj in list(self._objects):
            if obj.active:
                obj.update(delta_time)

    def render(self) -> None:
        """Render all active game objects."""

        for obj in list(self._objects):
            if obj.active:
                obj.render()

    # -- Game object management -----------------------------------------
    def add_object(self, obj: GameObject) -> GameObject:
        """Attach *obj* to the scene."""

        obj.scene = self
        self._objects.append(obj)
        obj.on_added(self)
        return obj

    def add_objects(self, objects: Iterable[GameObject]) -> None:
        for obj in objects:
            self.add_object(obj)

    def remove_object(self, obj: GameObject) -> None:
        if obj in self._objects:
            self._objects.remove(obj)
            obj.on_removed(self)
            obj.scene = None

    def clear_objects(self) -> None:
        for obj in list(self._objects):
            self.remove_object(obj)


class TextScene(Scene):
    """Helper scene tailored for turn-based text adventures."""

    def __init__(self, name: Optional[str] = None, *, prompt: str = "> ", auto_clear: bool = True) -> None:
        super().__init__(name=name)
        self.prompt = prompt
        self.auto_clear = auto_clear

    def get_display_text(self) -> str:
        """Return the textual representation of the current scene state."""

        raise NotImplementedError("TextScene subclasses must implement get_display_text().")

    def process_command(self, command: str) -> None:
        """Handle a user-entered command."""

        raise NotImplementedError("TextScene subclasses must implement process_command().")

    def handle_input(self) -> bool:
        if self.app is None:
            raise RuntimeError("Scene is not attached to an application.")

        command = self.app.get_input(self.prompt)
        self.process_command(command)
        return True

    def render(self) -> None:
        if self.app is None:
            return

        if self.auto_clear:
            self.app.clear()
        self.app.display(self.get_display_text())
