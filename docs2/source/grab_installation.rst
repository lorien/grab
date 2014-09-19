.. _grab_installation:

Installation
============

To use grab you need to install the Grab package and all its dependencies. Although the Python distribution system allows you to specify a list of dependencies to install automatically, you need to install Grab's dependencies manually; they will not be installed automatically when you just install the Grab package. The reason is that you need to install different versions of libraries for different python branches. Also, none of the dependencies are mandatory.

Recommended dependency list
---------------------------

To gain access to all the power of Grab, you should install the lxml and pycurl libraries. See the section below corresponding to your OS.

.. _installation_linux:

Installation in Linux
---------------------

1) Install lxml::

    pip install lxml

If you have build issues try to install the dependencies (Debian/Ubuntu example)::

    sudo apt-get install libxml2-dev libxslt-dev

2) Install pycurl::

    pip install pycurl

3) Finally, install Grab::

    pip install Grab

Installation in Windows
-----------------------

1) Install lxml

You can get lxml here: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

2) Install pycurl

You can get pycurl here: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

3) Install Grab

Download the Grab package from https://pypi.python.org/pypi/grab, unpack it and run::

    python setup.py install

If you use python 2.x, then you might get an error while using `python setup.py install`. There is a bug in python 2.7.6. Delete it, download python 2.7.5 and try to install Grab again.

You can also install Grab via pip. If you don't have pip installed, install pip first. Download the file get-pip.py from https://bootstrap.pypa.io/get-pip.py and then run this command::

    python get-pip.py

Now you can install Grab via pip with this command::

    python -m pip install grab


Installation on FreeBSD
-----------------------

See :ref:`installation_linux`

You can also install Grab from FreeBSD ports (thanks to Ruslan Makhmatkhanov):

* To install the port: cd /usr/ports/devel/py-grab/ && make install clean
* To add the package: pkg_add -r py27-grab

Installation on MacOS
---------------------

See :ref:`installation_linux`

Dependencies to run tests
-------------------------

If you want to run the test suite, then you have to install extra dependencies::

    pip install tornado
    pip install cssselect
    pip install jsonpath_rw
