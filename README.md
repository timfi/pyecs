# pyecs
_An implementation of the Entity-Component-System pattern._

[![PyPI](https://img.shields.io/pypi/v/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Status](https://img.shields.io/pypi/status/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - License](https://img.shields.io/pypi/l/pyecs)](https://opensource.org/licenses/MIT)

[![Build Status](https://travis-ci.org/tim-fi/pyecs.svg?branch=master)](https://travis-ci.org/tim-fi/pyecs)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

## Install
This project is available on [PyPI](https://pypi.org/project/pyecs) so you can simply install it via
```sh
pip install pyecs
```

## Example
```python
from dataclasses import dataclass
from typing import Tuple

from pyecs import ECSController, Component, system

# 1. build your components
@dataclass
class Transform(Component, identifier="transform"):
    position: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Rigidbody(Component, identifier="rigidbody"):
    velocity: Tuple[float, float] = (0.0, 0.0)
    acceleration: Tuple[float, float] = (0.0, 0.0)


# 2. define some systems
@system((Transform, Rigidbody))
def physics(delta_t, data, entities):
    for entity in entities:
        entity.rigidbody.velocity = (
            entity.rigidbody.velocity[0] + entity.rigidbody.acceleration[0] * delta_t,
            entity.rigidbody.velocity[1] + entity.rigidbody.acceleration[1] * delta_t,
        )
        entity.transform.position = (
            entity.transform.position[0] + entity.rigidbody.velocity[0] * delta_t,
            entity.transform.position[1] + entity.rigidbody.velocity[1] * delta_t,
        )


@system((Transform,))
def introspect_position(delta_t, data, entities):
    if "tick" not in data:
        data["tick"] = 0
    print(f"Tick: {data['tick']}")
    for entity in entities:
        print(f" - Entity {entity.uuid}: position = {entity.transform.position}")
    data["tick"] += 1


if __name__ == "__main__":
    # 3. setup controller
    controller = ECSController()
    controller.register_system(physics)
    controller.register_system(introspect_position)

    # 4. add some entities
    controller.add_entity(Transform(), Rigidbody(acceleration=(1.0, 0.0)))
    controller.add_entity(Transform(), Rigidbody(acceleration=(0.0, 1.0)))
    controller.add_entity(Transform(), Rigidbody(acceleration=(1.0, 1.0)))

    # 5. run everything
    controller.run()
```


## Dev Setup
Simply install [pipenv](https://docs.pipenv.org/en/latest/) and run the following line:
```sh
pipenv install --dev
```
