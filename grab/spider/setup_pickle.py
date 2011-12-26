"""
This module provide function setup_pickle which
teaches pickle module to load/unload classmethods.

It works only with classmethods
"""
import copy_reg
import types

def _pickle_method(method):
    func_name = method.im_func.__name__
    cls = method.im_self
    return _unpickle_method, (func_name, cls)

def _unpickle_method(func_name, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(cls)

copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
