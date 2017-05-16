# Grab Change Log

## [0.6.38] - 2017-05-17
### Fixed
- Fix "error:None" in spider rps logging
- Fix race condition bug in task generator

### Added
- Add original_exc attribute to GrabNetworkError (and subclasses) that points to original exception

### Changed
- Remove IOError from the ancestors of GrabNetworkError
- Add default values to --spider-transport and --grab-transport options of crawl script

## [0.6.37] - 2017-05-13
### Added
- Add --spider-transport and --grab-transport options to crawl script
- Add SOCKS5 proxy support in urllib3 transport

### Fixed
- Fix #237: urllib3 transport fails without pycurl installed
- Fix bug: incorrect spider request logging when cache is enabled
- Fix bug: crawl script fails while trying to process a lock key
- Fix bug: urllib3 transport fails while trying to throw GrabConnectionError exception
- Fix bug: Spider add_task method fails while trying to log invalid URL error

### Removed
- Remove obsoleted hammer_mode and hammer_timeout config options

## [0.6.36] - 2017-02-12
### Added
- Add pylint to default test set

### Fixed
- Fix #229: using deprecated response object inside Grab

### Removed
- Remove spider project template and start_project script

## [0.6.35] - 2017-02-06
### Fixed
- Fix bug in deprecated grab.choose_form method
- Add default project templates files to the distribution, by @rushter
- Fix #222: debug_post option fails with big post data
- Fix #148: pycurl ignores sigint signal

## [0.6.34] - 2017-02-04
### Added
- Start running Grab tests in OSX environment on travis CI

### Changed
- Use defusedxml library to parse HTML and XML, by @kevinlondon
- Put selection, lxml and pycurl libs back to required dependencies in setup.py
- Update installation documentation

## [0.6.33] - 2017-01-28 
### Added
- Add API documentation about few grab modules, by @rushter
- Start running Grab tests in Windows enviroment on appveyor CI
- New spider transport based on threads that allows to use Spider with any Grab network backend e.g. urllib3
- Add `remove_from_post` option to grab.doc.submit method 
- Add `random` option to grab.change_proxy method 
- Support for deprecated attributes Spider.items and Spider.counters
- If Spider handler raises ResponseNotValid exception, then that task goes back to task queue until task.task_try_count reaches the spider.task_try_limit

### Changed
- Refactor management of internal threads, fix random test failures related to cache sub-module
- Disable default logging to files while running spider by `run crawl` command
- Multiple improvements in urllib3 transport
- Set default spider network & try limits to 3 (was 10)

### Fixed
- Different bugs in urllib3 transport
- Different bugs

### Removed
- Remove grab.use_next_proxy method
- Remove grab.dump method
- Remove deprecated Spider methods and attributes

## [0.6.32] - 2017-12-31
### Fixed
- Fix setup.py

## [0.6.31] - 2017-12-31
### Added
- Everyting :) Probably later I'll extend changelog more deep to the history
