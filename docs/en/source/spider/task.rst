.. _spider_task:

Task Object
===========

Any Grab::Spider crawler is a set of handlers that process network responses.
Each handler can spawn new network requests or just process/save data. 
The spider add each new request to task queue and process this task when there
is free network stream. Each task is assigned a name that defines its type.
Each type of task are handles by specific handler. To find the handler the
Spider takes name of the task and then looks for `task_<name>` method.

For example, to handle result of task named "contact_page" we need to define
"task_contact_page" method:

.. code:: python

        ...
        self.add_task(Task('contact_page', url='http://domain.com/contact.html'))
        ...

    def task_contact_page(self, grab, task):
        ...


Constructor of Task Class
-------------------------

Constructor of Task Class accepts multiple arguments. At least you have to
specify URL of requested document OR the configured Grab object. Next, you
see examples of different task creation. All three examples do the same:

.. code:: python

    # Using `url` argument
    t = Task('wikipedia', url 'http://wikipedia.org/')

    # Using Grab intance
    g = Grab()
    g.setup(url='http://wikipedia.org/')
    t = Task('wikipedia', grab=g)

    # Using configured state of Grab instance
    g = Grab()
    g.setup(url='http://wikipedia.org/')
    config = g.dump_config()
    t = Task('wikipedia', grab_config=config)


Also you can specify these arguments:

:priority: приоритет задания, целое положительное число, чем меньше число, тем выше приоритет.
:disable_cache: не использовать кэш паука для этого запроса, сетевой ответ в кэш сохранён не будет
:refresh_cache: не использовать кэш паука, в случае удачного ответа обновить запись в кэше
:valid_status: обрабатывать обычным способом указанные статусы. По умолчанию обрабатываются все статусы 2xx, а также статус 404.
:use_proxylist: использовать заданный глобально для паука список прокси. По умолчанию  опция включена.


Task Object as Data Storage
---------------------------

If you pass the argument that is unknown then it will be saved in the Task
object. That allows you to pass data between network request/response.

There is `get` method that return value of task attribute or `None` if that
attribute have not been defined.

.. code:: python

    t = Task('bing', url='http://bing.com/', disable_cache=True, foo='bar')
    t.foo # == "bar"
    t.get('foo') # == "bar"
    t.get('asdf') # == None
    t.get('asdf', 'qwerty') # == "qwerty"


Cloning Task Object
-------------------

Sometimes it is usefule to create copy of Task object. For example::

    # task.clone()
    # TODO: example


Setting Up Initial Tasks
------------------------

When you call `run` method of your spider it starts working from initial tasks.
There are few ways to setup initial tasks.


.. _spider_task_initial_urls:

initial_urls
^^^^^^^^^^^^

You can specify list of URLs in `self.initial_urls`. For each URl in this list
the spider will create Task object with name "initial":

.. code:: python

    class ExampleSpider(Spider):
        initial_urls = ['http://google.com/', 'http://yahoo.com/']


.. _spider_task_generator:

task_generator
^^^^^^^^^^^^^^

More flexible way to define initial tasks is to use `task_generator` method.
Its interface is simple, you just have to yield new Task objects.

There is common use case when you need to process big number of URLs from the
file. With `task_generator` you can iterate over lines of the file and yield
new tasks. That will save memory used by the script because you will not read
whole file into the memory. Spider consumes only portion of tasks from
`task_generator`. When there are free networks resources the spiders consumes
next portion of task. And so on.

Example:

.. code:: python

    class ExampleSpider(Spider):
        def task_generator(self):
            for line in open('var/urls.txt'):
                yield Task('download', url=line.strip())


Explicit Ways to Add New Task
-----------------------------

Adding Tasks With add_task method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use `add_task` method anywhere, even before the spider have started working:

.. code:: python

    bot = ExampleSpider()
    bot.setup_queue()
    bot.add_task('google', url='http://google.com')
    bot.run()


Yield New Tasks
^^^^^^^^^^^^^^^

You can use yield statement to add new tasks in two places. First, in
:ref:`spider_task_generator`. Second, in any handler. Using yield is
completely equal to using `add_task` method. The yielding is just a bit
more beautiful:

.. code:: python

    class ExampleSpider(Spider):
        initial_urls = ['http://google.com']
        
        def task_initial(self, grab, task):
            # Google page was fetched
            # Now let's download yahoo page
            yield Task('yahoo', url='yahoo.com')

        def task_yahoo(self, grab, task):
            pass


.. _spider_default_grab_instance:

Default Grab Instance
---------------------

You can control the default config of Grab instances used in spider tasks.
Define the `create_grab_instance` method in your spider class:

.. code:: python

    class TestSpider(Spider):
        def create_grab_instance(self, **kwargs):
            g = super(TestSpider, self).create_grab_instance(**kwargs)
            g.setup(timeout=20)
            return g

Be aware, that this method allows you to control only those Grab instances
that were created automatically. If you create task with explicit grab instance
it will not be affected by `create_grab_instance_method`:

.. code:: python

    class TestSpider(Spider):
        def create_grab_instance(self, **kwargs):
            g = Grab(**kwargs)
            g.setup(timeout=20)
            return g

        def task_generator(self):
            g = Grab(url='http://example.com')
            yield Task('page', grab=g)
            # The grab instance in the yielded task
            # will not be affected by `create_grab_instance` method.


.. _spider_updating_any_grab_instance:

Updating Any Grab Instance
--------------------------

With method `update_grab_instance` you can update any Grab instance, even those
instances that you have passed explicitly to the Task object. Be aware, that
any option configured in this method overwrites the previously configured
option.

.. code:: python

    class TestSpider(Spider):
        def update_grab_instance(self, grab):
            grab.setup(timeout=20)

        def task_generator(self):
            g = Grab(url='http://example.com', timeout=5)
            yield Task('page', grab=g)
            # The effective timeout setting will be equal to 20!
