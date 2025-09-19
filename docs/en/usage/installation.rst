.. _usage_installation:

Grab Installation
================

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

    pip install -U setuptools pip

Run the command:

.. code:: shell

    pip install -U grab

This command will install Grab and all dependencies. Be aware that you need
to have some libraries installed in your system to successfully build lxml and
pycurl dependencies.

To build pycurl successfully you need to install:

.. code:: shell

    apt-get install libcurl4-openssl-dev
   
To build lxml successfully you need to install:

.. code:: shell

    apt-get install libxml2-dev libxslt-dev

If your system has 512Mb RAM or less you might experience issues during instalation
of Grab dependencies. Installation of lxml requries quite a few RAM. In such case
enable swap file if it is disabled.


.. _installation_windows:

Installation on Windows
-----------------------

Step 1. Install lxml. You can get lxml here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

Step 2. Install pycurl.

.. warning::

    Do not use the recent version of pycurl (7.43.0 at the moment). This version fails randomly on windows platform. Use 7.19.5.3 version. You can get it here https://bintray.com/pycurl/pycurl/pycurl/view#files

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

    lxml
    pycurl
    selection
    weblib
    six
    user_agent


.. _installation_upgrade:

Upgrade Grab from 0.5.x version to 0.6.x
----------------------------------------

In Grab 0.6.x some features were moved out into separate packages. If
you install/upgrade Grab with pip, all dependencies should be installed 
automatically. Anyway, if you have some ImportError issues then try to 
install dependencies manually with the command: 

.. code:: shell

    pip install -U lxml pycurl selection weblib six user_agent
