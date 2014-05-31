.. _grab_installation:

Installation
============

To use grab you need to install Grab package and all its dependencies. Although python distribution system allows to specify dependcy list to install automatically, you need to install depencies manually, they will not be installed automatically when you just install one Grab package. The reason is that you need to install different version of libraries for different python branches. Also none of dependencies are mandatory.

Recommended dependency list
---------------------------

To gain access to all power of grab you should install lxml and pycurl libraries. See the section below corresponding to your OS

.. _installation_linux:

Installation in Linux
---------------------

1) Install lxml::

    pip install lxml

If you have build issues try to install dependencies (debian/ubuntu example)::

    sudo apt-get install libxml2-dev libxslt-dev

2) Install pycurl::

    pip install pycurl

3) Finally, install Grab::

    pip install Grab

Installation in Windows
-----------------------

1) Install lxml

You can get lxml package here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

2) Install pycurl

You can get pycurl package here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

3) Install Grab

Download the Grab package from the https://pypi.python.org/pypi/grab, unpack it and run::

    python setup.py install

If you use python of 2.X version then you could get an error while using `python setup.py install`. There is a bug in python 2.7.6 version. Delete it, download python of 2.7.5 version and try to install Grab again.

Also you can install Grab via pip. If you have no pip installed, install pip first. Download file get-pip.py from https://bootstrap.pypa.io/get-pip.py and then run command::

    python get-pip.py

Now you can install Grab via pip with command::

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

If you want to run test suit then you have to install extra dependencies::

    pip install tornado
    pip install cssselect
    pip install jsonpath_rw
