"""Test the files module"""


import unittest


from projects import files


class TestFiles(unittest.TestCase):
    def test_copy_to_empty(self):
        with self.assertRaises(ValueError) as cm:
            files.copy('')
        error_message = str(cm.exception)
        self.assertEquals(error_message, 'path cannot be empty')

    def test_copy_to_file(self):
        with self.assertRaises(ValueError) as cm:
            files.copy('~/.bashrc')
        error_message = str(cm.exception)
        self.assertEquals(error_message, "'~/.bashrc' is not a directory")
