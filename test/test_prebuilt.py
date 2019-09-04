import pytest

from pyecs import ECSController, systems


@systems.preregister_system(tuple())
def empty_system(delta_t, data):
    ...


def test_prebuilt():
    controller = ECSController()

    systems.register_system(controller, empty_system)

    assert "empty_system" in controller._systems
    assert 0 in controller._system_groups
    assert "empty_system" in controller._system_groups[0]

    def unregistered_system(delta_t, data, entities):
        ...

    with pytest.raises(KeyError):
        systems.register_system(controller, unregistered_system)
