"""Test the projects package"""


import unittest


import projects


def test_doc():
    """The module should be documented"""
    assert getattr(projects, '__doc__', None) is not None


def test_version():
    """The version has not zero"""
    assert projects.__version__ > '0.0.0'


class TestProgramScript(unittest.TestCase):
    def test_main(self):
        """The main method calls one method from the package"""
        with self.assertRaises(ValueError) as cm:
            projects.copy('')
        error_message = str(cm.exception)
        self.assertEquals(error_message, 'path cannot be empty')
