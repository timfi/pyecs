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


def test_systems():
    core._COMPONENT_REGISTRY = {}

    class ComponentA(core.Component, identifier="A"):
        ...

    class ComponentB(core.Component, identifier="B"):
        ...

    controller = core.ECSController()

    # Test persistant data on the controller
    @controller.register_system()
    def system1(delta_t, data):
        data["last_delta_t"] = delta_t

    @controller.register_system()
    def system2(delta_t, data):
        assert data["last_delta_t"] == delta_t

    controller._run_system("system1", 0)
    assert "last_delta_t" in controller.data
    assert controller.data["last_delta_t"] == 0
    controller._run_system("system2", 0)

    # Test entity/component collection
    @controller.register_system((ComponentA,))
    def system_a(delta_t, data, components):
        # abuse delta_t to check if components is of proper length
        assert len(components) == delta_t
        assert all(
            isinstance(component, ComponentA) for entity_id, component in components
        )

    @controller.register_system((ComponentA, ComponentB))
    def system_ab(delta_t, data, components):
        # abuse delta_t to check if components is of proper length
        assert len(components) == delta_t
        assert all(
            isinstance(component_a, ComponentA) and isinstance(component_b, ComponentB)
            for entity_id, component_a, component_b in components
        )

    controller._run_system("system_a", 0)
    controller._run_system("system_ab", 0)

    uuid_a = controller.add_entity(ComponentA())
    controller._run_system("system_a", 1)
    controller._run_system("system_ab", 0)

    uuid_b = controller.add_entity(ComponentA())
    controller._run_system("system_a", 2)
    controller._run_system("system_ab", 0)

    controller.add_components(uuid_a, ComponentB())
    controller._run_system("system_a", 2)
    controller._run_system("system_ab", 1)

    controller.add_components(uuid_b, ComponentB())
    controller._run_system("system_a", 2)
    controller._run_system("system_ab", 2)

    _ = controller.add_entity(ComponentB())
    controller._run_system("system_a", 2)
    controller._run_system("system_ab", 2)
