.. _grab_tutorial:

Введение в Grab
===============

Для начала нужно проимпортировать нужные вещи::

    from grab import Grab

Теперь создадим рабочий объект::

    g = Grab()

Запросим главную страницу сайта livejournal::

    g.go('http://livejournal.com')

И выведем содержимое тэга title::

    print g.xpath_text('//title')

Если вы хотите отправить POST-запрос, это можно сделать так::

    g.setup(post={'key1': 'value1})
    g.go('http://...')
    
Посмотреть кукисы, заголовки, код ответы можно в объекте `response`::

    g.go('http://...')
    print g.response.cookies['sid']
    print g.response.headers['Content-Type']
    print g.response.code

По-умолчанию, Grab сам обрабатывает кукисы. Например, если вы залогинитесь на
какой-либо сайт, сессия будет поддерживаться автоматически.

С помощью Grab удобно обрабатывать формы::

   g.go('some log-in page')
   g.set_input('user', 'foo')
   g.set_input('password', 'bar')
   g.submit()
   
Вот так можно найти информацию в теле ответа по XPATH::

   print g.xpath('//div[@id="error"]').text_content()
   
А так можно пробежаться по элементам::

   for elem in g.xpath_list('//h3'):
       print elem.text
       
Об этих и многих других вещах читайте в :ref:`grab_toc`
