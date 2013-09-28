.. _changelog:

==========
Change Log
==========

0.4.13
======

Major
-----
* New: item.DateField
* New: item.DecimalField
* New: add `multiple` option to item.StringField
* New: ability to process extra command-line arguments per each spider
* New: new layer in Spider - command interface, that allows to pass commands
  to live spiders.
* New: structure extension
* New: item classes inheritance

Other
-----

* New: All commands executed via `grab` command automatically set django's settings.DEBUG to False
* Fix: some issues raised then `grab crawl` command is building list of available spiders.
* New: start working on new version of documentation (in docs2/ directory)
* Fix: `grab` command reset existing logging configuration
* New: Add `valid_exceptions` option to tools.grab.control.repeat
* New: add __slots__ to some classes
* New: remove firefox user-agents from the list of default user-agents
* Fix: some memory-leaks

0.4.12
======

Major
-----

* New: py3k support (thanks to https://github.com/signaldetect)
* New: builtin script called `grab` to launch spider processes. Ability to specify
    spider settings via settings file
* New: ability to specify crawler config via settings file
* New: develop proof-of-concept network transport that uses QtWebKit module to do
    network requests and proces HTML/JavaScript
* New: develop proof-of-concept Selector extensions that allows to work with nodes
* Change: refactor captcha module, support for asynchronouse usage in Spider
* New: ability to schedule delayed tasks (only in memory task queue backend yet)
* New: Add automatic virtualenv activation to `grab` utility
* New: Add --env option to `grab` utility to specify virtualenv home
* New: develop proof-of-concept architecture that allows to run spider tasks in multiple processes

Other
-----

* New: Item.get_function to extract standalone function from FuncField field
* Del: drop clear_on_init and clear_on_exit options of mongodb task queue backend
* New: add Spider.get_name method which output is used to register spider in spider registry
* New: task queue constructor accepts new required option: spider_name
* New: ability to control `refresh_cache` option of all tasks with same name
* Fix: exception while installing Grab without lxml installed before
* New: implement special Class to load, store and process all settings, use it in Spider
  of real-time DOM of QtWebKit engine
* New: refactor and make more clean test structure
* Del: remove Grab.sleep method
* Change: class Selector is deprecated, use more specific classes XpathSelector, PyquerySelector, etc
* New: add MIT license file
* New: add has_item method to mysql cache backend
* New: add file locking feature to `crawl` command
* Del: drop `unique` feature in memory task queue
* Del: drop `timeout` options in `get` method of all task queue backends
* New: add `start_project` script and provide files for default project template
* New: add SelectorList.html method
* New: Raise exception when func_field decorator is used incorrectly
* Del: drop task_raw_* handlers support.
* Change: Raise `NoTaskHandler` error when no handler is defined for the task
* New: Add raw option to Task constructor that allows to pass response object
    to the handler even if there was a network error or HTTP status code indicating some HTTP error
* New: Add callback options to Task constructor that allows to specify any callable object as
    handler for responses generated with that task
* New: push current directory into sys.path when `grab` utility starts working
* New: Add ignore_chars option to grab.tools.text.find_number and to grab.item.field.IntegerField
* Del: Remove deprecated `debug_error` option from Spider constructor
* New: now it is possible to pass multiple object in one Data instance
* New: Give Data object ability to provide callback-handler to process themself.
* New: Add MongoObjectImageData shourt to handle specific cases when you need to download
    image and assign its local path to some field of object stored in the mongo database
* New: Add normalize_space option to StringField
* Change: Make more user-friendly exception about that spider could not process relative url
* New: Add get_month_number to grab.tools.russian
* Change: Speed up clear method of task queue redis backend
* Del: drop `smart_copy_file` function in grab.tools.files
* New: Add `multiple` option to StringField, IntegerField
* New: Add new setting GRAB_DJANGO_SETTINGS which allows to setup location of django settings module
* New: Add ability to save state of crawling process to database
* New: add py33 env to tox config
* New: Add file_required option to load_cookies method
* New: Add item.BooleanField
* New: Enchance Item module to support json selectors
* Change: Refactor the handling of url, grab, grab_config in Task class. Disallow
    passing both url and grab options to task constructor or to Task.clone method

0.4.11
======

* New: ability to specify record's timeout when working with spider cache
* New: add `clear` method to spider cache backend
* New: grab command line utility to control spiders
* New: add mock transport which could be useful in testing
* New: more flexible Grab `transport` option (#90)
* Fix: correct processing of infinite redirect in meta refresh tag (#88)
* Fix: spider redis task queue does not store multiple tasks with same URL
* Test: add travis (continous integration service) support 
* Test: refactor tests, use Flask instead BaseHTTPServer

0.4.10
======

* Fix: spider ignores `user_agent` option 
* Del: drop spider `retry_rebuild_user_agent` option
