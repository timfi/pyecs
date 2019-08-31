from ecs import core


def test_components():
    class ComponentA(core.Component):
        ...

    assert ComponentA in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentA] == "ComponentA"

    class ComponentB(core.Componnent, identifier="B"):
        ...

    assert ComponentB in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentA] == "B"
