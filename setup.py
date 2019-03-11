#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="respykt",
    version="0.8",
    description="A useful module",
    license="EUPL 1.2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jan Svanda",
    author_email="svandajan@svandajan.cz",
    url="http://python.svandajan.cz/",
    packages=["respykt"],
    package_data={"respykt": ["resources/*"]},
    install_requires=["requests", "beautifulsoup4", "Mako"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",

    ]
)
