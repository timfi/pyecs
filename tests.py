from uuid import uuid1

import pytest

from pyecs import Store


class ComponentA:
    ...


class ComponentB:
    ...


def test_entity_component_workflow():
    store = Store()

    ca = ComponentA()
    e = store.add_entity(ca)

    _e = store.get_entity(e.uuid)
    assert e == _e
    _e, *_ = store.get_entities()
    assert e == _e

    with pytest.raises(KeyError):
        store.get_entity(uuid1())

    assert e.get_component(ComponentA) == ca
    assert e.get_components(ComponentA) == (ca,)
    assert e.get_components() == (ca,)

    assert e.get_component(ComponentA) == store.get_component(e.uuid, ComponentA)
    assert e.get_components(ComponentA) == store.get_components(e.uuid, ComponentA)
    assert e.get_components() == store.get_components(e.uuid)

    with pytest.raises(KeyError):
        e.get_component(ComponentB)
    with pytest.raises(KeyError):
        e.get_components(ComponentB)

    cb = ComponentB()
    e.add_components(cb)

    assert e.get_components(ComponentA, ComponentB) == (ca, cb)
    assert e.get_components(ComponentB, ComponentA) == (cb, ca)
    assert e.get_components() in [(ca, cb), (cb, ca)]

    assert e.get_components(ComponentA, ComponentB) == store.get_components(
        e.uuid, ComponentA, ComponentB
    )
    assert e.get_components(ComponentB, ComponentB) == store.get_components(
        e.uuid, ComponentB, ComponentB
    )
    assert e.get_components() == store.get_components(e.uuid)

    _e1, (_ca1,) = store.get_entities_with(ComponentA)[0]
    _e2, (_cb1,) = store.get_entities_with(ComponentB)[0]
    _e3, (_ca2, _cb2) = store.get_entities_with(ComponentA, ComponentB)[0]

    assert e == _e1
    assert _e1 == _e2
    assert _e2 == _e3
    assert _ca1 == ca and _cb1 == cb
    assert _ca2 == ca and _cb2 == cb

    e.remove_components(ComponentA)

    with pytest.raises(KeyError):
        e.get_component(ComponentA)

    with pytest.raises(KeyError):
        e.get_components(ComponentA)

    assert e.get_component(ComponentB) == cb
    assert e.get_components(ComponentB) == (cb,)
    assert not store.get_entities_with(ComponentA)

    with pytest.raises(KeyError):
        store.add_entity(uuid=e.uuid)

    e.remove()
    assert not store.get_entities_with(ComponentB)

    store.clear()


def test_entity_tree():
    store = Store()

    p = store.add_entity()
    e = p.add_child()

    assert e.get_parent() == p
    assert p.get_children() == (e,)

    e.remove()
    assert p == store.get_entity(p.uuid)

    e = store.add_entity(parent=p)
    p.remove()
    with pytest.raises(KeyError):
        store.get_entity(e.uuid)

    store.clear()

    p = store.add_entity()
    p.add_child()

    c1 = ComponentA()
    e1 = p.add_child(c1)
    r1 = (e1, (c1,))

    c2 = ComponentA()
    e2 = p.add_child(c2, ComponentB())
    r2 = (e2, (c2,))

    assert p.get_children_with(ComponentA) in [(r1, r2), (r2, r1)]


def test_delayed_removals():
    store = Store()

    ca = ComponentA()
    e1 = store.add_entity(ca)
    e2 = store.add_entity()

    e1.remove_components(ComponentA, delay=True)
    e2.remove(delay=True)

    assert ca == e1.get_component(ComponentA)
    assert e2 == store.get_entity(e2.uuid)

    store.apply_removals()

    with pytest.raises(KeyError):
        e1.get_component(ComponentA)

    with pytest.raises(KeyError):
        store.get_entity(e2.uuid)

    store.clear()

    ca = ComponentA()
    e1 = store.add_entity(ca)

    e1.remove_components(ComponentA, delay=True)
    e1.remove(delay=True)

    store.apply_removals()
