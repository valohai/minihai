# -*- coding: utf-8 -*-
import re

from setuptools import find_packages, setup

from minihai import __version__


def read_requirements(filename):
    return [
        line
        for line in (re.sub(r"\s*#.+$", "", line) for line in open(filename))
        if line.strip()
    ]


setup(
    name="minihai",
    description="A small shark",
    author="Valohai",
    author_email="hait@valohai.com",
    version=__version__,
    entry_points={"console_scripts": ["minihai=minihai.cli:main"]},
    install_requires=read_requirements("requirements.txt"),
    packages=find_packages(include=("minihai", "minihai.*")),
)
