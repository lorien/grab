import functools
import logging

from weblib.error import ResponseNotValid


def integrity(integrity_func, integrity_errors=(ResponseNotValid,),
              ignore_errors=()):
    """
    Args:
        :param integrity_func: couldb callable or string contains name of
            method to call
    """
    def build_decorator(func):
        @functools.wraps(func)
        def func_wrapper(self, grab, task):
            if isinstance(integrity_func, (list, tuple)):
                int_funcs = integrity_func
            else:
                int_funcs = [integrity_func]
            try:
                for int_func in int_funcs:
                    if isinstance(int_func, str):
                        getattr(self, int_func)(grab)
                    else:
                        int_func(grab)
            except ignore_errors as ex:
                self.stat.inc(ex.__class__.__name__)
                grab.meta['integrity_error'] = ex
                result = func(self, grab, task)
                if result is not None:
                    for event in result:
                        yield event
            except integrity_errors as ex:
                yield task.clone(refresh_cache=True)
                self.stat.inc(ex.__class__.__name__)
                #logging.error(ex)
            else:
                grab.meta['integrity_error'] = None
                result = func(self, grab, task)
                if result is not None:
                    for event in result:
                        yield event
        return func_wrapper
    return build_decorator
