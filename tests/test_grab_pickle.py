import pickle

from grab import Grab
from tests.util import BaseGrabTestCase


class TestGrab(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_pickle_grab(self):
        grab = Grab()
        pickle.dumps(grab)
