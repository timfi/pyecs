from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from uuid import UUID, uuid4

__all__ = ("ECSController", "Component")


@dataclass
class ECSController:
    _entities: Dict[UUID, List[str]] = field(init=False, default_factory=dict)
    _components: Dict[str, Dict[UUID, Component]] = field(
        init=False, default_factory=dict
    )
    _systems: Dict[str, Tuple[Callable, List[str], List[UUID]]] = field(
        init=False, default_factory=dict
    )
    _system_groups: Dict[int, List[str]] = field(
        init=False, default_factory=lambda: defaultdict(list)
    )
    _to_be_delete: Tuple[List[UUID], List[Tuple[UUID, str]]] = field(  # type: ignore
        init=False, default=(list(), list())
    )
    data: Dict[str, Any] = field(init=False, default_factory=dict)
    delay_cleanup: bool = False
    time_per_cycle: float = 1 / 60

    def __post_init__(self):
        for component_type in _COMPONENT_REGISTRY:
            self._components[component_type.type()] = dict()

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value

    def add_entity(self, *components: Component) -> UUID:
        """Add a single entity to the controller.

        *Public interface for `_add_entity`*

        :param *components: components to add to the entity
        :return: entity id
        """
        entity_id = self._add_entity()
        self.add_components(entity_id, *components)
        return entity_id

    def _add_entity(self) -> UUID:
        """Generate a unique entity id and setup component type cache for it.

        :return: entity id
        """
        entity_id = uuid4()
        while entity_id in self._entities:
            entity_id = uuid4()
        self._entities[entity_id] = []
        return entity_id

    def delete_entity(self, entity_id: UUID):
        """Delete an entity from the controller.

        :param entity_id: entity to delete
        :raises KeyError: Unknown entity id
        """
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        if self.delay_cleanup:
            self._to_be_delete[0].append(entity_id)
        else:
            self._delete_entity(entity_id)

    def _delete_entity(self, entity_id: UUID):
        """Actually delete an entity from the controller

        :param entity_id: entity to delete
        """
        for component_type in self._entities[entity_id]:
            self._delete_component(entity_id, component_type)
        del self._entities[entity_id]

    def add_components(self, entity_id: UUID, *components: Component):
        """Add components to an existing entity.

        *Public interface for `_add_component`*

        :param entity_id: id of the entity to add the components to
        :param *components: components to add to the entity
        """
        for component in components:
            self._add_component(entity_id, component)

    def _add_component(self, entity_id: UUID, component: Component):
        """Add a component to an existing entity.

        :param entity_id: id of the entity to add the component to
        :param component: component to add to the entity
        :raises KeyError: Unknown entity id
        :raises TypeError: Unknown component type
        :raises KeyError: Entity already has component of that type
        """
        component_type = type(component).type()
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        elif component_type not in self._components:
            raise TypeError(f"Unknown component type {component_type}")
        elif component_type in self._entities[entity_id]:
            raise KeyError(
                f"Entity {entity_id} already has a component of type {component_type}"
            )
        self._entities[entity_id].append(component_type)
        self._components[component_type][entity_id] = component

        # calculate which systems will access the entity based on the change
        for _, target_components, entity_cache in self._systems.values():
            if (
                entity_id not in entity_cache
                and component_type in target_components
                and all(
                    target_component in self._entities[entity_id]
                    for target_component in target_components
                )
            ):
                entity_cache.append(entity_id)

    def delete_components(self, entity_id: UUID, *component_types: Type[Component]):
        """Delete components from an entity

        :param entity_id: entity to delete component from
        :param *components: components to delete from the entity
        :raises KeyError: Unknown entity id
        :raises TypeError: Unknown component type
        :raises KeyError: Entity already has component of that type
        """
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        for component_type in component_types:
            component_type_ = component_type.type()
            if component_type_ not in self._components:
                raise TypeError(f"Unknown component type {component_type_}")
            elif component_type_ not in self._entities[entity_id]:
                raise KeyError(
                    f"Entity {entity_id} doesn't have a component of type {component_type_}"
                )
            if self.delay_cleanup:
                self._to_be_delete[1].append((entity_id, component_type_))
            else:
                self._delete_component(entity_id, component_type_)

    def _delete_component(self, entity_id: UUID, component_type: str):
        """Actually delete a component from an entity

        :param entity_id: entity to delete component from
        :param component: component to delete to the entity
        """
        del self._components[component_type][entity_id]
        del self._entities[entity_id][self._entities[entity_id].index(component_type)]
        for _, target_components, entity_cache in self._systems.values():
            if component_type in target_components and entity_id in entity_cache:
                del entity_cache[entity_cache.index(entity_id)]

    def register_system(
        self,
        target_components: Tuple[Type[Component], ...],
        name: Optional[str] = None,
        group: int = 0,
    ) -> Callable[[Callable], Callable]:
        """Register a system with the controller

        :param target_components: components the system targets
        :param name: name of the system, defaults to the name of the system function
        :param group: group the system is part of, defaults to 0
        :return: a decorator to wrap the system function
        """

        def inner_register_system(func: Callable) -> Callable:
            name_ = name or func.__name__
            self._systems[name_] = (
                func,
                [component.type() for component in target_components],
                list(),
            )
            self._system_groups[group].append(name_)
            self._precalculate_system(name_)
            return func

        return inner_register_system

    def _precalculate_system(self, name: str):
        """Calculate the entity cache of a system

        :param name: system to calculate the cache for
        """
        _, target_components, entity_cache = self._systems[name]
        for entity_id, component_types in self._entities.items():
            if entity_id not in entity_cache and all(
                target_component in component_types
                for target_component in target_components
            ):
                entity_cache.append(entity_id)

    def _do_cleanup(self):
        """Do cleanup that was cached so far."""
        entity_deletions, component_deletions = self._to_be_delete
        for entity_id in entity_deletions:
            self._delete_entity(entity_id)
        for entity_id, component_type in component_deletions:
            self._delete_component(entity_id, component_type)
        self._to_be_delete = (list(), list())  # type: ignore

    def run(self):
        start = time()
        while True:
            delta_t = start - time()
            start = time()
            self._run_systems(delta_t)

    def _run_systems(self, delta_t: float):
        for group in sorted(self._system_groups.keys()):
            for system in self._system_groups[group]:
                self._run_system(system, delta_t)

    def _run_system(self, name: str, delta_t: float):
        func, target_components, entity_cache = self._systems[name]
        func(
            delta_t,
            self.data,
            *[
                tuple(
                    self._components[target_component][entity_id]
                    for target_component in target_components
                )
                for entity_id in entity_cache
            ],
        )


_COMPONENT_REGISTRY: Dict[Type[Component], str] = dict()


class Component:
    def __init_subclass__(cls, identifier: Optional[str] = None):
        super().__init_subclass__()
        _COMPONENT_REGISTRY[cls] = identifier or cls.__name__

    @classmethod
    def type(cls) -> str:
        return _COMPONENT_REGISTRY[cls]
