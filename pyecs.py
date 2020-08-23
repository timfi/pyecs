"""Entity-Component Store."""
from __future__ import annotations

from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)
from uuid import UUID
from uuid import uuid4 as get_uuid

F = TypeVar("F", bound=Callable)
if TYPE_CHECKING:

    def lru_cache(f: F) -> F:  # noqa
        ...


else:
    from functools import lru_cache


__version__ = "0.14"
__all__ = ("Store", "Entity")


C = TypeVar("C")


class Entity:
    """A wrapper around an entity-uuid and entity-component store."""

    __slots__ = ("_store", "_uuid")
    _store: Store
    _uuid: UUID

    def __init__(self, store: Store, uuid: UUID):  # noqa
        self._store = store
        self._uuid = uuid

    def __repr__(self) -> str:  # noqa
        return f"Entity(uuid={self._uuid})"

    __str__ = __repr__

    @property
    def uuid(self):  # noqa
        """Identifier of this entity in the Store."""
        return self._uuid

    def __eq__(self, other: Any) -> bool:  # noqa
        return isinstance(other, Entity) and self.uuid == other.uuid

    def add_child(self, *components: Any, uuid: Optional[UUID] = None) -> Entity:
        """Create child entity.

        :param *components: Any: Components to add to the entity.
        :param uuid: Optional[UUID]: Override UUID, if given this skips the automatic
                                     UUID generation. (Default value = None)

        """
        return self._store.add_entity(*components, parent=self, uuid=uuid)

    def add_components(self, *components: Any):
        """Add components to entity.

        :param *components: Any: Components to add to the entity.

        """
        self._store.add_components(self.uuid, *components)

    def get_component(self, c_type: Type[C]) -> C:
        """Get a single component from entity.

        :param c_type: Type[C]: Type of the component to get from the entity.

        """
        return self._store.get_component(self.uuid, c_type)

    def get_components(self, *c_types: type) -> Tuple[Any, ...]:
        """Get multiple components from entity.

        :param *c_types: type: Types of the components to get from the entity,
                               the result will be in the order these types are given.

        """
        return self._store.get_components(self.uuid, *c_types)

    def get_parent(self) -> Optional[Entity]:
        """Get parent entity."""
        return self._store.get_parent(self.uuid)

    def get_children(self) -> Tuple[Entity, ...]:
        """Get all child entities."""
        return self._store.get_children(self.uuid)

    def get_children_with(
        self, *c_types: type
    ) -> Tuple[Tuple[Entity, Tuple[Any, ...]], ...]:
        """Get all children with the given components.

        :param *c_types: type: Types of the components the entities should have.

        """
        return self._store.get_children_with(self.uuid, *c_types)

    def remove_components(self, *c_types: type, delay: bool = False):
        """Remove component from entity.

        :param *c_types: type: Types of the components to remove from the entity.
        :param delay: bool: Delay the removal of the components until `Store.apply_removals`
                            is called. (Default value = False)

        """
        self._store.remove_components(self.uuid, *c_types, delay=delay)

    def remove(self, *, delay: bool = False):
        """Remove entity from Store.

        :param delay: bool: Delay the removal of this entity until `Store.apply_removals`
                            is called. (Default value = False)

        """
        self._store.remove_entity(self.uuid, delay=delay)


class Store:
    """Entity-Component Store/Controller/Mapper."""

    __slots__ = (
        "entities",
        "entity_hirarchy",
        "entity_hirarchy_rev",
        "components",
        "entity_delete_buffer",
        "component_delete_buffer",
    )

    entities: Dict[UUID, Set[str]]
    entity_hirarchy: Dict[UUID, Set[UUID]]
    entity_hirarchy_rev: Dict[UUID, Optional[UUID]]
    components: Dict[str, Dict[UUID, Any]]
    entity_delete_buffer: Set[UUID]
    component_delete_buffer: Set[Tuple[UUID, type]]

    def __init__(self):  # noqa
        self.entities = {}
        self.entity_hirarchy = {}
        self.entity_hirarchy_rev = {}
        self.components = defaultdict(dict)
        self.entity_delete_buffer = set()
        self.component_delete_buffer = set()

    def __hash__(self):  # noqa
        return id(self)

    def clear_cache(self):
        """Clear LRU and misc caches."""
        self.get_components.cache_clear()
        self.get_entities_with.cache_clear()

    def clear(self):
        """Delete all data."""
        self.clear_cache()
        self.entities.clear()
        self.entity_hirarchy.clear()
        self.entity_hirarchy_rev.clear()
        self.components.clear()
        self.entity_delete_buffer.clear()
        self.component_delete_buffer.clear()

    def add_entity(
        self,
        *components: Any,
        parent: Optional[Entity] = None,
        uuid: Optional[UUID] = None,
    ) -> Entity:
        """Add entity to store.

        :param *components: Any: Components to add to the entity.
        :param parent: Optional[Entity]: Entity to register as a parent
                                         entity. (Default value = None)
        :param uuid: Optional[UUID]: Override UUID, if given this skips the automatic
                                     UUID generation. (Default value = None)

        """
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
        """Add components to an existing entity.

        :param uuid: UUID: UUID of the entity to add the components to.
        :param *components: Any: Components to add to the entity.

        """
        for component in components:
            c_name = type(component).__qualname__
            self.entities[uuid] |= {c_name}
            self.components[c_name][uuid] = component

        self.clear_cache()

    def get_component(self, uuid: UUID, c_type: Type[C]) -> C:
        """Get a single component from an entity.

        :param uuid: UUID: UUID of the entity to get the component from.
        :param c_type: Type[C]: Type of the component to get from the entity.

        """
        return self.components[c_type.__qualname__][uuid]  # type: ignore

    @lru_cache
    def get_components(self, uuid: UUID, *c_types: type) -> Tuple[Any, ...]:
        """Get multiple component from an entity.

        :param uuid: UUID: UUID of the entity to get the components from.
        :param *c_types: type: Types of the components to get from the entity,
                               the result will be in the order these types are given.

        """
        if c_types:
            return tuple(self.get_component(uuid, c_type) for c_type in c_types)
        else:
            return tuple(
                self.components[c_name][uuid] for c_name in self.entities[uuid]
            )

    def get_entity(self, uuid: UUID) -> Entity:
        """Get an entity for a given UUID.

        :param uuid: UUID: UUID of the entity to get.

        """
        if uuid in self.entities:
            return Entity(self, uuid)
        else:
            raise KeyError("Unknown entity id.")

    def get_entities(self) -> Tuple[Entity, ...]:
        """Get all entities in this store."""
        return tuple(Entity(self, uuid) for uuid in self.entities)

    @lru_cache
    def get_entities_with(
        self, *c_types: type
    ) -> Tuple[Tuple[Entity, Tuple[Any, ...]], ...]:
        """Get all entities with the given components.

        :param *c_types: type: Types of the components the entities should have.

        """
        target_c_names = {c_type.__qualname__ for c_type in c_types}
        return tuple(
            (self.get_entity(uuid), self.get_components(uuid, *c_types))
            for uuid, c_names in self.entities.items()
            if target_c_names <= c_names
        )

    def get_children(self, uuid: UUID) -> Tuple[Entity, ...]:
        """Get children of an entity.

        :param uuid: UUID: UUID of the entity to get the children for.

        """
        return tuple(Entity(self, c_uuid) for c_uuid in self.entity_hirarchy[uuid])

    @lru_cache
    def get_children_with(
        self, uuid: UUID, *c_types: type
    ) -> Tuple[Tuple[Entity, Tuple[Any, ...]], ...]:
        """Get all children of an entity with the given components.

        :param *c_types: type: Types of the components the entities should have.

        """
        target_c_names = {c_type.__qualname__ for c_type in c_types}
        return tuple(
            (self.get_entity(c_uuid), self.get_components(c_uuid, *c_types))
            for c_uuid in self.entity_hirarchy[uuid]
            if target_c_names <= self.entities[c_uuid]
        )

    def get_parent(self, uuid: UUID) -> Optional[Entity]:
        """Get parent of an entity.

        :param uuid: UUID: UUID of the entity to get the parent for.

        """
        return (
            Entity(self, p_uuid)
            if (p_uuid := self.entity_hirarchy_rev.get(uuid))
            else None
        )

    def _remove_component(self, uuid: UUID, c_type: type):  # noqa
        self.entities[uuid] -= {c_type.__qualname__}
        del self.components[c_type.__qualname__][uuid]

    def remove_components(self, uuid: UUID, *c_types: type, delay: bool = False):
        """Remove components from an entity.

        :param uuid: UUID: UUID of the entity to remove the components from.
        :param *c_types: type: Types of the components to remove from the entity.
        :param delay: bool: Delay the removal of the components until `Store.apply_removals`
                            is called. (Default value = False)

        """
        if delay:
            for c_type in c_types:
                self.component_delete_buffer.add((uuid, c_type))
        else:
            for c_type in c_types:
                self._remove_component(uuid, c_type)
            self.clear_cache()

    def _remove_entity(self, uuid: UUID):  # noqa
        for c_name in self.entities.pop(uuid, ()):
            del self.components[c_name][uuid]

        if (p_uuid := self.entity_hirarchy_rev.pop(uuid)) :
            self.entity_hirarchy[p_uuid] -= {uuid}

        for c_uuid in [*self.entity_hirarchy[uuid]]:
            self.remove_entity(c_uuid)

        del self.entity_hirarchy[uuid]

    def remove_entity(self, uuid: UUID, *, delay: bool = False):
        """Remove an entity.

        :param uuid: UUID: UUID of the entity to remove.
        :param delay: bool: Delay the removal of this entity until `Store.apply_removals`
                            is called. (Default value = False)

        """
        if delay:
            self.entity_delete_buffer.add(uuid)
        else:
            self._remove_entity(uuid)
            self.clear_cache()

    def apply_removals(self):
        """Apply all delayed removals."""
        dirty = False

        for uuid in self.entity_delete_buffer:
            self._remove_entity(uuid)
            dirty = True
        self.entity_delete_buffer.clear()

        for uuid, c_type in self.component_delete_buffer:
            try:
                self._remove_component(uuid, c_type)
            except KeyError:
                # Entity was deleted as well, so the component is already gone.
                ...
            dirty = True
        self.component_delete_buffer.clear()

        if dirty:
            self.clear_cache()
