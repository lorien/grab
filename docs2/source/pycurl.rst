.. _pycurl:

Pycurl Hints
============

Grab can use different network libraries to send and receieve network queries. At the moment only pycurl is fully supported. In this document I want to share some things that can help you to get more from pycurl and from Grab.

Asynchronous DNS Resolving
--------------------------

Pycurl allows you to drive network requests asynchronously with multicurl interface. Unfortunatelly, by default multicurl do not handle DNS requests asynchronously. Than means that every DNS request block other network activity. You can manage it with building curl library from the source and configuring it to use ares library that knows how to do async. DNS requests.

First, you need to download curl sources from http://curl.haxx.se/download.html. Then unpack source code and run the command::

    $ ./configure --prefix=/opt/curl --enable-ares

We use custom prefix because we dot not mix our custom curl lib. with curl lib that could be already installed in your system. Do not forget to install cares packages before configuring curl with ares::

    $ apt-get install libc-ares-dev

If ./configure command has finished successfuly then run::

    $ make
    $ make install

Now you have customized curl library files at /opt/culr/lib

To let your python script now that you want to use custom curl lib use the following feature::

    $ LD_LIBRARY_PATH="/opt/curl/lib" python your_script.py

You can manually check that you use curl lib with ares support::

    >>> import pycurl
    >>> pycurl.version
    'libcurl/7.32.0 OpenSSL/1.0.1e zlib/1.2.7 c-ares/1.10.0 libidn/1.25'

You should see something like "c-ares/1.10.0" if you made things well done.

Supported Protocols
-------------------

By default, pycurl support tons of protocols including STMP, POP3, SSH, media streams, FTP. If you do not need all this crap you can disable it on the configure stage. Here is example of what you can do::

    ./configure --without-libssh2 --disable-ipv6 --disable-ldap --disable-ldaps\
                --without-librtmp --disable-rtsp --disable-ftp --disable-dict\
                --disable-telnet --disable-tftp --disable-pop3 --disable-imap\
                --disable-smtp --disable-gopher --without-winssl --without-darwinssl\
                --without-winidn

To see all aviable options just run the command::
    
    ./configure --help


Python 3 Support
----------------

If you are Ubuntu user then you can just use pycurl that is installed by you package manager. If you are a user of another linux distribution then (as far as I know) the only way for you to use pycurl in py3k is to download patched pycurl sources and install it manually. Good news, it is quite easy::

    pip install git+http://github.com/lorien/pycurl

This command download patched pycurl and install it in to your system. I've just copied the patched pycurl sources from the launchad repository of ubunty version of pycurl package. I beilive it is more easy install pycurl from github than from launchpad.


Multicurl and SOCKS proxy
-------------------------

This combination just does not work. Use HTTP procies with multicurl.
