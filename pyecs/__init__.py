"""Entity-Component Store."""
from collections import defaultdict
from functools import lru_cache
from uuid import uuid4 as get_uuid

__all__ = ("Store", "Entity")


class Entity:
    """A wrapper around an entity-uuid and entity-component store."""

    __slots__ = ("_store", "_uuid")

    def __init__(self, store, uuid):  # noqa
        self._store = store
        self._uuid = uuid

    def __repr__(self):  # noqa
        return f"Entity(uuid={self._uuid})"

    __str__ = __repr__

    @property
    def uuid(self):  # noqa
        """Identifier of this entity in the Store."""
        return self._uuid

    def __eq__(self, other):  # noqa
        return (
            isinstance(other, Entity)
            and self.uuid == other.uuid
            and self._store == other._store
        )

    def add_child(self, *components, uuid=None):
        """Create child entity.

        :param *components: Components to add to the entity.
        :param uuid: Override UUID, if given this skips the automatic
                     UUID generation. (Default value = None)

        """
        return self._store.add_entity(*components, parent=self, uuid=uuid)

    def add_components(self, *components):
        """Add components to entity.

        :param *components: Components to add to the entity.

        """
        self._store.add_components(self.uuid, *components)

    def get_component(self, c_type):
        """Get a single component from entity.

        :param c_type: Type of the component to get from the entity.

        """
        return self._store.get_component(self.uuid, c_type)

    def get_components(self, *c_types):
        """Get multiple components from entity.

        Note that proper typing is only ensured up to 10 components.

        :param *c_types: Types of the components to get from the entity,
                         the result will be in the order these types are given.

        """
        return self._store.get_components(self.uuid, *c_types)

    def get_parent(self):
        """Get parent entity."""
        return self._store.get_parent(self.uuid)

    def get_children(self):
        """Get all child entities."""
        return self._store.get_children(self.uuid)

    def get_children_with(self, *c_types):
        """Get all children with the given components.

        :param *c_types: Types of the components the entities should have.

        """
        return self._store.get_children_with(self.uuid, *c_types)

    def remove_components(self, *c_types, delay=False):
        """Remove component from entity.

        :param *c_types: Types of the components to remove from the entity.
        :param delay: Delay the removal of the components until `Store.apply_removals`
                      is called. (Default value = False)

        """
        self._store.remove_components(self.uuid, *c_types, delay=delay)

    def remove(self, *, delay=False):
        """Remove entity from Store.

        :param delay: Delay the removal of this entity until `Store.apply_removals`
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
        self.get_children_with.cache_clear()

    def clear(self):
        """Delete all data."""
        self.clear_cache()
        self.entities.clear()
        self.entity_hirarchy.clear()
        self.entity_hirarchy_rev.clear()
        self.components.clear()
        self.entity_delete_buffer.clear()
        self.component_delete_buffer.clear()

    def add_entity(self, *components, parent=None, uuid=None):
        """Add entity to store.

        :param *components: Components to add to the entity.
        :param parent: Entity to register as a parent
                       entity. (Default value = None)
        :param uuid: Override UUID, if given this skips the automatic
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

    def add_components(self, uuid, *components):
        """Add components to an existing entity.

        :param uuid: UUID of the entity to add the components to.
        :param *components: Components to add to the entity.

        """
        for component in components:
            c_name = type(component).__qualname__
            self.entities[uuid] |= {c_name}
            self.components[c_name][uuid] = component

        self.clear_cache()

    def get_component(self, uuid, c_type):
        """Get a single component from an entity.

        :param uuid: UUID of the entity to get the component from.
        :param c_type: Type of the component to get from the entity.

        """
        return self.components[c_type.__qualname__][uuid]

    @lru_cache
    def get_components(self, uuid, *c_types):
        """Get multiple component from an entity.

        Note that proper typing is only ensured up to 10 components.

        :param uuid: UUID of the entity to get the components from.
        :param *c_types: Types of the components to get from the entity,
                         the result will be in the order these types are given.

        """
        if c_types:
            return tuple(self.get_component(uuid, c_type) for c_type in c_types)
        else:
            return tuple(
                self.components[c_name][uuid] for c_name in self.entities[uuid]
            )

    def get_entity(self, uuid):
        """Get an entity for a given UUID.

        :param uuid: UUID of the entity to get.

        """
        if uuid in self.entities:
            return Entity(self, uuid)
        else:
            raise KeyError("Unknown entity id.")

    def get_entities(self):
        """Get all entities in this store."""
        return tuple(Entity(self, uuid) for uuid in self.entities)

    def _filter_entities(self, entities, c_types):  # noqa
        for c_type in c_types:
            entities &= set(self.components[c_type.__qualname__])

        return tuple(self.get_entity(uuid) for uuid in entities)

    @lru_cache
    def get_entities_with(self, *c_types):
        """Get all entities with the given components.

        :param *c_types: Types of the components the entities should have.

        """
        return self._filter_entities(set(self.entities), c_types)

    def get_children(self, uuid):
        """Get children of an entity.

        :param uuid: UUID of the entity to get the children for.

        """
        return tuple(Entity(self, c_uuid) for c_uuid in self.entity_hirarchy[uuid])

    @lru_cache
    def get_children_with(self, uuid, *c_types):
        """Get all children of an entity with the given components.

        :param *c_types: Types of the components the entities should have.

        """
        return self._filter_entities(self.entity_hirarchy[uuid], c_types)

    def get_parent(self, uuid):
        """Get parent of an entity.

        :param uuid: UUID of the entity to get the parent for.

        """
        return (
            Entity(self, p_uuid)
            if (p_uuid := self.entity_hirarchy_rev.get(uuid))
            else None
        )

    def _remove_component(self, uuid, c_type):
        self.entities[uuid] -= {c_type.__qualname__}
        del self.components[c_type.__qualname__][uuid]

    def remove_components(self, uuid, *c_types, delay=False):
        """Remove components from an entity.

        :param uuid: UUID of the entity to remove the components from.
        :param *c_types: Types of the components to remove from the entity.
        :param delay: Delay the removal of the components until `Store.apply_removals`
                      is called. (Default value = False)

        """
        if delay:
            for c_type in c_types:
                self.component_delete_buffer.add((uuid, c_type))
        else:
            for c_type in c_types:
                self._remove_component(uuid, c_type)
            self.clear_cache()

    def _remove_entity(self, uuid):  # noqa
        for c_name in self.entities.pop(uuid, ()):
            del self.components[c_name][uuid]

        if (p_uuid := self.entity_hirarchy_rev.pop(uuid)) :
            self.entity_hirarchy[p_uuid] -= {uuid}

        for c_uuid in [*self.entity_hirarchy[uuid]]:
            self.remove_entity(c_uuid)

        del self.entity_hirarchy[uuid]

    def remove_entity(self, uuid, *, delay=False):
        """Remove an entity.

        :param uuid: UUID of the entity to remove.
        :param delay: Delay the removal of this entity until `Store.apply_removals`
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
