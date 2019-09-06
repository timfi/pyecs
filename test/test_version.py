from pyecs import __version__


def test_version():
    assert "__title__" in dir(__version__)
    assert "__description__" in dir(__version__)
    assert "__url__" in dir(__version__)
    assert "__version__" in dir(__version__)
    assert "__build__" in dir(__version__)
    assert "__author__" in dir(__version__)
    assert "__author_email__" in dir(__version__)
    assert "__license__" in dir(__version__)
    assert "__copyright__" in dir(__version__)
