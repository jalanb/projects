"""Handle files for projects"""


import os
import shutil


def texts():
    return [
        'CONTRIBUTING.txt',
        'LICENSE',
    ]


def templates():
    return [
        'README.md',
        'TODO.md',
        'requirements.txt',
        'setup.py',
    ]


def sources():
    return texts() + templates()


def copy(path):
    if not path:
        raise ValueError('path cannot be empty')
    if not os.path.isdir(path):
        raise ValueError('%r is not a directory' % path)
    for source in sources:
        shutil.copy(source, path)
