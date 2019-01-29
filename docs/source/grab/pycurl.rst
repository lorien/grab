.. _pycurl:

Pycurl Tips
===========


Asynchronous DNS Resolving
--------------------------

Pycurl allows you to drive network requests asynchronously with the multicurl interface.
Unfortunately, by default multicurl do not handle DNS requests asynchronously. Than means that every DNS request blocks other network activity.
You can manage it by building curl from source and configuring it to use the ares library, which knows how to do asynchronous DNS requests.

First, you need to download curl sources from http://curl.haxx.se/download.html. Then unpack source code and run the command::

    $ ./configure --prefix=/opt/curl --enable-ares

We use a custom prefix because we do not want to mix up our custom curl with the curl lib that could be already installed in your system.
Do not forget to install cares packages before configuring curl with ares::

    $ apt-get install libc-ares-dev

If ./configure command has finished successfully, then run::

    $ make
    $ make install

Now you have customized the curl library files at /opt/curl/lib.

To let your python script know that you want to use this custom curl lib, use the following feature::

    $ LD_LIBRARY_PATH="/opt/curl/lib" python your_script.py

You can manually check that you used a curl compiled with ares support::

    >>> import pycurl
    >>> pycurl.version
    'libcurl/7.32.0 OpenSSL/1.0.1e zlib/1.2.7 c-ares/1.10.0 libidn/1.25'

You should see something like "c-ares/1.10.0" if everything was correct.


Supported Protocols
-------------------

By default, pycurl supports a ton of protocols including SMTP, POP3, SSH, media streams, and FTP.
If you do not need all this crap, you can disable it at the configure stage. Here is example of what you can do::

    ./configure --without-libssh2 --disable-ipv6 --disable-ldap --disable-ldaps\
                --without-librtmp --disable-rtsp --disable-ftp --disable-dict\
                --disable-telnet --disable-tftp --disable-pop3 --disable-imap\
                --disable-smtp --disable-gopher --without-winssl --without-darwinssl\
                --without-winidn

To see all available options, just run the command::
    
    ./configure --help


Multicurl and SOCKS proxy
-------------------------

This combination just does not work. Use HTTP proxies with multicurl.
