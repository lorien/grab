import pickle

from grab import Grab
from tests.util import BaseTestCase


class TestGrab(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

    def test_pickle_grab(self) -> None:
        grab = Grab()
        pickle.dumps(grab)
