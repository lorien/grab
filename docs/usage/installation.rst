.. _usage_installation:

Grab Installation
=================

.. _installation_linux:

Installation on Linux
---------------------

Run the command:

.. code:: shell

    pip install -U grab

This command will install Grab and all dependencies.

Be aware that you need to have some libraries installed in your system
to successfully build lxml dependency.  To build lxml successfully you
need to install:

.. code:: shell

    apt-get install libxml2-dev libxslt-dev

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

Run the command::

.. code:: shell

    python -m pip install grab

.. _installation_macos:

Installation on MacOS
---------------------

Run the command:

.. code:: shell

    pip install -U grab

.. _installation_deps:

Dependencies
------------

All required dependencies should be installed automatically if you 
install Grab with pip. Actual list of grab dependencies is stored in
https://github.com/lorien/grab/blob/master/pyproject.toml in "dependencies" key.
