from uuid import uuid1

import pytest

from pyecs import core


class ComponentFullname(core.Component):
    ...


class ComponentA(core.Component, identifier="A"):
    ...


class ComponentB(core.Component, identifier="B"):
    ...


def test_components():
    assert ComponentFullname in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentFullname] == "ComponentFullname"
    assert "ComponentFullname" in core._COMPONENT_REGISTRY_REV
    assert core._COMPONENT_REGISTRY_REV["ComponentFullname"] == ComponentFullname

    assert ComponentA in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentA] == "A"
    assert "A" in core._COMPONENT_REGISTRY_REV
    assert core._COMPONENT_REGISTRY_REV["A"] == ComponentA

    assert ComponentB in core._COMPONENT_REGISTRY
    assert core._COMPONENT_REGISTRY[ComponentB] == "B"
    assert "B" in core._COMPONENT_REGISTRY_REV
    assert core._COMPONENT_REGISTRY_REV["B"] == ComponentB


def test_controller():
    controller = core.ECSController()

    assert controller._components == {
        component_type: dict() for component_type in core._COMPONENT_REGISTRY_REV
    }

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

    controller.delete_components(uuid_b, ComponentB, instant=True)

    assert controller._entities[uuid_b] == ["A"]
    assert uuid_b not in controller._components["B"]

    controller.delete_entity(uuid_b, instant=True)

    assert uuid_b not in controller._entities
    assert uuid_b not in controller._components["A"]

    uuid_c = uuid1()

    class UnregisteredComponent(core.Component):
        ...

    with pytest.raises(KeyError):
        # generate entity with unknown component type
        controller.add_entity(UnregisteredComponent())

    with pytest.raises(KeyError):
        # add component to unknown entity id
        controller.add_components(uuid_c, ComponentA())

    with pytest.raises(KeyError):
        # add component to entity that already has a component of that type
        controller.add_components(uuid_a, ComponentA())

    with pytest.raises(KeyError):
        # delete unknown entity
        controller.get_components(uuid_c, ComponentA)

    with pytest.raises(KeyError):
        # get component of unknown type
        controller.get_components(uuid_a, UnregisteredComponent)

    with pytest.raises(KeyError):
        # get component which doesn't exist in entity
        controller.get_components(uuid_a, ComponentB)

    with pytest.raises(KeyError):
        # delete unknown entity
        controller.delete_entity(uuid_c)

    with pytest.raises(KeyError):
        # delete component in unknown entity
        controller.delete_components(uuid_c, ComponentA)

    with pytest.raises(KeyError):
        # delete component of unknown type
        controller.delete_components(uuid_a, UnregisteredComponent)

    with pytest.raises(KeyError):
        # delete component which doesn't exist in entity
        controller.delete_components(uuid_a, ComponentB)


def test_persistant_data():

    # Test persistant data on the controller
    @core.system()
    def system1(delta_t, data):
        data["last_delta_t"] = delta_t

    @core.system()
    def system2(delta_t, data):
        assert data["last_delta_t"] == delta_t

    controller = core.ECSController()
    controller.register_system(system1)
    controller.register_system(system2)

    controller._run_system("system1", 0)
    assert "last_delta_t" in controller.data
    assert controller.data["last_delta_t"] == 0
    controller._run_system("system2", 0)


def test_systems():
    @core.system((ComponentA,))
    def system_a(delta_t, data, entities):
        # abuse delta_t to check if entities is of proper length
        assert len(entities) == delta_t
        assert all(isinstance(entity, core.EntityProxy) for entity in entities)
        assert all(len(entity.components) == 1 for entity in entities)
        assert all("A" in entity.components for entity in entities)
        assert all(isinstance(entity.A, ComponentA) for entity in entities)

    @core.system((ComponentA, ComponentB))
    def system_ab(delta_t, data, entities):
        # abuse delta_t to check if entities is of proper length
        assert len(entities) == delta_t
        assert all(len(entity.components) == 2 for entity in entities)
        assert all(
            "A" in entity.components and "B" in entity.components for entity in entities
        )
        assert all(
            isinstance(entity.A, ComponentA) and isinstance(entity.B, ComponentB)
            for entity in entities
        )

    controller = core.ECSController()
    controller.register_system(system_a)
    controller.register_system(system_ab)

    def unknown_system(delta_t, data, entities):
        ...

    with pytest.raises(KeyError):
        controller.register_system(unknown_system)

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


def test_system_precalculation():
    controller = core.ECSController()
    uuid = controller.add_entity(ComponentA())

    @core.system((ComponentA,))
    def test_system(delta_t, data, entities):
        assert len(entities) == 1
        assert entities[0].uuid == uuid

    controller.register_system(test_system)
    controller._run_system("test_system", 0)


def test_quit_exception():
    @core.system()
    def quit_timeout(delta_t, data):
        data["tick"] += 1
        if data["tick"] == 4:
            raise core.Quit

    controller = core.ECSController()
    controller.register_system(quit_timeout)
    controller["tick"] = 0

    controller.run()
    assert controller["tick"] == 4


def test_automatic_cleanup():
    @core.system((ComponentA, ComponentB))
    def delete_system(delta_t, data, entities):
        if len(entities) > 0:
            for entity in entities:
                del entity.A
                entity.delete()
                del entity.uuid
                assert not hasattr(entity, "uuid")

        else:
            raise core.Quit()

    controller = core.ECSController()
    controller.register_system(delete_system)

    uuid = controller.add_entity(ComponentA(), ComponentB())
    controller.delete_components(uuid, ComponentB)

    assert controller._entities[uuid] == ["A", "B"]
    assert controller._to_be_delete == ([], [(uuid, "B")])

    controller.delete_entity(uuid)

    assert uuid in controller._entities
    assert controller._to_be_delete == ([uuid], [(uuid, "B")])

    controller._do_cleanup()

    assert controller._to_be_delete == ([], [])
    assert uuid not in controller._entities
    assert uuid not in controller._components["A"]
    assert uuid not in controller._components["B"]

    controller.add_entity(ComponentA(), ComponentB())
    controller.run()
    assert len(controller._entities) == 0
