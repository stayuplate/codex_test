"""Lightweight, text-first utilities for building simple games.

The goal of this package is to provide just enough structure to build small
prototypes or educational projects directly from the terminal.  It exposes a
minimal scene graph, a base application runner and helper utilities tailored for
turn-based text adventures.  The intent is to act as a starting point that can
be grown into a richer engine over time.
"""

from .app import GameApp
from .game_object import GameObject
from .scene import Scene, TextScene

__all__ = ["GameApp", "GameObject", "Scene", "TextScene"]
