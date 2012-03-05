.. _installation:

=========================
Установка библиотеки Grab
=========================

Зависимости
===========

Grab нуждается в двух библиотеках: lxml и pycurl

Grab тестируется под python 2.6

Установка под Linux
===================

Установите зависимости любым удобным для вас способом. Вы можете воспользоваться пакетным менеджером либо утилитами `easy_install` или `pip`::

    pip install pycurl lxml

Далее установите Grab::

    pip install grab


Установка под Windows
=====================

Скачайте и установите lxml и pycurl библиотеки с сайта http://www.lfd.uci.edu/~gohlke/pythonlibs/:

* lxml-2.3.3.win32-py2.6.exe  
* pycurl-7.19.0.win32-py2.6.exe 

Скачайте и установите grab с http://pypi.python.org/pypi/grab/0.3.25:

* качаем tar.gz архив
* распаковываем
* запускаем команду python.exe setup.py install
