# pyecs
_An implementation of the Entity-Component-System pattern._

[![PyPI](https://img.shields.io/pypi/v/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Status](https://img.shields.io/pypi/status/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - License](https://img.shields.io/pypi/l/pyecs)](https://opensource.org/licenses/MIT)

[![Build Status](https://travis-ci.org/tim-fi/pyecs.svg?branch=master)](https://travis-ci.org/tim-fi/pyecs)
[![codecov](https://codecov.io/gh/tim-fi/pyecs/branch/master/graph/badge.svg)](https://codecov.io/gh/tim-fi/pyecs)
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

from pyecs import ECSController

# 1. build your components
@dataclass
class Transform:
    position: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Rigidbody:
    velocity: Tuple[float, float] = (0.0, 0.0)
    acceleration: Tuple[float, float] = (0.0, 0.0)


# 2. define a system
def physics(controller: ECSController):
    for entity in controller.get_entities_with(Transform, Rigidbody):
        transform, rigidbody = entity.get_components(Transform, Rigidbody)
        rigidbody.velocity = (
            rigidbody.velocity[0] + rigidbody.acceleration[0],
            rigidbody.velocity[1] + rigidbody.acceleration[1],
        )
        transform.position = (
            transform.position[0] + rigidbody.velocity[0],
            transform.position[1] + rigidbody.velocity[1],
        )
        print(f"{transform=}\t{rigidbody=}")


if __name__ == "__main__":
    # 3. setup controller
    controller = ECSController()
    controller.add_system(physics)

    # 4. add some entities
    controller.add_entity(Transform(), Rigidbody(acceleration=(1.0, 0.0)))
    controller.add_entity(Transform(), Rigidbody(acceleration=(0.0, 1.0)))
    controller.add_entity(Transform(), Rigidbody(acceleration=(1.0, 1.0)))

    # 5. run everything
    while True:
        controller.tick()
```


## Dev Setup
Simply install [pipenv](https://docs.pipenv.org/en/latest/) and run the following line:
```sh
pipenv install --dev
```
