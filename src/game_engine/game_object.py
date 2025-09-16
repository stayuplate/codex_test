"""Core building blocks for the game engine.

This module currently exposes a small :class:`GameObject` base class that can
be used by games or scenes to model entities that participate in the update
cycle.  The implementation is intentionally lightweight so it can operate in a
text-based environment without any external dependencies.  The class is
 designed to be extended by gameplay code and does not enforce a specific
rendering strategy.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only used for typing information
    from .scene import Scene


class GameObject:
    """Base class for entities that live inside a :class:`Scene`.

    The default implementation is intentionally small; derived classes are
    expected to override :meth:`update` and/or :meth:`render` to implement their
    behaviour.  The ``active`` flag can be toggled to temporarily disable an
    object without removing it from the scene.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self.scene: Optional["Scene"] = None
        self.active: bool = True

    # Lifecycle hooks -------------------------------------------------
    def on_added(self, scene: "Scene") -> None:
        """Called once the object has been attached to *scene*.

        Sub-classes can override this hook to perform initialisation that
        depends on the owning scene.
        """

    def on_removed(self, scene: "Scene") -> None:
        """Called when the object is removed from *scene*."""

    # Game loop hooks -------------------------------------------------
    def update(self, delta_time: float) -> None:
        """Advance the state of the object by ``delta_time`` seconds."""

    def render(self) -> None:
        """Render the object.

        For text-based games the default implementation does nothing.  It is up
        to sub-classes to decide how to present themselves to the player.
        """
