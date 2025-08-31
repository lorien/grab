.. _installation:

=========================
Установка библиотеки Grab
=========================

Установка под Linux
===================

Установите зависимости любым удобным для вас способом. Вы можете воспользоваться пакетным менеджером либо утилитами `easy_install` или `pip`::

    pip install pycurl lxml

Если у вас есть проблемы при установке lxml, возможно, вам нужно установить дополнительные пакеты. Пример для Debian/Ubuntu систем::

    sudo apt-get install libxml2-dev libxslt-dev

Далее установите Grab::

    pip install grab


Установка под Windows
=====================

Скачайте и установите lxml библиотеку с сайта http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml:

Скачайте и установите pycurl библиотеку с сайта http://www.lfd.uci.edu/~gohlke/pythonlibs/#pycurl:

Скачайте и установите grab с http://pypi.python.org/pypi/grab:

* качаем tar.gz архив
* распаковываем
* запускаем команду python.exe setup.py install

Если у вас python 2.7.6, то команда `python setup.py install` выполнится с ошибкой из-за бага в версии python 2.7.6. Вам нужно удалить Python версии 2.7.6 и установить версию 2.7.5
