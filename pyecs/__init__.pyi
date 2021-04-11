"""Entity-Component Store Type-Stubs."""
from typing import *
from uuid import UUID

F = TypeVar("F", bound=Callable)
C = TypeVar("C")
T0 = TypeVar("T0")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
T7 = TypeVar("T7")
T8 = TypeVar("T8")
T9 = TypeVar("T9")

def lru_cache(f: F) -> F: ...

class Entity:
    _store: Store
    _uuid: UUID
    def __init__(self, store: Store, uuid: UUID): ...
    def __repr__(self) -> str: ...
    __str__ = __repr__
    @property
    def uuid(self) -> UUID: ...
    def __eq__(self, other: Any) -> bool: ...
    def add_child(self, *components: Any, uuid: Optional[UUID] = ...) -> Entity: ...
    def add_components(self, *components: Any): ...
    def get_component(self, c_type: Type[C]) -> C: ...
    @overload
    def get_components(self, t0: Type[T0]) -> Tuple[T0]: ...
    @overload
    def get_components(self, t0: Type[T0], t1: Type[T1]) -> Tuple[T0, T1]: ...
    @overload
    def get_components(
        self, t0: Type[T0], t1: Type[T1], t2: Type[T2]
    ) -> Tuple[T0, T1, T2]: ...
    @overload
    def get_components(
        self, t0: Type[T0], t1: Type[T1], t2: Type[T2], t3: Type[T3]
    ) -> Tuple[T0, T1, T2, T3]: ...
    @overload
    def get_components(
        self, t0: Type[T0], t1: Type[T1], t2: Type[T2], t3: Type[T3], t4: Type[T4]
    ) -> Tuple[T0, T1, T2, T3, T4]: ...
    @overload
    def get_components(
        self,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
    ) -> Tuple[T0, T1, T2, T3, T4, T5]: ...
    @overload
    def get_components(
        self,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6]: ...
    @overload
    def get_components(
        self,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7]: ...
    @overload
    def get_components(
        self,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
        t8: Type[T8],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8]: ...
    @overload
    def get_components(
        self,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
        t8: Type[T8],
        t9: Type[T9],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]: ...
    @overload
    def get_components(self, *c_types: type) -> Tuple[Any, ...]: ...
    def get_parent(self) -> Optional[Entity]: ...
    def get_children(self) -> Tuple[Entity, ...]: ...
    def get_children_with(self, *c_types: type) -> Tuple[Entity, ...]: ...
    def remove_components(self, *c_types: type, delay: bool = ...) -> None: ...
    def remove(self, *, delay: bool = ...) -> None: ...

class Store:
    entities: Dict[UUID, Set[str]]
    entity_hirarchy: Dict[UUID, Set[UUID]]
    entity_hirarchy_rev: Dict[UUID, Optional[UUID]]
    components: Dict[str, Dict[UUID, Any]]
    entity_delete_buffer: Set[UUID]
    component_delete_buffer: Set[Tuple[UUID, type]]
    def __init__(self) -> None: ...
    def __hash__(self) -> int: ...
    def clear_cache(self) -> None: ...
    def clear(self) -> None: ...
    def add_entity(
        self,
        *components: Any,
        parent: Optional[Entity] = ...,
        uuid: Optional[UUID] = ...
    ) -> Entity: ...
    def add_components(self, uuid: UUID, *components: Any) -> None: ...
    def get_component(self, uuid: UUID, c_type: Type[C]) -> C: ...
    @overload
    def get_components(self, uuid: UUID, t0: Type[T0]) -> Tuple[T0]: ...
    @overload
    def get_components(
        self, uuid: UUID, t0: Type[T0], t1: Type[T1]
    ) -> Tuple[T0, T1]: ...
    @overload
    def get_components(
        self, uuid: UUID, t0: Type[T0], t1: Type[T1], t2: Type[T2]
    ) -> Tuple[T0, T1, T2]: ...
    @overload
    def get_components(
        self, uuid: UUID, t0: Type[T0], t1: Type[T1], t2: Type[T2], t3: Type[T3]
    ) -> Tuple[T0, T1, T2, T3]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
    ) -> Tuple[T0, T1, T2, T3, T4]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
    ) -> Tuple[T0, T1, T2, T3, T4, T5]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
        t8: Type[T8],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8]: ...
    @overload
    def get_components(
        self,
        uuid: UUID,
        t0: Type[T0],
        t1: Type[T1],
        t2: Type[T2],
        t3: Type[T3],
        t4: Type[T4],
        t5: Type[T5],
        t6: Type[T6],
        t7: Type[T7],
        t8: Type[T8],
        t9: Type[T9],
    ) -> Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]: ...
    @overload
    def get_components(self, uuid: UUID, *c_types: type) -> Tuple[Any, ...]: ...
    def get_entity(self, uuid: UUID) -> Entity: ...
    def get_entities(self) -> Tuple[Entity, ...]: ...
    def _filter_entities(
        self, entities: Set[UUID], c_types: Tuple[type, ...]
    ) -> Tuple[Entity, ...]: ...
    def get_entities_with(self, *c_types: type) -> Tuple[Entity, ...]: ...
    def get_children(self, uuid: UUID) -> Tuple[Entity, ...]: ...
    def get_children_with(self, uuid: UUID, *c_types: type) -> Tuple[Entity, ...]: ...
    def get_parent(self, uuid: UUID) -> Optional[Entity]: ...
    def _remove_component(self, uuid: UUID, c_type: type) -> None: ...
    def remove_components(
        self, uuid: UUID, *c_types: type, delay: bool = ...
    ) -> None: ...
    def _remove_entity(self, uuid: UUID) -> None: ...
    def remove_entity(self, uuid: UUID, *, delay: bool = ...) -> None: ...
    def apply_removals(self) -> None: ...
