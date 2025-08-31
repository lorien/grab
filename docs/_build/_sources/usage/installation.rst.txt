.. _usage_installation:

Grab Installation
=================

.. _requirement_parsing_error:

Common problems
---------------


1) If you got the error `requirement specifiers; Expected version spec ...` while
installing grab via the pip then you have outdated setuptools or pip packages.

Fix the error with following command:

.. code:: shell

    pip install -U setuptools pip

2) If you got out of memory error while installing lxml on linux machine with 512Mb RAM
or less then check that you swap file is enabled.


.. _installation_linux:

Installation on Linux
---------------------

Update installation tools:

.. code:: shell

    pip install -U pip

Run the command:

.. code:: shell

    pip install -U grab

This command will install Grab and all dependencies.

Be aware that you need to have some libraries installed in your system
to successfully build lxml dependency.  To build lxml successfully you
need to install:

.. code:: shell

    apt-get install libxml2-dev libxslt-dev

If your system has 512Mb RAM or less you might experience issues during instalation
of Grab dependencies. Installation of lxml requries quite a few RAM. In such case
enable swap file if it is disabled.


.. _installation_windows:

Installation on Windows
-----------------------

If you have problems with installing lxml with pip try to manually install lxml with
packages available here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
I

Step 3. Update installation tools

.. code:: shell

    python -m pip install -U pip setuptools

If you don't have pip installed, install pip first. Download the file get-pip.py from 
https://bootstrap.pypa.io/get-pip.py and then run the command

.. code:: shell

    python get-pip.py

Step 4. Install Grab

Now you can install Grab via pip with this command::

    python -m pip install grab



.. _installation_freebsd:

Installation on FreeBSD
-----------------------

Update installation tools:

.. code:: shell

    pip install -U setuptools pip

Run the command:

.. code:: shell

    pip install -U grab

You can also install Grab from FreeBSD ports (thanks to Ruslan Makhmatkhanov):

* To install the port: cd /usr/ports/devel/py-grab/ && make install clean
* To add the package: pkg_add -r py27-grab


.. _installation_macos:

Installation on MacOS
---------------------

Update installation tools:

.. code:: shell

    pip install -U setuptools pip

Run the command:

.. code:: shell

    pip install -U grab



.. _installation_deps:

Dependencies
------------

All required dependencies should be installed automatically if you 
install Grab with pip. Here is list of Grab dependencies::

     weblib
     six
     user_agent
     selection
     lxml
     defusedxml
