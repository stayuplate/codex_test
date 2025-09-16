+from __future__ import annotations
+
+from typing import Dict, Optional, Type, TypeVar, Union, cast
+
+
+T = TypeVar("T", bound="Component")
+
+
+class Component:
+    """Base class for all components that can be attached to an :class:`Entity`."""
+
+    def __init__(self) -> None:
+        self.entity: Optional[Entity] = None
+
+    def on_added_to_scene(self, scene: object) -> None:  # pragma: no cover - default hook
+        """Called when the owning entity is added to a scene."""
+
+    def on_removed_from_scene(self) -> None:  # pragma: no cover - default hook
+        """Called when the owning entity is removed from a scene."""
+
+
+class Entity:
+    """Represents a game object that can hold a collection of components."""
+
+    def __init__(self) -> None:
+        self.scene: Optional[object] = None
+        self._components: Dict[Type[Component], Component] = {}
+
+    def add_component(self, component: T) -> T:
+        """Attach ``component`` to the entity."""
+
+        component.entity = self
+        self._components[type(component)] = component
+        if self.scene is not None:
+            component.on_added_to_scene(self.scene)
+        return component
+
+    def remove_component(self, component_or_type: Union[Type[T], T]) -> Optional[T]:
+        """Detach a component from the entity."""
+
+        if isinstance(component_or_type, Component):
+            component = component_or_type
+            component_type = type(component)
+            existing = self._components.get(component_type)
+            if existing is not component:
+                return None
+            self._components.pop(component_type, None)
+        else:
+            component = self._components.pop(component_or_type, None)
+
+        if component is None:
+            return None
+
+        if self.scene is not None:
+            component.on_removed_from_scene()
+
+        component.entity = None
+        return cast(Optional[T], component)
+
+    def has_component(self, component_type: Type[T]) -> bool:
+        return component_type in self._components
+
+    def get_component(self, component_type: Type[T]) -> Optional[T]:
+        component = self._components.get(component_type)
+        return cast(Optional[T], component)
+
+    def attach_to_scene(self, scene: object) -> None:
+        if self.scene is scene:
+            return
+
+        self.scene = scene
+        for component in self._components.values():
+            component.on_added_to_scene(scene)
+
+    def detach_from_scene(self) -> None:
+        if self.scene is None:
+            return
+
+        for component in self._components.values():
+            component.on_removed_from_scene()
+        self.scene = None
