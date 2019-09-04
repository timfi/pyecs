from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from uuid import UUID

from pyecs.components import Rigidbody2D, Transform2D
from pyecs.core import Component, ECSController

__all__ = ("register_system", "basic_physics2D")


def register_system(controller: ECSController, system: Callable, group: int = 0):
    if system.__name__ not in _SYSTEM_PREREGISTRY:
        raise KeyError(
            "'register_system' is only to be used with prebuilt systems, please use 'ECSController.register_system' instead."
        )
    target_components, name = _SYSTEM_PREREGISTRY[system.__name__]
    controller.register_system(target_components, name=name, group=group)(system)


_SYSTEM_PREREGISTRY: Dict[
    str, Tuple[Tuple[Type[Component], ...], Optional[str]]
] = dict()


def preregister_system(
    target_components: Tuple[Type[Component], ...], name: Optional[str] = None
):
    def inner(func: Callable) -> Callable:
        _SYSTEM_PREREGISTRY[func.__name__] = (target_components, name)
        return func

    return inner


@preregister_system((Transform2D, Rigidbody2D))
def basic_physics2D(
    delta_t: float,
    data: Dict[str, Any],
    components: List[Tuple[UUID, Transform2D, Rigidbody2D]],
):
    for entity_id, transform, rigidbody in components:
        rigidbody.velocity += rigidbody.acceleration * delta_t
        transform.position += rigidbody.velocity * delta_t
