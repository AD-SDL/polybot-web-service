import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join("polybot", "version.py")) as f:
    exec(f.read(), version_ns)
version = version_ns['__version__']

# Read in the package requirements
with open("requirements.txt") as fp:
    requirements = fp.readlines()

setup(
    name='polybot',
    version=version,
    packages=find_packages(),
    description='Server to analyze, monitor and control robotic experiments performed at CNM',
    install_requires=requirements,
    python_requires=">=3.7",
    package_data={
        'polybot': ['templates/*.html']
    },
    entry_points={
        'console_scripts': [
            'polybot = polybot.cli:main'
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering"
    ],
    author='Logan Ward',
    author_email='lward@anl.gov',
    license="Apache License, Version 2.0",
    url="https://github.com/materials-data-facility/polybot"
)
