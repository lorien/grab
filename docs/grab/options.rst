.. _configuration:

Полный список настроек
======================

О том как изменять настройки, читайте в :ref:`grab_customization`.

Настройки
---------

**url**
    Сетевой запрашиваемого документа. Можно использовать относительный адрес, в таком
    случае полный адрес будет получен путём соединения с полным адресом предыдущего
    сетевого запроса. Grab ожидает адрес в корректном формате. Это ваша обязанность -
    преобразовать все нестдартные символы в escape-последовательности (`RFC 2396 <http://www.ietf.org/rfc/rfc2396.txt>`_).

**timeout**
    Максимальное время, отведённое на получение документа. По-умолчанию, 15 секунд.

**connect_timeout**
    Максимальное время, отведённое на ожидание начала получения данных от сервера.
    По-умолчанию, 10 секунд.

**user_agent**
    Содержимое HTTP-заголовка `User-Agent`. По-умолчанию, случайный выбор из множества
    реальных `User-Agent` значений, заложенных в Grab.

**user_agent_file**
    Путь к текстовому файлу с `User-Agent` строками. При указании этой опции, будет
    выбран случайный вариант из указанного файла.

**method**
    Выбор метода HTTP-запроса. По-умолчанию, используется `GET` метод. Если заданы
    непустые опции `post` или `multipart_post`, то используется `POST` метод.

    Возможные варианты: `GET`, `POST`, `PUT`, `DELETE`.

**post**
    Указание данных для отправки `POST` методом.
    Значением опции может быть словарь или последовательность двузначных последовательной
    или просто строка.
    
    В случае словаря или последовательности, каждое значение обрабатывается по следующему алгоритму:
    * объекты класса `UploadFile` преобразовываются во внутреннее представление библиотеки pycurl
    * unicode-строки преобразовываются в байтовые строки
    * `None`-значения преобразовываются в пустые строки

    Если значением `post` опции является строка, то она передаётся в сетевой запрос без изменений.

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
