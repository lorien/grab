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

    bot = SomeSpider() # task queue is stored in memory
    # OR (that is the same)
    from grab.spider.queue_backend.memory import MemoryTaskQueue

    bot = SomeSpider(task_queue=MemoryTaskQueue())


MongoDB backend:

.. code:: python

    from grab.spider.queue_backend.mongodb import MongodbTaskQueue

    bot = SomeSpider(task_queue=MongodbTaskQueue())

Redis backend:

.. code:: python

    from grab.spider.queue_backend.redis import RedisTaskQueue

    bot = SomeSpider(task_queue=RedisTaskQueue())
