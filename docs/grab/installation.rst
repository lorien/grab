.. _installation:

============
Installation
============

Grab is developed for python 2.x environment. It does not support py3k yet.
This could be changed in future. The reason why is Grab works only with 2.x python
is simple: I live in Debian world where python 2.x is default version of python.
The development process of Grab always was a result of implementing features which
I was need for my projects. I have never need a py3k support.

.. _installation_dependencies:

Dependencies
============

Grab architecture is designed as set of layers. In theory you can use
different libraries for network layer. In practice there is only one solution
for network layer: `pycurl <http://pycurl.sourceforge.net/>`_. There were attempts to implement network layer with
Selenium, Requests, Ghost.py: they all are half-ready for use.

Except pycurl you need to install `lxml <http://lxml.de/>`_ library if you want to use form processing
feature or HTML DOM access feature. The lxml is optional dependency. You can use
Grab withou lxml and you'll still be able to create network request and work with
body, cookies, headers of network response.

.. _linux_installation:

Installation on Linux
=====================

The recommended way is to install grab with pip utility::

    $ pip install -U Grab

You can install dependencies also with pip::

    $ pip instal lxml
    $ pip install pycurl

Both lxml and pycurl libraries reqired some development libraries in your system. If you have some problems with installation try to install following libraries before lxml&pycurl installation::

* libxml2-dev
* libxslt1-dev
* libcurl4-openssl-dev

Installation on Windows
=======================

You can find lxml library package here http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml

.. warning::

    Do not download pycurl library from the lfd.uci.edu. The pycurl library on that site has a bug
    (POST requests contains incorrect data).

Please use our own version https://github.com/lorien/grab-files/raw/master/pycurl/pycurl-ssl-7.19.0.win32-py2.7.msi This is
pycurl compiled from the official source without any patches, but it does not has a bug.


Download and install Grab from http://pypi.python.org/pypi/grab:

* download tar.gz archive
* unpack the archive
* run the command `python.exe setup.py install`

You can try to install Grab with easy_install utility (see `details <http://flask.pocoo.org/docs/installation/#pip-and-distribute-on-windows>`_ in Falsk documentation)

Installation on FreeBSD
=======================

You can use pip to install Grab, see :ref:`linux_installation` section above.

You can also install Grab from FreeBSD ports (thanks to Ruslan Makhmatkhanov):

* To install the port: cd /usr/ports/devel/py-grab/ && make install clean
* To add the package: pkg_add -r py27-grab
