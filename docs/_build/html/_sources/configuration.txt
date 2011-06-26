.. _configuration:

=============
Configuration
=============

You can configure grab using ``setup`` method::

    g = Grab()
    g.setup(opt1=val1, opt2=val2)

You can pass configuration to constructor::

    g = Grab(opt1=val1, opt2=val2)

You can pass configuration to ``request`` method::

    g = Grab()
    g.request(opt1=val1, opt2=val2)


=================
Available options
=================

**url**
    URL of requested document.

    You can use relative url - it will be joined with the absolute url of previously
    requested document. Special symbols in URL should be properly quoted.

**timeout**
    Max. time to work with remote document. Default is 15.

**connect_timeout**
    Max. time to wait for the start of response of remote document. Default is 10.

**user_agent**
    Value of User-Agent HTTP header. Default is random choice from set of real-world user agents.

    See "grab.user_agents" module.

**debug**
    True value enable debug mode which save request headers and make them available
    via ``request_header`` attribute of grab instance.

**method**
    Set the http method. By default POST method is used if ``post`` or ``payload``
    options were configured. In any other case the default method is GET.

    You can specify POST, PUT, DELETE or GET.

**post**
    Sequence of two-value tuples or dictionary.

    If value is unicode then it is converted to byte string using value of 
    ``charset`` option.

**payload**
    Raw value to send in POST or PUT request.

**headers**
    Extra http headers. The value of this option will be merged with
    default headers which are Accept, Accept-Language, Accept-Charset and Keep-Alive.

**reuse_cookies**
    If true then remember cookies and request them in next requests.
    If false then clear cookies before each request.
    Default: True

**cookies**
    Explicitly specify cookies to send in the request. If ``reuse_cookies`` option
    is enabled then value of ``cookies`` will be merged with remembered cookies.

**referer**
    Set Referrer header.
    
    Default: URL of previous request.

**reuse_referer**:
    Set Referer header to the URL of previous request.

    Default: True

**proxy**
    Proxy address in format "server:port"

**proxy_userpwd**
    Access credentials in format "username:password"

**proxy_type**
    Type of proxy. Available values: http, socks4, socks5

**encoding**
    WTF? What is charset and what is encoding options?

**charset**
    Charset of remote document. Charset value will be used in encoding request data and
    in parsing of response data.

**guess_encodings**
    List of charsets which will be tried to build the unicode version of the response document.

**log_file**
    File to log the response body.

    Default: None

**log_dir**
    Directory to save response bodies. Each response is saved in two documents. XX.log contains
    HTTP headers of the response. XX.html contains the body of response. XX is a number. Each request
    has a number. First request hasnumber 1, second request has number 2 and so on. You can see number
    of requests in the console output if you setup your script to display logging messages of DEBUG level.

**follow_refresh**
    Follow the url in <meta refresh> tag.

**nohead**
    Do not process HTTP headers of the response. This mean that processing of response will
    be broken as soon as possible.

**nohead**
    Do not process body of request. That works for request of any kind, not only for PUT.
    This makes sense if you want to reduce traffic usage.

**debug_post**
    Output to console the content of POST requests.

**cookiefile**
    Before each request load cookies from this file. After each request save received cookies to 
    this file. Cookies in this file could be in Netscape/Mozilla format or just at HTTP-headers dump.
