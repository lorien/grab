.. _grab_debugging:

Debugging
=========

.. _grab_debugging_logging:

Using logging module
--------------------

The most easy way to see what is going on is to enable DEBUG logging messages. Write
the following code at every start of your program::

    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)

That logging configuration will output to console all logging message, not only from
Grab module but from other modules too. If you are interested only in Grab messages then::

    >>> import logging
    >>> logger = logging.getLogger('grab')
    >>> logger.addHandler(logging.StreamHandler())
    >>> logger.setLevel(logging.DEBUG)

Also you can use a `default_logging` function that configures logging as follows:

* all messages of any level except from Grab modules are printed to console
* all "grab*" messages with level INFO or higher are printed to console
* all "grab*" messages of any level are saved to /tmp/grab.log
* all "grab.network*" messages (usually these are URLs being requested) of any level are saved to /tmp/grab.network.log

Usage of `default_logging` function is simple::

    >>> from grab.tools.logs import default_logging
    >>> default_logging()

.. _grab_debugging_logging_network:

Logging messages about network request
--------------------------------------

For each network request Grab generates the "grab.network" logging message with level DEBUG. Let's look at example::

    [5864] GET http://www.kino-govno.com/movies/rusichi via 188.120.244.68:8080 proxy of type http with authorization    

We can see the requested URL and also that request has 5864 ID, that the HTTP method is GET, that request is passed via proxy with authorization. For each network request Grab uses next ID value from the sequence that is shared by all Grab instances. That does mean that even different Grab instances will generates network loggging messages with unique ID. 

Also you can turn on logging of content of POST requests. Use `debug_post` option::

    >>> g.setup(debug_post=True)

The output will be like this::

    [01] POST http://yandex.ru
    POST request:
    foo                      : bar
    name                     : Ivan

.. _grab_debugging_response_saving:

Saving content of requests and responses
----------------------------------------

You can ask Grab to save the content of each network response to the file
located at the path that is value of `log_file` option::

    >>> g.setup(log_file='log.html')

Of course, each new resposne will overwrite the content of previous response.

If you want to log all traffic then consider to use `log_dir` option that tells Grab to
save contents of all responses to files inside the specified directory. Not that each such
file will contains request ID in its filename. For each response there will be two files XXX.log
and XXX.html. The file XXX.html contains the raw response. If you requested the image or porn movie you'll get its raw content in that file. The file XXX.log contains headers of network response. 
If you configure Grab with `debug=True` option, the file XXX.log will contains also a headers of request.
