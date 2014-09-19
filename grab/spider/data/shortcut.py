import os
from copy import deepcopy
from urlparse import urlsplit
import imghdr
from StringIO import StringIO

from grab.spider.data.base import Data
from grab.tools.files import hashed_path
from grab.spider.task import Task
from grab import Grab


def build_image_hosting_referer(url):
    from database import db

    host = urlsplit(url).netloc
    return '.'.join(host.split('.')[-2:])


def image_handler(grab, task):
    from database import db

    if grab.response.code == 200:
        if len(grab.response.body):
            if imghdr.what(StringIO(grab.response.body)):
                grab.response.save(task.path)
                db[task.collection].update({'_id': task.obj['_id']},
                                           {'$set': {task.path_field: task.path}})


def image_set_handler(grab, task):
    from database import db

    if grab.response.code == 200:
        if len(grab.response.body):
            if imghdr.what(StringIO(grab.response.body)):
                grab.response.save(task.path)
                db[task.collection].update(
                    {'_id': task.obj['_id'], ('%s.url' % task.set_field): task.image['url']},
                    {'$set': {('%s.$.path' % task.set_field): task.path}}
                )   


class MongoObjectImageData(Data):
    def handler(self, url, collection, obj, path_field, base_dir, task_args=None,
                grab_args=None, callback=None):
        from database import db
        path = hashed_path(url, base_dir=base_dir)
        if os.path.exists(path):
            if path != obj.get(path_field, None):
                db[collection].update({'_id': obj['_id']},
                                      {'$set': {path_field: path}})
        else:
            kwargs = {}
            if task_args:
                kwargs = deepcopy(task_args)

            g = Grab()
            g.setup(url=url)
            g.setup(referer=build_image_hosting_referer(url))
            if grab_args:
                g.setup(**grab_args)

            yield Task(
                callback=callback or image_handler,
                grab=g,
                collection=collection,
                path=path,
                obj=obj,
                path_field=path_field,
                disable_cache=True,
                backup=g.dump_config(),
                **kwargs
            )


class MongoObjectImageSetData(Data):
    def handler(self, collection, obj, set_field, base_dir, task_args=None,
                grab_args=None, callback=None):
        from database import db

        for image in obj.get(set_field, []):
            path = hashed_path(image['url'], base_dir=base_dir)
            if os.path.exists(path):
                if path != image['path']:
                    db[collection].update(
                        {'_id': obj['_id'], ('%s.url' % set_field): image['url']},
                        {'$set': {('%s.$.path' % set_field): path}})
            else:
                kwargs = {}
                if task_args:
                    kwargs = deepcopy(task_args)

                g = Grab()
                g.setup(url=image['url'])
                g.setup(referer=build_image_hosting_referer(image['url']))
                if grab_args:
                    g.setup(**grab_args)

                yield Task(
                    callback=callback or image_set_handler,
                    grab=g,
                    collection=collection,
                    path=path,
                    obj=obj,
                    image=image,
                    set_field=set_field,
                    disable_cache=True,
                    backup=g.dump_config(),
                    **kwargs
                )

