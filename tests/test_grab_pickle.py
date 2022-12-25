import pickle

from grab import Grab
from tests.util import BaseTestCase


class TestGrab(BaseTestCase):
    def setUp(self):
        self.server.reset()

    def test_pickle_grab(self):
        grab = Grab()
        pickle.dumps(grab)
