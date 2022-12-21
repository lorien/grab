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
