"""Set up the projects project"""


from setuptools import setup


import projects


setup(
    name='projects',
    version=projects.__version__,
    url='https://github.com/jalanb/projects',
    license='MIT License',
    author='J Alan Brogan',
    author_email='projects@al-got-rhythm.net',
    description='Provide skeletal outlines for any of my future projects',
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
    ],
    scripts=['bin/projects'],
    test_suite='nose.collector',
    tests_require=['nose'],
    extras_require={
        'docs': ['Sphinx'],
        'testing': ['nose'],
    }
)
