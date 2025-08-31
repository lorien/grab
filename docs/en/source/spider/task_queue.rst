.. _spider_task_queue:

Task Queue
==========

.. _spider_task_priority:

Task Priorities
---------------

All new tasks are places into task queue. The Spider get tasks from task queue
when there are free network streams. Each task has priority. Lower number means
higher priority. Task are processed in the order of their priorities: from
highest to lowest. If you do not specify the priority for the new task then it
is assigned automatically. There are two algorithms of assigning default task
priorities:

:random: random priorities
:const: same priority for all tasks

By default random priorities are used. You can control the algorithm of default
priorities with `priority_mode` argument:

.. code:: python
    
    bot = SomeSpider(priority_mode='const')


.. _spider_task_backend:

Tasks Queue Backends
--------------------

You can choose the storage for the task queue. By default, Spider uses python
`PriorityQueue` as storage. In other words, the storage is memory. You can
also used redis and mongo backends.

In-memory backend:

.. code:: python

    bot = SomeSpider()
    bot.setup_queue() # очередь в памяти
    # OR (that is the same)
    bot.setup_queue(backend='memory')


MongoDB backend:

.. code:: python

    bot = SomeSpider()
    bot.setup_queue(backend='mongo', database='database-name')

All arguments except `backend` go to MongoDB connection constructor. You
can setup database name, host name, port, authorization arguments and other
things.

Redis backend:

.. code:: python

    bot = SomeSpider()
    bot.setup_queue(backend='redis', db=1, port=7777)
