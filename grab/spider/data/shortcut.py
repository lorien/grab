import os
from copy import deepcopy
from urlparse import urlsplit

from .base import Data
from grab.tools.files import hashed_path
from .. import Task
from grab import Grab

# Some day I'll remove this hack
from database import db


def build_image_hosting_referer(url):
    host = urlsplit(url).netloc
    return '.'.join(host.split('.')[-2:])


class MongoObjectImageData(Data):
    def handler(self, url, collection, obj, path_field, base_dir, task_args=None,
                grab_args=None, callback=None):
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
            if grab_args:
                g.setup(**grab_args)
            g.setup(referer=build_image_hosting_referer(url))

            yield Task(
                callback=callback,
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
        for image in obj.get(set_field, []):
            path = hashed_path(image['url'], base_dir=base_dir)
            if os.path.exists(path):
                if path != image['path']:
                    db[collection].update(
                        {'_id': obj['_id'], ('%s.key' % set_field): image['key']},
                        {'$set': {'%s.$.path': path}})
            else:
                kwargs = {}
                if task_args:
                    kwargs = deepcopy(task_args)

                g = Grab()
                g.setup(url=image['url'])
                if grab_args:
                    g.setup(**grab_args)
                g.setup(referer=build_image_hosting_referer(image['url']))

                yield Task(
                    callback=callback,
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

