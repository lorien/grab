.. _changelog:

==========
Change Log
==========

0.4.11
======

* New feature: ability to specify record's timeout when working with spider cache
* New feature: add `clear` method to spider cache backend
* New feature: grab command line utility to control spiders
* New feature: add mock transport which could be useful in testing
* Fix bug: correct processing of infinite redirect in meta refresh tag (#88)
* Improvement: more flexible Grab `transport` option (#90)
* Fix bug: spider redis task queue does not store multiple tasks with same URL
* Test: add travis (continous integration service) support 
* Test: refactor tests, use Flask instead BaseHTTPServer

0.4.10
======

* Fix bug: spider ignores `user_agent` option 
* Drop option: spider `retry_rebuild_user_agent` option
