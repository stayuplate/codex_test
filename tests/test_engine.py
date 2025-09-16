+from engine.entity import Component, Entity
+
+
+class DummyComponent(Component):
+    def __init__(self) -> None:
+        super().__init__()
+        self.removed_called = False
+
+    def on_removed_from_scene(self) -> None:
+        self.removed_called = True
+
+
+def test_remove_component_without_scene_does_not_call_hook() -> None:
+    entity = Entity()
+    component = DummyComponent()
+    entity.add_component(component)
+
+    entity.remove_component(DummyComponent)
+
+    assert not component.removed_called
