.. _grab_debugging:

Debugging
=========


.. _grab_debugging_logging:

Using the logging module
------------------------

The easiest way to see what is going on is to enable DEBUG logging messages.
Write the following code at every entry point to your program::

    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)

That logging configuration will output all logging messages to console, not
just from Grab but from other modules too. If you are interested only
in Grab's messages::

    >>> import logging
    >>> logger = logging.getLogger('grab')
    >>> logger.addHandler(logging.StreamHandler())
    >>> logger.setLevel(logging.DEBUG)

You can also use a `default_logging` function that configures logging as
follows:

* all messages of any level except from Grab modules are printed to console
* all "grab*" messages with level INFO or higher are printed to console
* all "grab*" messages of any level are saved to /tmp/grab.log
* all "grab.network*" messages (usually these are URLs being requested) of any
  level are saved to /tmp/grab.network.log

Usage of `default_logging` function is simple::

    >>> from weblib.logs import default_logging
    >>> default_logging()


.. _grab_debugging_logging_network:

Logging messages about network request
--------------------------------------

For each network request, Grab generates the "grab.network" logging message 
with level DEBUG. Let's look at an example::

    [5864] GET http://www.kino-govno.com/movies/rusichi via 188.120.244.68:8080 proxy of type http with authorization    

We can see the requested URL and also that request has ID 5864, that the HTTP
method is GET, and that the request goes through a proxy with authorization.
For each network request Grab uses the next ID value from the sequence that is
shared by all Grab instances. That does mean that even different Grab instances
will generates network logging messages with unique ID. 

You can also turn on logging of POST request content. Use the `debug_post`
option::

    >>> g.setup(debug_post=True)

The output will be like this::

    [01] POST http://yandex.ru
    POST request:
    foo                      : bar
    name                     : Ivan


.. _grab_debugging_response_saving:

Saving the content of requests and responses
--------------------------------------------

You can ask Grab to save the content of each network response to the file
located at the path passed as the `log_file` option::

    >>> g.setup(log_file='log.html')

Of course, each new resposne will overwrite the content of the previous
response.

If you want to log all traffic, then consider using the `log_dir` option, which
tells Grab to save the contents of all responses to files inside the specified
directory. Note that each such file will contain a request ID in its filename.
For each response, there will be two files: XXX.log and XXX.html. The file
XXX.html contains the raw response. Even if you requested an image or
large movie, you'll get its raw content in that file. The file XXX.log contains
headers of network response.  If you configure Grab with `debug=True`,
the file XXX.log will also contain request headers.
