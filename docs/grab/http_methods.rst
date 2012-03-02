.. _http_methods:

====================
Методы HTTP-запросов
====================

Выбор метода
============

По-умолчанию, создаётся GET-запрос. Если вы указываете POST-данные, то тип запроса автоматически изменяется на POST::

    g.setup(post={'user': 'root'})
    g.request() # будет сгенерирован POST-запрос

Если вам нужен более экзотический типа запроса, вы можете указать его опцией `method`::

    g.setup(method='PUT')


POST-запрос
===========

Рассмотрим более подробно создание POST-запросов. По-умолчанию, когда вы задаёте `post` опцию, тип запроса меняется на POST, а `Content-Type` становится равен `application/x-www-form-urlencoded`. Опция `post` принимает данные в различных форматах. Если вы передаёте `dict` или список пар значений, то данные будут преобразованы в "key1=value1&key2=value2..." строку. Если же вы передаёте строку, то она будет отпралена в неизменном виде::

    g.setup(post={'user': 'root', 'pwd': '123'})
    g.setup(post=[('user', 'root'), ('pwd', '123')])
    g.setup(post='user=root&pwd=123')

Чтобы отправить POST запрос с `Content-Type` равным `multipart/form-data`, используйте опцию `post_multipart` вместо `post`.

Отправка файлов
===============

Чтобы отправить файл используйте специальный класс :ref:`~grab.base.UploadFile`, а также опцию :ref:`option_post_multipart`::

    g.setup(multipart_post={'foo': bar', 'image': UploadFile('/tmp/image.gif')})

Вы также можете использовать :ref:`~grab.base.UploadFile` в `set_input` методах.  В случае использования метода `submit` для отправки формы, нужная опция (`post` или `multipart_post`) выбирается автоматически::

    g.set_input('file', UploadFile('/path/to/file'))
    g.submit()
