# pyecs
_A simple implementation of the Entity-Component pattern._

[![PyPI - Version](https://img.shields.io/pypi/v/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Status](https://img.shields.io/pypi/status/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyecs)](https://pypi.org/project/pyecs)
[![PyPI - License](https://img.shields.io/pypi/l/pyecs)](https://opensource.org/licenses/MIT)

[![Build Status](https://img.shields.io/github/workflow/status/tim-fi/pyecs/Tests?logo=github)](https://github.com/tim-fi/pyecs/actions?query=workflow%3ATests)
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

from pyecs import Store

# 1. build your components
@dataclass
class Transform:
    position: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Rigidbody:
    velocity: Tuple[float, float] = (0.0, 0.0)
    acceleration: Tuple[float, float] = (0.0, 0.0)


if __name__ == "__main__":
    # 2. intialize entity-component store
    store = Store()

    # 3. add some entities
    scene = store.add_entity()
    scene.add_child(Transform(), Rigidbody(acceleration=(1.0, 0.0)))
    scene.add_child(Transform(), Rigidbody(acceleration=(0.0, 1.0)))
    scene.add_child(Transform(), Rigidbody(acceleration=(1.0, 1.0)))

    # 4. run everything
    while True:
        for transform, rigidbody in store.get_entities_with(Transform, Rigidbody, unpack=True):
            rigidbody.velocity = (
                rigidbody.velocity[0] + rigidbody.acceleration[0],
                rigidbody.velocity[1] + rigidbody.acceleration[1],
            )
            transform.position = (
                transform.position[0] + rigidbody.velocity[0],
                transform.position[1] + rigidbody.velocity[1],
            )
            print(f"{transform=}\t{rigidbody=}")
```


## Dev Setup
Simply install [pipenv](https://docs.pipenv.org/en/latest/) and run the following line:
```sh
pipenv install --dev
```
