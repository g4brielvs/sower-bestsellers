#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = ["scrapy"]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="g4brielvs",
    author_email="sower@g4brielvs.me",
    python_requires=">=3.7,<=3.8",
    install_requires=requirements,
    license="Proprietary",
    include_package_data=True,
    name="sower",
    packages=find_packages(include=["sower", "sower.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    version="0.1.0",
    zip_safe=False,
)
