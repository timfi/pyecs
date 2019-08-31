from dataclasses import dataclass

from ecs.core import Component
from ecs.datatypes import Vector2D


__all__ = ("Transform2D", "Rigidbody2D", "BoxCollider2D")


@dataclass
class Transform2D(Component):
    position: Vector2D
    rotation: float


@dataclass
class Rigidbody2D(Component):
    velocity: Vector2D
    acceleration: Vector2D


@dataclass
class BoxCollider2D(Component):
    x_offset: float
    y_offset: float
    width: float
    height: float
