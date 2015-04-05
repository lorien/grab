.. _usage_testing:

Testing Grab Framework
======================

To run full set of Grab tests you should install additional dependencies
listed in files requirements_dev.txt and requirements_dev_backend.txt.

To run all tests run the command:

.. code:: shell

	./runtest.py --test-all --extra --backend-mongo --backend-mysql --backend-redis --backend-postgres


.. _usage_testing_control:

Controlling what parts of Grab to test
--------------------------------------

You can run tests for specific part of Grab framework. Here is 
available options of runtest.py command::

    --test-grab - Grab API tests
    --test-spider - Grab::Spider API tests
    --test-all - shortcut to run both Grab and Grab::Spider tests
    --backend-redis - enable tests of things that work with redis
    --backend-mysql - enable tests of things that work with mysql
    --backend-postgresql - enable tests of things that work with postgresql
    --backend-mongo - enable tests of things that work with mongo

If you want to run specific test case then use `-t` option. Example:

.. code:: shell

    ./runtest.py -t test.grab_api


.. _usage_testing_tox:

Testing with Tox
----------------

To run Grab tests in different python environments you can use `tox` command::

    tox

By default it run full set of tests in two environemnts: python3.4 and python2.7

You can specify concrete environment with `-e` option::

    tox -e py34

To run all tests except backend tests use `-nobackend` suffix::

    tox -e py34-nobackend,py27-nobackend


.. _usage_testing_database_configuration:

Database configuration
----------------------

To run tests on specific machine you may need to change default database
connection settings. Default settings are stored in the `test_settings.py`
file. You can override any default setting in the `test_settings_local.py`
file.


.. _usage_testing_travis:

Travis Testing
--------------

Grab project is configured to run full set of tests for each new commit placed
into the project repository. You can see status of recent commit and status of
all previous commits here: https://travis-ci.org/lorien/grab 


.. _usage_testing_coverage:

Test Coverage
-------------

To see test coverage run the commands::

	coverage erase
	coverage run --source=grab ./runtest.py --test-all --extra --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m

Also you can use shortcut::

    make coverage

Grab project is configured to submit coverage statistics to coveralls.io service
after each test session completed on travis-ci.org service. You can see
coverage history at this URL: https://coveralls.io/r/lorien/grab
