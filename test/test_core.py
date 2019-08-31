from ecs import core


def test_components():
    class ComponentA(core.Component):
        ...

    assert ComponentA in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentA] == "ComponentA"

    class ComponentB(core.Component, identifier="B"):
        ...

    assert ComponentB in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentB] == "B"


def test_controller():
    core._COMPONENT_REGISTRY = {}

    class ComponentA(core.Component, identifier="A"):
        ...

    class ComponentB(core.Component, identifier="B"):
        ...

    controller = core.ECSController()

    assert controller._components == {"A": dict(), "B": dict()}

    uuid_a = controller.add_entity()

    assert uuid_a in controller._entities
    assert controller._entities[uuid_a] == []

    componentA_a = ComponentA()
    controller.add_components(uuid_a, componentA_a)

    assert controller._entities[uuid_a] == ["A"]
    assert uuid_a in controller._components["A"]
    assert controller._components["A"][uuid_a] == componentA_a

    componentA_b = ComponentA()
    componentB_b = ComponentB()
    uuid_b = controller.add_entity(componentA_b, componentB_b)

    assert uuid_b in controller._entities
    assert len(controller._entities) == 2
    assert controller._entities[uuid_b] == ["A", "B"]
    assert uuid_b in controller._components["A"]
    assert controller._components["A"][uuid_b] == componentA_b
    assert uuid_b in controller._components["B"]
    assert controller._components["B"][uuid_b] == componentB_b

    controller.delete_components(uuid_b, ComponentB)

    assert controller._entities[uuid_b] == ["A"]
    assert uuid_b not in controller._components["B"]

    controller.delete_entity(uuid_b)

    assert uuid_b not in controller._entities
    assert uuid_b not in controller._components["A"]
