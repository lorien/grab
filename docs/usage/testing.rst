.. _usage_testing:

Testing Grab Framework
======================

Building test environment
-------------------------

Run command:

.. code:: shell

    make bootstrap


Run tests
---------

Run all tests in 30 parallel threads::

    pytest -n30

Run all tests in 30 parallel threads, fail on first error::

    pytest -n30 -x

Same as previous but via make command::

    make pytest

Run specific test::

    pytest tests/test_util_types.py

Run all test cases which has "redis" in their name::

    pytest -k redis

.. _usage_testing_github:

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
