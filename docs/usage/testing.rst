.. _usage_testing:

Testing Grab Framework
======================

Building test environment
-------------------------

Run command:

.. code:: shell

    make bootstrap



Fastest way to run all Grab tests
---------------------------------

.. code:: shell

    pytest -n30

Classic way to run tests
------------------------

Run the commands:

.. code:: shell

	./runtest.py --test-all --backend=mongodb,redis,pyquery

With runtestpy you can choose which set of tests to run. Available runtest.py options::

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


.. _usage_testing_travis:

Github Testing
--------------

The Grab project is configured to run the full set of tests for each new 
commit placed into the project repository. You can see the status of a recent 
commit and the status of all previous commits here: https://github.com/lorien/grab/actions


.. _usage_testing_coverage:

Test Coverage
-------------

To see test coverage just run full set of tests through pytest

.. code:: shell

    pytest -n30 -x --cov grab --cov-report term-missing

You can use shortcut::

    make pytest

The Grab project is configured to submit coverage statistics to the 
coveralls.io service after each test session is completed by travis-ci. You 
can see the coverage history at this URL: https://coveralls.io/github/lorien/grab

Linters
-------

Run with:

.. code:: shell

   make check

That will run mypy, pylint and flake8 linters.
