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

If you use python 2.x then install lxml and pycurl::

    pip install lxml
    pip install pycurl

If you use python 3.x then install lxml and custom version of pycurl::

    pip install lxml
    pip install pip install git+https://github.com/lorien/pycurl

What is the custom pycurl? It is just a pycurl that Ubunty guyes ported to python 3. I've just copied their launchpad.net repo to the github.

After all dependencies has installed you can install the Grab::

    pip install Grab

Installation in Windows
-----------------------

If you use python 2.x then install lxml and custom version of pycurl.

* You can get lxml package here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
* Custom pycurl is here: https://github.com/lorien/grab-files/raw/master/pycurl/pycurl-ssl-7.19.0.win32-py2.7.msi Do not use pycurl from any other source because it could contains a bug that corrupts content of POST requests. I do no know the reason, but then we just compiled pycurl from the source on windows, the resulted package worked fine and did not put trasn in POST requests

If you use python 3.x on Windows then bad news for you: there is no pycurl package for windows python 3 yet. Consider to use linux or python 2 on windows.

After all dependencies has installed you can install the Grab. Download the Grab package from the https://pypi.python.org/pypi/grab, unpack it and run::

    python setup.py install

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
