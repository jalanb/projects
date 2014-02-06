"""Test the projects package"""


import projects


def test_doc():
    assert getattr(projects, '__doc__', None) is not None


def test_version():
    assert projects.__version__ > '0.0.0'
