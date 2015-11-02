import functools
import logging

from weblib.error import ResponseNotValid


def integrity(integrity_func, retry_errors=(ResponseNotValid,)):
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
            except retry_errors as ex:
                yield task.clone(refresh_cache=True)
                error_code = ex.__class__.__name__.replace('_', '-')
                self.stat.inc('integrity:%s' % error_code)
            except Exception as ex:
                raise
            else:
                result = func(self, grab, task)
                if result is not None:
                    for event in result:
                        yield event
        func_wrapper._original_func = func
        return func_wrapper
    return build_decorator
