from pyecs.datatypes import Vector2D


def test_vector2D():
    a = Vector2D(1.0, 0.0)
    b = Vector2D(1.0, 1.0)

    assert 2 * b == Vector2D(2.0, 2.0)
    assert 2 * b == b * 2

    assert a + b == Vector2D(2.0, 1.0)
    assert b + a == a + b

    assert b - a == Vector2D(0.0, 1.0)
    assert a - b != b - a

    b += a
    assert b == Vector2D(2.0, 1.0)

    b -= a
    assert b == Vector2D(1.0, 1.0)

    a *= 2
    assert a == Vector2D(2.0, 0.0)
