"""Set up the projects project"""


from dataclasses import dataclass
from setuptools import setup


import projects as project

description = project.__doc__
headline = description.splitlines()[0]
name = project.__name__,
version = project.__version__,

@dataclass
class User:
    service: str
    username: str
    email: str

    def url(self, name):
        return f'https://{self.service}/{self.username}/{name}'

user = User('github', 'jalanb', 'github@al-got-rhythm.net', 'J Alan Brogan')

setup(
    name=name,
    version=version,
    description=headline,
    long_description=description,
    url=user.url,
    download_url='{user.url(name)}/tarball/v{version}',
    license='MIT License',
    author=user.name,
    author_email=user.email,
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
    ],
    tests_require=['pytest'],
    extras_require={
        'docs': ['Sphinx'],
        'testing': ['pytest'],
    }
)
