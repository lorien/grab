# WTF: Honestrly, I do not remember what it does.
# Commenting for now because it is too sophisticated for annotating with type hints
# import functools
#
# from grab.base import Grab
# from grab.error import ResponseNotValid
# from grab.spider.task import Task
#
#
# def integrity(integrity_func, retry_errors=(ResponseNotValid,)):
#    # Args:
#    #    :param integrity_func: couldb callable or string contains name of
#    #        method to call
#    def build_decorator(func):
#        @functools.wraps(func)
#        def func_wrapper(self, grab: Grab, task: Task):
#            if isinstance(integrity_func, (list, tuple)):
#                int_funcs = integrity_func
#            else:
#                int_funcs = [integrity_func]
#            try:
#                for int_func in int_funcs:
#                    if isinstance(int_func, str):
#                        getattr(self, int_func)(grab)
#                    else:
#                        int_func(grab)
#            except retry_errors as ex:
#                yield task.clone()
#                error_code = ex.__class__.__name__.replace("_", "-")
#                self.stat.inc("integrity:%s" % error_code)
#            else:
#                result = func(self, grab, task)
#                if result is not None:
#                    yield from result
#
#        # func_wrapper._original_func = func  # pylint: disable=protected-access
#        return func_wrapper
#
#    return build_decorator
