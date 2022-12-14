.. _usage_testing:

Testing Grab Framework
======================

To run the full set of Grab tests you should install the additional 
dependencies listed in `requirements_dev.txt` and 
`requirements_dev_backend.txt.`

To run all tests run the command:

.. code:: shell

	./runtest.py --test-all --backend=mongodb,redis,pyquery


.. _usage_testing_control:

Controlling what parts of Grab to test
--------------------------------------

You can run tests for specific parts of the Grab framework. Here are the
available options for `runtest.py`::

    --test-grab - Grab API tests
    --test-spider - Grab::Spider API tests
    --test-all - shortcut to run both Grab and Grab::Spider tests
    --backend=redis - enable tests of things that work with redis
    --backend=mysql - enable tests of things that work with mysql
    --backend=mongodb - enable tests of things that work with mongo
    --backend=pyquery - enable tests of things that work with pyquery

If you want to run specific test cases then use the `-t` option. For example:

.. code:: shell

    ./runtest.py -t test.grab_api


.. _usage_testing_tox:

Testing with Tox
----------------

To run Grab tests in different python environments you can use `tox` command::

    tox

By default it will run the full set of tests in two environments: python3.4 
and python2.7 

You can specify a specific environment with `-e` option::

    tox -e py34

To run all tests except backend tests, use `-nobackend` suffix::

    tox -e py34-nobackend,py27-nobackend


.. _usage_testing_database_configuration:

Database configuration
----------------------

To run tests on a specific machine you may need to change the default database
connection settings. Default settings are stored in the `test_settings.py`
file. You can override any default setting in the `test_settings_local.py`
file.


.. _usage_testing_travis:

Travis Testing
--------------

The Grab project is configured to run the full set of tests for each new 
commit placed into the project repository. You can see the status of a recent 
commit and the status of all previous commits here: https://travis-ci.org/lorien/grab 


.. _usage_testing_coverage:

Test Coverage
-------------

To see test coverage run the commands::

    coverage erase
    coverage run --source=grab ./runtest.py --test-all --backend=mongodb,redis,pyquery
    coverage report -m

Also you can use shortcut::

    make coverage

The Grab project is configured to submit coverage statistics to the 
coveralls.io service after each test session is completed by travis-ci. You 
can see the coverage history at this URL: https://coveralls.io/r/lorien/grab
