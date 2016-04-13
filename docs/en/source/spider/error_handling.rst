.. _spider_error_handling:

Spider Error Handling
=====================

Rules of Network Request Handling
---------------------------------

* If request is completed successfully then the corresponding handler is called
* If request is failed due the network error, then the task is submitted back
  to the task queue
* If the request is completed and the handler is called and failed due to any
  error inside the handler then the task processing is aborted. This type of
  errors is not fatal. The handler error is logged and other requests and
  handlers are processed in usual way.


Network Errors
--------------

Network error is:

* error occurred in process of data transmission to or back from the server e.g.
  connection aborted, connection timeout, server does not accept connection and
  so on
* data transmission has been completed but the HTTP status of received document
  differs from 2XX or from 404

Yes, by default documents with 404 status code counts as valid! That makes
sense to me :) If that is not you want then you can configure custom rule to
mark status as valid or failed. You have two ways. 

First way is to use `valid_status` argument in Task constructor. With this
argument you can only extend the default valid status. This arguments accepts
list of additional valid status codes:

.. code:: python

    t = Task('example', url='http://example.com', valid_status=(500, 501, 502))

Second way is to redefine `valid_response_code` method. In this way you can
implement any logic you want. Method accepts two arguments: status code and
task object. Method returns boolean value, `True` means that the status code
is valid:

.. code:: python

    class SomeSpider(Spider):
        def valid_response_code(self, code, task):
            return code in (200, 301, 302)


Handling of Failed Tasks
------------------------

The task failed due to the network error is put back to tas queue. The number
of tries is limited to the `Spider.network_try_limit` and is 10 by default.
The try's number is stored in the `Task.network_try_count`. If
`network_try_count` reaches the `network_try_limit` the task is aborted.

When the task is aborted and there is method with name
`task_<task-name>_fallback` then it is called and receives the failed task as
first argument.

Also, it happens that you need to put task back to task queue even it was not
failed due to the network error. For example, the response contains captcha
challenge or other invalid data reasoned by the anti-scraping protection.
You can control number of such tries. Max tries number is configured by
`Spider.task_try_count`. The try's number is stored in `Task.task_try_count`.
Keep in mind, that you have to increase `task_try_count` explicitly when you
put task back to task queue.

.. code:: python

    def task_google(self, grab, task):
        if captcha_found(grab):
            yield Task('google', url=grab.config['url'],
                       task_try_count=task.task_try_count + 1)

    def task_google_fallback(self, task):
        print 'Google is not happy with you IP address'



Manual Processing of Failed Tasks
---------------------------------

You can disable default mechanism of processing failed tasks and
process failures manually. Use `raw=True` parameter in Task constructor.
If the network request would fail then the grab object passed to the handler
would contain information about failure in two attributes: 
`grab.response.error_code` and `grab.response.error_msg`

See example:

.. code:: python

    class TestSpider(Spider):
        def task_generator(self):
            yield Task('page', url='http://example.com/', raw=True)

        def task_page(self, grab, task):
            if grab.response.error_code:
                print('Request failed. Reason: %s' % grab.response.error_msg)
            else:
                print('Request completed. HTTP code: %d' % grab.response.code)


Error Statistics
----------------

After spider has completed the work or even in the process of working you can
receive the information about number of completed requests, failed requests,
number of specific network errors with method `Spider.render_stats`.
