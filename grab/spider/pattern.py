import os.path
import logging

from grab.spider.task import Task
from grab.tools.files import hashed_path

logger = logging.getLogger('grab.spider.pattern')


class SpiderPattern(object):
    """
    This is base class for Spider class which contains
    methods for automating common task in scraping the typical
    web site, for example, iterating over pagination and fetching images
    associated with some scraped object.
    """

    def process_object_image(self, task_name, collection, obj, image_field, image_url,
                             base_dir, ext='jpg', skip_existing=True):
        path = os.path.join(base_dir, hashed_path(image_url, ext=ext))
        if os.path.exists(path) and skip_existing:
            collection.update({'_id': obj['_id']},
                              {'$set': {'%s_path' % image_field: path,
                                        '%s_url' % image_field: image_url}})
        else:
            self.add_task(Task(task_name, url=image_url, obj=obj, disable_cache=True,
                               image_field=image_field,
                               collection=collection, base_dir=base_dir, ext=ext))

    def generic_task_image(self, grab, task):
        relpath = grab.response.save_hash(task.url, task.base_dir, ext=task.ext)
        path = os.path.join(task.base_dir, relpath)
        task.collection.update({'_id': task.obj['_id']},
                              {'$set': {'%s_path' % task.image_field: path,
                                        '%s_url' % task.image_field: task.url}})

    def process_next_page(self, grab, task, xpath, resolve_base=False, **kwargs):
        """
        Generate task for next page.

        :param grab: Grab instance
        :param task: Task object which should be assigned to next page url
        :param xpath: xpath expression which calculates list of URLS
        :param **kwargs: extra settings for new task object

        Example::

            self.follow_links(grab, 'topic', '//div[@class="topic"]/a/@href')
        """
        try:
            #next_url = grab.xpath_text(xpath)
            next_url = grab.doc.select(xpath).text()
        except IndexError:
            return False
        else:
            url = grab.make_url_absolute(next_url, resolve_base=resolve_base)
            page = task.get('page', 1) + 1
            grab2 = grab.clone()
            grab2.setup(url=url)
            task2 = task.clone(task_try_count=0, grab=grab2, page=page, **kwargs)
            self.add_task(task2)
            return True

    def process_links(self, grab, task_name, xpath,
                      resolve_base=False, limit=None, **kwargs):
        """
        :param grab: Grab instance
        :param xpath: xpath expression which calculates list of URLS
        :param task_name: name of task to generate

        Example::

            self.follow_links(grab, 'topic', '//div[@class="topic"]/a/@href')
        """
        urls = set()
        count = 0
        for url in grab.xpath_list(xpath):
            url = grab.make_url_absolute(url, resolve_base=resolve_base)
            if not url in urls:
                urls.add(url)
                g2 = grab.clone(url=url)
                self.add_task(Task(task_name, grab=g2, **kwargs))
                count += 1
                if limit is not None and count >= limit:
                    break

    # Deprecated methods

    def next_page_task(self, grab, task, xpath, **kwargs):
        """
        DEPRECATED, WILL BE REMOVED

        Return new `Task` object if link that matches the given `xpath`
        was found.
        """

        logger.error('Method next_page_task is deprecated. '
                     'Use process_next_page method instead.')
        nav = grab.xpath_one(xpath, None)
        if nav is not None:
            url = grab.make_url_absolute(nav.get('href'))
            page = task.get('page', 1) + 1
            grab2 = grab.clone()
            grab2.setup(url=url)
            task2 = task.clone(task_try_count=0, grab=grab2, page=page, **kwargs)
            return task2

    def follow_links(self, grab, xpath, task_name, task=None):
        """
        DEPRECATED, WILL BE REMOVED

        Args:
            :xpath: xpath expression which calculates list of URLS

        Example::

            self.follow_links(grab, '//div[@class="topic"]/a/@href', 'topic')
        """
        logger.error('Method follow_links is deprecated. '
                     'Use process_links method instead.')

        urls = []
        for url in grab.xpath_list(xpath):
            #if not url.startswith('http') and self.base_url is None:
            #    raise SpiderError('You should define `base_url` attribute to resolve relative urls')
            url = urljoin(grab.config['url'], url)
            if not url in urls:
                urls.append(url)
                g2 = grab.clone()
                g2.setup(url=url)
                self.add_task(Task(task_name, grab=g2))
