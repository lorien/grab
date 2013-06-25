import os

from .base import Data
from grab.tools.files import hashed_path
from .. import Task

class MongoObjectImageData(Data):
    def handler(self, url, collection, obj, path_field):


        path = hashed_path(url, base_dir='media/post_image')
        if os.path.exists(path):
            if path != getattr(obj, path_field, None):
                collection.update({'_id': obj['_id']},
                                  {'$set': {path_field: path}})
        else:
            yield Task(
                callback=self.task_handler,
                url=url,
                collection=collection,
                path=path,
                obj=obj,
                path_field=path_field,
                disable_cache=True,
            )

    def task_handler(self, grab, task):
        grab.response.save(task.path)
        task.collection.update({'_id': task.obj['_id']},
                               {'$set': {task.path_field: task.path}})
