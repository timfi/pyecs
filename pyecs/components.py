from dataclasses import dataclass

from pyecs.core import Component
from pyecs.datatypes import Vector2D

__all__ = ("Transform2D", "Rigidbody2D", "BoxCollider2D")


@dataclass
class Transform2D(Component):
    position: Vector2D = Vector2D(0.0, 0.0)
    rotation: float = 0.0


@dataclass
class Rigidbody2D(Component):
    velocity: Vector2D = Vector2D(0.0, 0.0)
    acceleration: Vector2D = Vector2D(0.0, 0.0)


@dataclass
class BoxCollider2D(Component):
    x_offset: float = 0.0
    y_offset: float = 0.0
    width: float = 0.0
    height: float = 0.0
