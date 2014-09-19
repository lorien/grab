from datetime import datetime
from traceback import format_exc
import os
import time


def save_result(func):
    def decorated(spider_name, *args, **kwargs):
        if not kwargs.get('save_result', False):
            return func(spider_name, *args, **kwargs)
        else:
            from grab.djangoui.grabstat.models import Task

            task = Task(
                task_name=spider_name,
                start_time=datetime.now(),
                pid=os.getpid(),
            )
            task.save()

            def dump_spider_stats(spider):
                now = time.time()
                if not hasattr(spider, '_log_task_timer') \
                        or now - spider._log_task_timer  > 60:
                    spider._log_task_timer = now
                    elapsed = datetime.now() - task.start_time
                    elapsed_time = (elapsed.days * 3600 * 24) + elapsed.seconds
                    Task.objects.filter(pk=task.pk)\
                        .update(spider_stats=spider.render_stats(timing=False),
                                spider_timing=spider.render_timing(),
                                elapsed_time=elapsed_time)

            kwargs['dump_spider_stats'] = dump_spider_stats
            kwargs['stats_object'] = task

            try:
                func_res = func(spider_name, *args, **kwargs)
            except Exception as ex:
                task.error_traceback = format_exc()
                task.is_ok = False
                raise
            else:
                task.spider_stats = func_res['spider_stats']
                task.spider_timing = func_res['spider_timing']
            finally:
                task.is_done = True
                task.end_time = datetime.now()
                elapsed = task.end_time - task.start_time
                task.elapsed_time = (elapsed.days * 3600 * 24) + elapsed.seconds
                task.save()
    return decorated
