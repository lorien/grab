# Grab Framework Project

[![Grab Test Status](https://github.com/lorien/grab/actions/workflows/test.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Code Quality](https://github.com/lorien/grab/actions/workflows/check.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/test.yml)
[![Type Check](https://github.com/lorien/grab/actions/workflows/mypy.yml/badge.svg)](https://github.com/lorien/grab/actions/workflows/mypy.yml)
[![Grab Test Coverage Status](https://coveralls.io/repos/github/lorien/grab/badge.svg)](https://coveralls.io/github/lorien/grab)
[![Pypi Downloads](https://img.shields.io/pypi/dw/grab?label=Downloads)](https://pypistats.org/packages/grab)
[![Grab Documentation](https://readthedocs.org/projects/grab/badge/?version=latest)](https://grab.readthedocs.io/en/latest/)

Grab is a Python web scraping framework with advanced features for handling complex scraping tasks.

## Features

- **HTTP Client**: Make GET, POST, PUT, and other HTTP requests with ease
- **Smart Transport**: Automatically switches between regular HTTP and Cloudflare bypass modes
- **HTML Parsing**: Built-in HTML parsing with XPath and CSS selectors
- **Robust Error Handling**: Specific exceptions for different error scenarios
- **Cookies Management**: Automatic cookie handling for session management
- **Spider Framework**: Build asynchronous web crawlers with task queues
- **Multiple Queue Backends**: Memory, MongoDB, and Redis queue backends for spider tasks

## Status of Project

I myself have not used Grab for many years. I am not sure it is being used by anybody at present time.
Nonetheless I decided to refactor the project, just for fun. I have annotated
whole code base with mypy type hints (in strict mode). Also the whole code base complies to
pylint and flake8 requirements. There are few exceptions: very large methods and classes with too many local
atributes and variables. I will refactor them eventually.

The current and the only network backend is [urllib3](https://github.com/urllib3/urllib3), with an added [cloudscraper](https://github.com/VeNoMouS/cloudscraper) transport for Cloudflare bypass.

I have refactored a few components into external packages: [proxylist](https://github.com/lorien/proxylist),
[procstat](https://github.com/lorien/procstat), [selection](https://github.com/lorien/selection),
[unicodec](https://github.com/lorien/unicodec), [user\_agent](https://github.com/lorien/user_agent)

Feel free to give feedback in Telegram groups: [@grablab](https://t.me/grablab) and [@grablab\_ru](https://t.me/grablab_ru)

## Real-World Testing Status

Extensive real-world testing has been conducted and the framework is ready for production use. Key findings:

- Core functionality is stable and well-tested (84% overall test coverage)
- Successfully tested against various websites including httpbin.org, news.ycombinator.com, and more
- The SmartTransport system effectively handles Cloudflare protected sites
- Error handling is robust, with specific exceptions for different scenarios

See [SUMMARY.md](SUMMARY.md) for detailed testing results and recommendations.

## Quick Start

```python
from grab import HttpClient

# Make a simple GET request
client = HttpClient()
resp = client.request('https://httpbin.org/get')
print(resp.code)  # 200
print(resp.unicode_body())  # Response content

# Parse HTML with XPath
resp = client.request('https://news.ycombinator.com/')
for link in resp.select('//span[contains(@class, "titleline")]/a'):
    print(link.text())  # Prints headlines

# Handle Cloudflare protection automatically
resp = client.request('https://cloudflare-protected-site.com')
# SmartTransport will automatically switch to CloudscraperTransport if needed
```

## Installation

Current development version (recommended):
```
pip install git+https://github.com/lorien/grab.git
```

Old stable version (not compatible with current code):
```
pip install -U grab
```

The updated Grab available in this repository is 100% not compatible with spiders and crawlers
written for Grab released in 2018 year.

## Things to be done next

* Refactor source code to remove all pylint disable comments like:
    * too-many-instance-attributes
    * too-many-arguments
    * too-many-locals
    * too-many-public-methods
* Make 100% test coverage, it is currently about 84%
* Release new version to PyPI
* Refactor more components into external packages
* More abstract interfaces
* More data structures and types
* Decouple connections between internal components

## Documentation

Updated documentation is here https://grab.readthedocs.io/en/latest/

Documentation for old Grab version 0.6.41 (released in 2018 year) is here https://grab.readthedocs.io/en/v0.6.41-doc/
