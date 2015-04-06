.. _api_response:

===================================
grab.response: класс ответа сервера
===================================

.. module:: grab.response

.. autoclass:: Response

    .. attribute:: code

        HTTP код ответа

    .. attribute:: head

        HTTP-заголовки ответа в виде текста

    .. attribute:: body

        Тело ответа

    .. attribute:: headers

        HTTP-заголовки ответа в виде словаря

    .. attribute:: time

        Время, затраченное на запрос-ответ

    .. attribute:: url

        URL запрошенного документа. В случае автоматической обработки редиректов он может отличаться от URL запроса.

    .. attribute:: cokies

        Кукисы ответв в виде словаря

    .. attribute:: charset

        Кодировка документа

    .. automethod:: unicode_body
    .. automethod:: copy
    .. automethod:: save
    .. automethod:: save_hash

