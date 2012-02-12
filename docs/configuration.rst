.. _configuration:

Список настроек
===============

**url**
    URL of requested document.

    You can use relative url - it will be joined with the absolute url of previously
    requested document. You are responsible for quoting unsafe symbols in the
    URL.

**timeout**
    Max. time to work with remote document. Default is 15.

**connect_timeout**
    Max. time to wait for the start of response of remote document. Default is 10.

**user_agent**
    Value of User-Agent HTTP header. Default is random choice from set of real-world user agents.

**user_agent_file**
    Path to file which contains User-Agent strings. Grab instance will be configured
    with random user agent from that file.

**method**
    Set the http method. By default POST method is used if ``post`` or ``payload``
    options were configured. In any other case the default method is GET.

    You can specify POST, PUT, DELETE or GET.

**post**
    Sequence of two-value tuples or dictionary or string.

    In case of sequence or dictionary all values are processed in this way:
    * instance of ``UploadFile`` class converted into spercial internal curl object
    * unicode is converted into bytestring
    * ``None`` is converted into empty string

    If option value is a string then it is submitted as is.

**multipart_post**
    Sequence of two-value tuples.

    Similar to post option but send "multipart/form-data" request. 

**headers**
    Extra http headers. The value of this option will be merged with
    default headers which are Accept, Accept-Language, Accept-Charset and Keep-Alive.

**reuse_cookies**
    If True then remember cookies and request them in next requests.
    If False then clear cookies before each request.
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
