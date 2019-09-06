from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, cast
from uuid import UUID, uuid1

__all__ = ("ECSController", "Component", "Quit", "system")


class Quit(Exception):
    ...


@dataclass
class ECSController:
    """Controller that handles all the entity/component management and system dispatching."""

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
    _last_update: float = field(init=False, default_factory=time)
    data: Dict[str, Any] = field(init=False, default_factory=dict)
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
        entity_id = uuid1()
        self._entities[entity_id] = []
        return entity_id

    def get_entity(self, entity_id: UUID, *components: Type[Component]) -> EntityProxy:
        """Get an entity proxy correlating to an entity and some of its components

        :param entity_id: id of the target entity
        :param *components: components to collect in the proxy
        :raises KeyError: Unknown entity id
        :return: an entity proxy populated with the given components
        """
        return EntityProxy(
            uuid=entity_id,
            components=dict(
                zip(
                    [component.type() for component in components],
                    self.get_components(entity_id, *components),
                )
            ),
            _controller=self,
        )

    def delete_entity(self, entity_id: UUID, *, instant: bool = False):
        """Delete an entity from the controller.

        :param entity_id: entity to delete
        :param instant: delete immediately instead of queueing deletion, defaults to False
        :raises KeyError: Unknown entity id
        """
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        if instant:
            self._delete_entity(entity_id)
        else:
            self._to_be_delete[0].append(entity_id)

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
        :raises KeyError: Unknown component type
        :raises KeyError: Entity already has component of that type
        """
        component_type = type(component).type()
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        elif component_type not in self._components:
            raise KeyError(f"Unknown component type {component_type}")
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

    def get_components(
        self, entity_id: UUID, *components: Type[Component]
    ) -> List[Component]:
        """Get a list of components correlating to an entity

        :param entity_id: id of the target entity
        :param *components: components to collect in the proxy
        :raises KeyError: Unknown entity id
        :return: a list filled with the request components
        """
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        return [self._get_component(entity_id, component) for component in components]

    def _get_component(self, entity_id: UUID, component: Type[Component]) -> Component:
        """Get a component from an entity

        :param entity_id: id of the target entity
        :param component: component type to get
        :raises KeyError: Unknown component type
        :raises KeyError: Entity doesn't have a component of that type
        :return: the requested component
        """
        component_type = component.type()
        if component_type not in self._components:
            raise KeyError(f"Unknown component type {component_type}")
        elif component_type not in self._entities[entity_id]:
            raise KeyError(
                f"Entity {entity_id} doesn't have a component of type {component_type}"
            )
        return self._components[component_type][entity_id]

    def delete_components(
        self, entity_id: UUID, *component_types: Type[Component], instant: bool = False
    ):
        """Delete components from an entity

        :param entity_id: entity to delete component from
        :param *components: components to delete from the entity
        :param instant: delete immediately instead of queueing deletion, defaults to False
        :raises KeyError: Unknown entity id
        :raises KeyError: Unknown component type
        :raises KeyError: Entity already has component of that type
        """
        if entity_id not in self._entities:
            raise KeyError(f"Unknown entity id {entity_id}")
        for component_type in component_types:
            component_type_ = component_type.type()
            if component_type_ not in self._components:
                raise KeyError(f"Unknown component type {component_type_}")
            elif component_type_ not in self._entities[entity_id]:
                raise KeyError(
                    f"Entity {entity_id} doesn't have a component of type {component_type_}"
                )
            if instant:
                self._delete_component(entity_id, component_type_)
            else:
                self._to_be_delete[1].append((entity_id, component_type_))

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

    def register_system(self, system: Callable, group: int = 0):
        """Register a system with the controller

        :param system: the system to register with the controller
        :param group: group the system is part of, defaults to 0
        :raises KeyError: Unknown component type
        :return: a decorator to wrap the system function
        """
        if system.__name__ not in _SYSTEM_PREREGISTRY:
            raise KeyError(f"Unknown system {system.__qualname__}")
        (target_components, name) = cast(
            Tuple[List[Type[Component]], str], _SYSTEM_PREREGISTRY[system.__name__]
        )
        self._systems[name] = (
            system,
            [component.type() for component in target_components],
            list(),
        )
        self._system_groups[group].append(name)
        self._precalculate_system(name)

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
        for entity_id, component_type in component_deletions:
            self._delete_component(entity_id, component_type)
        for entity_id in entity_deletions:
            self._delete_entity(entity_id)
        self._to_be_delete = (list(), list())  # type: ignore

    def run(self):
        """Run the controller"""
        start = time()
        while True:
            try:
                delta_t = time() - start
                start = time()
                self._run_systems(delta_t)
            except Quit:
                break
            else:
                self._do_cleanup()

    def _run_systems(self, delta_t: float):
        """Run all systems.

        :param delta_t: time difference since last execution
        """
        for group in sorted(self._system_groups.keys()):
            for system in self._system_groups[group]:
                self._run_system(system, delta_t)

    def _run_system(self, name: str, delta_t: float):
        """Run a single system

        :param name: name of the system to run
        :param delta_t: time difference since last execution
        """
        func, target_components, entity_cache = self._systems[name]
        if target_components:
            entities = [
                self.get_entity(
                    entity_id,
                    *[
                        _COMPONENT_REGISTRY_REV[target_component]
                        for target_component in target_components
                    ],
                )
                for entity_id in entity_cache
            ]
            func(delta_t, self.data, entities)
        else:
            func(delta_t, self.data)


@dataclass(repr=False)
class EntityProxy:
    """Proxy object that represents a subset the component list that defines an entity."""

    _controller: ECSController
    uuid: UUID
    components: Dict[str, Component]

    def delete(self):
        """Delete the entity linked with the proxy from the controller."""
        self._controller.delete_entity(self.uuid)

    def add_component(self, component: Component):
        """Add a component to the entity linked with this proxy.

        :param component: component to add to the entity
        """
        self._controller.add_components(self.uuid, component)
        self.components[type(component).type()] = component

    def __getattribute__(self, name: str) -> Any:
        components = object.__getattribute__(self, "components")
        if name in components:
            return components[name]
        else:
            return object.__getattribute__(self, name)

    def __delattr__(self, name: str):
        if name in self.components:
            self._controller.delete_components(self.uuid, _COMPONENT_REGISTRY_REV[name])
            del self.components[name]
        else:
            super().__delattr__(name)


_COMPONENT_REGISTRY: Dict[Type[Component], str] = dict()
_COMPONENT_REGISTRY_REV: Dict[str, Type[Component]] = dict()


class Component:
    def __init_subclass__(cls, identifier: Optional[str] = None):
        super().__init_subclass__()
        name = identifier or cls.__name__
        _COMPONENT_REGISTRY[cls] = name
        _COMPONENT_REGISTRY_REV[name] = cls

    @classmethod
    def type(cls) -> str:
        return _COMPONENT_REGISTRY[cls]


_SYSTEM_PREREGISTRY: Dict[
    str, Tuple[Tuple[Type[Component], ...], Optional[str]]
] = dict()


def system(
    target_components: Tuple[Type[Component], ...] = tuple(),
    *,
    name: Optional[str] = None,
):
    """Preconfigure a system for later registrations

    :param target_components: components the system targets, defaults to empty tuple
    :param name: name of the system, defaults to the name of the system function
    """

    def inner(func: Callable) -> Callable:
        _SYSTEM_PREREGISTRY[func.__name__] = (target_components, name or func.__name__)
        return func

    return inner
