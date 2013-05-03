import os
import shutil
import tempfile
import functools

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

# Global variable which is used in all tests to build
# Grab instance with specific transport layer
GRAB_TRANSPORT = None

def prepare_test_environment():
    global TMP_DIR, TMP_FILE

    TMP_DIR = tempfile.mkdtemp()
    TMP_FILE = os.path.join(TMP_DIR, '__temp')


def clear_test_environment():
    remove_directory(TMP_DIR)


def remove_directory(path):
    for root, dirs, files in os.walk(path):
        for fname in files:
            os.unlink(os.path.join(root, fname))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))


def ignore_transport(transport):
    """
    If test function is wrapped into this decorator then
    it should not be tested if test is performed for
    specified transport
    """

    def wrapper(func):
        @functools.wraps(func)
        def test_method(*args, **kwargs):
            if GRAB_TRANSPORT == transport:
                return
            else:
                func(*args, **kwargs)
        return test_method
    return wrapper


def only_transport(transport):
    """
    If test function is wrapped into this decorator then
    it should be called only for specified transport.
    """

    def wrapper(func):
        @functools.wraps(func)
        def test_method(*args, **kwargs):
            if GRAB_TRANSPORT == transport:
                func(*args, **kwargs)
            else:
                return
        return test_method
    return wrapper
