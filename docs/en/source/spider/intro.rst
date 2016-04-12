.. _spider_intro:

What is Grab::Spider?
=====================

The Spider is a framework that allow to describe web-site crawler as set of
handlers. Each handler handles only one specific type of web pages crawled on
web-site e.g. home page, user profile page, search results page. Each handler
could spawn new requests which will be processed in turn by other handlers.

The Spider process network requests asynchronously. There is only one process
that handles all network, business logic and HTML-processing tasks. Network
requests are performed by multicurl library. In short, when you create new
network request it is processed by multicurl and when the response is ready,
then the corresponding handler from your spider class is called with result
of network request.

Each handler receives two arguments. First argument is a Grab object, that
contains all data bout network request and response. The second argument is
Task object. Whenever you need to send network request you create Task object.

Let's check out simple example. Let's say we want to go to habrahabr.ru
web-site, read titles of recent news, then for each title find the image on
images.yandex.ru and save found data to the file.

.. code:: python

    # coding: utf-8
    import urllib
    import csv
    import logging

    from grab.spider import Spider, Task

    class ExampleSpider(Spider):
        # List of initial tasks
        # For each URL in this list the Task object will be created
        initial_urls = ['http://habrahabr.ru/']

        def prepare(self):
            # Prepare the file handler to save results.
            # The method `prepare` is called one time before the
            # spider has started working
            self.result_file = csv.writer(open('result.txt', 'w'))

            # This counter will be used to enumerate found images
            # to simplify image file naming
            self.result_counter = 0

        def task_initial(self, grab, task):
            print 'Habrahabr home page'

            # This handler for the task named `initial i.e.
            # for tasks that have been created from the
            # `self.initial_urls` list

            # As you see, inside handler you can work with Grab
            # in usual way i.e. just if you have done network request
            # manually
            for elem in grab.doc.select('//h1[@class="title"]'
                                        '/a[@class="post_title"]'):
                # For each title link create new Task
                # with name "habrapost"
                # Pay attention, that we create new tasks
                # with yield call. Also you can use `add_task` method:
                # self.add_task(Task('habrapost', url=...))
                yield Task('habrapost', url=elem.attr('href'))

        def task_habrapost(self, grab, task):
            print 'Habrahabr topic: %s' % task.url

            # This handler receives results of tasks we
            # created for each topic title found on home page

            # First, save URL and title into dictionary
            post = {
                'url': task.url,
                'title': grab.xpath_text('//h1/span[@class="post_title"]'),
            }

            # Next, create new network request to search engine to find
            # the image related to the title.
            # We pass info about the found publication in the arguments to
            # the Task object. That allows us to pass information to next
            # handler that will be called for found image.
            query = urllib.quote_plus(post['title'].encode('utf-8'))
            search_url = 'http://images.yandex.ru/yandsearch'\
                         '?text=%s&rpt=image' % query
            yield Task('image_search', url=search_url, post=post)

        def task_image_search(self, grab, task):
            print 'Images search result for %s' % task.post['title']

            # In this handler we have received result of image search.
            # That is not image! This is just a list of found images.
            # Now, we take URL of first image and spawn new network
            # request to download the image.
            # Also we pass the info about pulication, we need it be
            # available in next handler.
            image_url = grab.xpath_text('//div[@class="b-image"]/a/img/@src')
            yield Task('image', url=image_url, post=task.post)

        def task_image(self, grab, task):
            print 'Image downloaded for %s' % task.post['title']

            # OK, this is last handler in our spider.
            # We have received the content of image,
            # we need to save it.
            path = 'images/%s.jpg' % self.result_counter
            grab.response.save(path)
            self.result_file.writerow([
                task.post['url'].encode('utf-8'),
                task.post['title'].encode('utf-8'),
                path
            ])
            # Increment image counter
            self.result_counter += 1


    if __name__ == '__main__':
        logging.basicConfig(level=logging.DEBUG)
        # Let's start spider with two network concurrent streams
        bot = ExampleSpider(thread_number=2)
        bot.run()


In this example, we have considered the simple spider. I hope you have got idea
about how it works. See other parts of :ref:`spider_toc` to get detailed description
of spider features.
