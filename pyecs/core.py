from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar
from uuid import UUID
from uuid import uuid4 as get_uuid

__all__ = ("ECSManager", "Entity")


C = TypeVar("C")


class Entity:
    __slots__ = ("_manager", "_uuid")
    _manager: ECSManager
    _uuid: UUID

    def __init__(self, manager: ECSManager, uuid: UUID):
        self._manager = manager
        self._uuid = uuid

    def __repr__(self) -> str:
        return f"Entity(uuid={self._uuid})"

    __str__ = __repr__

    @property
    def uuid(self):
        """Identifier of this entity in the ECSManager."""
        return self._uuid

    def get_children(self) -> Tuple[Entity, ...]:
        """Retrieve child entities."""
        return self._manager.get_children(self.uuid)

    def get_parent(self) -> Optional[Entity]:
        """Retrieve parent entity."""
        return self._manager.get_parent(self.uuid)

    def add_components(self, *components: Any):
        """Add components to entity."""
        self._manager.add_components(self.uuid, *components)

    def get_component(self, c_type: Type[C]) -> C:
        """Get component from entity."""
        return self._manager.get_component(self.uuid, c_type)

    def get_components(self, *c_types: type) -> Tuple[Any, ...]:
        """Get components from entity."""
        return self._manager.get_components(self.uuid, *c_types)

    def remove_components(self, *c_types: type):
        """Remove component from entity."""
        self._manager.remove_components(self.uuid, *c_types)

    def remove(self):
        """Remove entity from ECSManager."""
        self._manager.remove_entity(self.uuid)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entity) and self.uuid == other.uuid


class ECSManager:
    __slots__ = (
        "entities",
        "entity_hirarchy",
        "entity_hirarchy_rev",
        "components",
        "systems",
        "system_groups",
        "misc_cache",
    )

    entities: Dict[UUID, Set[str]]
    entity_hirarchy: Dict[UUID, Set[UUID]]
    entity_hirarchy_rev: Dict[UUID, Optional[UUID]]
    components: Dict[str, Dict[UUID, Any]]
    systems: List[Callable[[ECSManager], None]]
    system_groups: Dict[int, List[int]]
    misc_cache: Dict[str, Any]

    def __init__(self):
        self.entities = {}
        self.entity_hirarchy = {}
        self.entity_hirarchy_rev = {}
        self.components = defaultdict(dict)
        self.systems = []
        self.system_groups = defaultdict(list)
        self.misc_cache = {}

    def clear_cache(self):
        """Clear LRU and misc caches."""
        self.get_component.cache_clear()
        self.get_components.cache_clear()
        self.get_entity.cache_clear()
        self.get_entities_with.cache_clear()
        self.get_unpacked_entities_with.cache_clear()
        self.get_children.cache_clear()
        self.get_parent.cache_clear()
        self.misc_cache.clear()

    def clear(self):
        """Delete all data."""
        self.clear_cache()
        self.entities.clear()
        self.entity_hirarchy.clear()
        self.entity_hirarchy_rev.clear()
        self.components.clear()
        self.system_groups.clear()
        self.systems = []

    def add_entity(
        self,
        *components: Any,
        parent: Optional[Entity] = None,
        uuid: Optional[UUID] = None,
    ) -> Entity:
        if uuid and uuid in self.entities:
            raise KeyError("Entity uuid collision.")
        uuid = uuid or get_uuid()

        self.entity_hirarchy[uuid] = set()
        if parent is not None:
            self.entity_hirarchy[parent.uuid] |= {uuid}
            self.entity_hirarchy_rev[uuid] = parent.uuid
        else:
            self.entity_hirarchy_rev[uuid] = None

        self.entities[uuid] = set()
        self.add_components(uuid, *components)
        return Entity(self, uuid)

    def add_components(self, uuid: UUID, *components: Any):
        for component in components:
            c_name = type(component).__qualname__
            self.entities[uuid] |= {c_name}
            self.components[c_name][uuid] = component

        self.clear_cache()

    @lru_cache
    def get_component(self, uuid: UUID, c_type: Type[C]) -> C:
        return self.components[c_type.__qualname__][uuid]  # type: ignore

    @lru_cache
    def get_components(self, uuid: UUID, *c_types: type) -> Tuple[Any, ...]:
        if c_types:
            return tuple(self.get_component(uuid, c_type) for c_type in c_types)
        else:
            return tuple(
                self.components[c_name][uuid] for c_name in self.entities[uuid]
            )

    @lru_cache
    def get_entity(self, uuid: UUID) -> Entity:
        if uuid in self.entities:
            return Entity(self, uuid)
        else:
            raise KeyError("Unknown entity id.")

    @lru_cache
    def get_entities_with(self, *c_types: type) -> Tuple[Entity, ...]:
        target_c_names = {c_type.__qualname__ for c_type in c_types}
        return tuple(
            self.get_entity(uuid)
            for uuid, c_names in self.entities.items()
            if target_c_names <= c_names
        )

    @lru_cache
    def get_unpacked_entities_with(self, *c_types: type) -> Tuple[Tuple[Any, ...], ...]:
        target_c_names = {c_type.__qualname__ for c_type in c_types}
        return tuple(
            tuple(self.get_component(uuid, c_type) for c_type in c_types)
            for uuid, c_names in self.entities.items()
            if target_c_names <= c_names
        )

    @lru_cache
    def get_children(self, uuid: UUID) -> Tuple[Entity, ...]:
        return tuple(Entity(self, c_uuid) for c_uuid in self.entity_hirarchy[uuid])

    @lru_cache
    def get_parent(self, uuid: UUID) -> Optional[Entity]:
        return (
            Entity(self, p_uuid)
            if (p_uuid := self.entity_hirarchy_rev.get(uuid))
            else None
        )

    def remove_components(self, uuid: UUID, *c_types: type):
        self.entities[uuid] -= {c_type.__qualname__ for c_type in c_types}
        for c_type in c_types:
            del self.components[c_type.__qualname__][uuid]
        self.clear_cache()

    def remove_entity(self, uuid: UUID):
        for c_name in self.entities.pop(uuid, ()):
            del self.components[c_name][uuid]

        if (p_uuid := self.entity_hirarchy_rev.pop(uuid)) :
            self.entity_hirarchy[p_uuid] -= {uuid}

        for c_uuid in [*self.entity_hirarchy[uuid]]:
            self.remove_entity(c_uuid)

        del self.entity_hirarchy[uuid]

        self.clear_cache()

    def add_system(self, sys: Callable[[ECSManager], None], *, group: int = 0):
        self.systems.append(sys)
        self.system_groups[group].append(len(self.systems) - 1)

    def add_systems(self, *sys: Callable[[ECSManager], None], group: int = 0):
        for s in sys:
            self.add_system(s, group=group)

    def tick_systems(self, *, group: Optional[int] = None):
        systems = (
            self.systems
            if group is None
            else (self.systems[sys_id] for sys_id in self.system_groups[group])
        )

        for system in systems:
            system(self)

    def __hash__(self):
        return id(self)
