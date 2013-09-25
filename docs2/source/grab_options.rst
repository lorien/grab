.. _grab_options:

Grab Options
============

To get info about how to setup Grab instance please go to :ref:`grab_configuration`.


.. _option_url:

url
---

:Type: string
:Default: None

The URL of requested web page. You can use relative URLS, in that case Grab will build
the absolute url by joining the relative URL with the URL or previously requested document.
Be aware, that Grab does not automatically escapes the unsafe characters in the URL. This is a design feature. You can use `urllib.quote` and `urllib.quote_plus` functions to make your URLs safe.

More info about valid URLs is in `RFC 2396 <http://www.ietf.org/rfc/rfc2396.txt>`_.


.. _option_timeout:

timeout
-------

:Type: int
:Default: 15

Maximal time to network operation. If it exeeds the GrabNetworkTimeout is raised.

.. _option_connect_timeout:

connect_timeout
---------------

:Type: int
:Default: 10

Maximal time of operation of connection to remote server and getting initial response.
If it exeeds then the GrabNetworkTimeout is raised

.. _option_user_agent:

user_agent
----------

:Type: string
:Default: см. выше

The content of "User-Agent" HTTP-header. By-default, Grab randomly chooses a user agent
from the list of real user agents that is built into Grab package.

.. _option_user_agent_file:

user_agent_file
---------------

:Type: string
:Default: None

Path to the text file with User-Agent strings. If that options is specified then
grab randomly choose one line from that file.

.. _option_method:

method
------

Выбор метода HTTP-запроса. По-умолчанию, используется `GET` метод. Если заданы
непустые опции `post` или `multipart_post`, то используется `POST` метод.
Возможные варианты: `GET`, `POST`, `PUT`, `DELETE`.

:Type: string
:Default: "GET"

.. _option_post:

post
----

Данные для отправки запроса методом `POST`.
Значением опции может быть словарь или последовательность пар значений  или просто строка.
В случае словаря или последовательности, каждое значение обрабатывается по следующему алгоритму:
* объекты класса `UploadFile` преобразовываются во внутреннее представление библиотеки pycurl
* unicode-строки преобразовываются в байтовые строки
* `None`-значения преобразовываются в пустые строки

Если значением `post` опции является строка, то она передаётся в сетевой запрос без изменений.

:Type: sequence or dict or string
:Default: None

.. _option_multipart_post:

multipart_post
--------------

Данные для отправки запроса методом `Post`.
Значением опции может быть словарь или последовательность пар значений.
Данные запроса будут отформатированы в соотвествии с методом "multipart/form-data".

:Type: sequence or dict
:Default: None

.. _option_headers:

headers
-------

Дополнительные HTTP-заголовки. Значение этой опции будут склеено с заголовками,
которые Grab отправляет по-умолчанию. Смотрите подробности в :ref:`request_headers`.

:Type: dict
:Default: None

.. _option_reuse_cookies:

reuse_cookies
-------------

Если `True`, то кукисы из ответа сервера будут запомнены и отосланы в последующем
запросе на сервер. Если `False` то кукисы из ответа сервера запоминаться не будут.

:Type: bool
:Default: True

.. _option_cookies:

cookies
-------

Кукисы для отправки на сервер. Если включена также опция `reuse_cookies`, то
кукисы из опции `cookies` будут склеены с кукисами, запомненными из ответов
сервера.

:Type: dict
:Default: None

.. _option_cookiefile:

cookiefile
----------

Перед каждым запросом Grab будет считывать кукисы из этого файла и объединять с теми, что он уже помнит. После каждого запроса, Grab будет сохранять все кукисы в указанный файл.

Формат данных в файле: JSON-сериализованный словарь.

.. _option_referer:

referer
-------

Указание `Referer` заголовка. По-умолчанию, Grab сам формирует этот заголовок
из адреса предыдущего запроса.

:Type: string
:Default: см. выше

.. _option_reuse_referer:

reuse_referer
-------------

Если `True`, то использовать адрес предыдущего запроса для формирования заголовка
`Refeer`.

:Type: bool
:Default: True

.. _option_proxy:

proxy
-----

Адрес прокси-сервера в формате "server:port".

:Type: string
:Default: None

.. _option_proxy_userpwd:

proxy_userpwd
-------------

Данные авторизации прокси-сервера в формате "username:password".

:Type: string
:Default: None

.. _option_proxy_type:

proxy_type
----------

Тип прокси-сервера. Возможные значения: "http", "socks4" и "socks5".

:Type: string
:Default: None

.. _option_encoding:

encoding
--------

Метод сжатия трафика. По-умолчанию, значение этой опции равно "gzip".  С некоторыми серверами возможны проблемы в работе pycurl, когда gzip включен.  В случае проблем передайте в качестве значения опции пустую строку,
чтобы выключить сжатие.

:Type: string
:Default: "gzip"

.. _option_charset:

charset
-------

Указание кодировки документа. По-умолчанию, кодировка определяется автоматически.
Если определение кодировки проходит неправильно, вы можете явно указать нужную кодировку.
Значение кодировки будет использовано для приведения содержимого документ в unicode-вид,
а также для кодирования строковых не-ascii значений в `POST` данных.

:Type: string
:Default: None

.. _option_log_file:

log_file
--------

Файл для сохранения полученного с сервера документа. Каждый новый запрос будет
перезатить сохранённый ранее документ.

:Type: string
:Default: None

.. _option_log_dir:

log_dir
-------

Директория для сохранения ответов сервера. Каждый ответ сохраняется в двух файлах:
* XX.log содержит HTTP-заголовки запроса и ответа
* XX.html содержите тело ответа
XX - это номер запроса.
Смотрите подробности в :ref:`grab_debugging`.

:Type: string
:Default: None

.. _option_follow_refresh:

follow_refresh
--------------

Автоматическая обработка тэга <meta http-equiv="refresh">.

:Type: bool
:Default: False

.. _option_follow_location:

follow_location
---------------

Автоматическая обработка редиректов в ответах со статусом 301 и 302.

:Type: bool
:Default: True

.. _option_nobody:

nobody
------

Игнорирование тела ответа сервера. Если опция включена, то соединение сервером будет
разорвано после получения всех HTTP-заголовков ответа. Эта опция действует для любого метода:
GET, POST и т.д.

:Type: bool
:Default: False

.. _option_body_maxsize:

body_maxsize
------------

Ограничение на количество принимаемых данных от сервера.

:Type: int
:Default: None

.. _option_debug_post:

debug_post
----------

Вывод через logging-систему содержимого POST-запросов.

:Type: bool
:Default: False

.. _option_hammer_mode:

hammer_mode
-----------

Режим повторных запросов. Смотрите подробности в :ref:`hammer_mode`.

:Type: bool
:Default: False

.. _option_hammer_timeouts:

hammer_timeouts
---------------

:Type: list
:Default: ((2, 5), (5, 10), (10, 20), (15, 30))

Настройка таймаутов для режима повторных запросов.

.. _option_userpwd:

userpwd
-------

Имя пользователя и пароль для прохождения http-авторизации. Значение опции - это строка вида "username:password"

:Type: string
:Default: None


.. _option_lowercased_tree:

lowercased_tree
---------------

Приведение HTML-код документа к нижнему регистру перед построением DOM-дерева. Эта опция не влияет на содержимое `response.body`.

:type: bool
:Default: False

.. _option_strip_null_bytes:

strip_null_bytes
----------------

Удаление нулевых байтов из HTML-кода документа перед построением DOM-дерева. Эта опция не влияет на содержимое `response.body`. Если в теле документа встретится нулевой байт, то библиотека LXML построит DOM-дерево только по фрагменту, следующему до первого нулевого байта.

:Type: bool
:Default: True
