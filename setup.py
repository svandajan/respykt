#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="respykt",
    version="0.8",
    description="A useful module",
    license="GPL v3",
    long_description=long_description,
    author="Jan Svanda",
    author_email="svandajan@svandajan.cz",
    url="http://python.svandajan.cz/",
    packages=["respykt"],
    install_requires=["requests", "beautifulsoup4", "Mako"]
)
