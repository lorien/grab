# Grab Framework Project

[![Grab Test Status](https://github.com/lorien/grab/actions/workflows/test.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Code Quality](https://github.com/lorien/grab/actions/workflows/check.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Type Check](https://github.com/lorien/grab/actions/workflows/mypy.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/mypy.yml)
[![Grab Test Coverage Status](https://coveralls.io/repos/github/lorien/grab/badge.svg)](https://coveralls.io/github/lorien/grab)
[![Pypi Downloads](https://img.shields.io/pypi/dw/grab?label=Downloads)](https://pypistats.org/packages/grab)
[![Grab Documentation](https://readthedocs.org/projects/grab/badge/?version=latest)](https://grab.readthedocs.io/en/latest/)

## Status of Project

I myself have not used Grab for many years. I am not sure it is being used by anybody at present time.
Nonetheless I decided to refactor the project, just for fun. I have annotated
whole code base with mypy type hints (in strict mode). Also the whole code base complies to
pylint and flake8 requirements. There are few exceptions: very large methods and classes with too many local
atributes and variables. I will refactor them eventually.

The current and the only network backend is [urllib3](https://github.com/urllib3/urllib3).

I have refactored a few components into external packages: [proxylist](https://github.com/lorien/proxylist),
[procstat](https://github.com/lorien/procstat), [selection](https://github.com/lorien/selection),
[unicodec](https://github.com/lorien/unicodec), [user\_agent](https://github.com/lorien/user_agent)

Feel free to give feedback in Telegram groups: [@grablab](https://t.me/grablab) and [@grablab\_ru](https://t.me/grablab_ru)

## Things to be done next

* Refactor source code to remove all pylint disable comments like:
    * too-many-instance-attributes
    * too-many-arguments
    * too-many-locals
    * too-many-public-methods
* Make 100% test coverage, it is about 95% now
* Release new version to pypi
* Refactor more components into external packages
* More abstract interfaces
* More data structures and types
* Decouple connections between internal components

## Installation

That will install old Grab released in 2018 year: `pip install -U grab`

The updated Grab available in github repository is 100% not compatible with spiders and crawlers
written for Grab released in 2018 year.

## Documentation

Updated documenation is here https://grab.readthedocs.io/en/latest/ Most updates are removings
content related to features I have removed from the Grab since 2018 year.

Documentation for old Grab version 0.6.41 (released in 2018 year) is here https://grab.readthedocs.io/en/v0.6.41-doc/
