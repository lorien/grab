from grab.spider import Spider
from tests.util import BaseGrabTestCase


class SpiderMetaTestCase(BaseGrabTestCase):

    def test_root_spider_class(self):
        self.assertEqual(Spider.Meta.abstract, True)

    def test_inherited_class(self):
        class Child(Spider):
            pass

        self.assertEqual(Child.Meta.abstract, False)

        class AnotherChild(Spider):
            # pylint: disable=no-init
            class Meta:
                abstract = True

        self.assertEqual(AnotherChild.Meta.abstract, True)

        class ChildOfChild(Child):
            pass

        self.assertEqual(ChildOfChild.Meta.abstract, False)

        class AnoterhChildOfChild(Child):
            # pylint: disable=no-init
            class Meta:
                abstract = True

        self.assertEqual(AnoterhChildOfChild.Meta.abstract, True)

    def test_meta_inheritance(self):
        class SomeSpider(Spider):
            # pylint: disable=no-init
            class Meta:
                some_foo = 'bar'

        class Child(SomeSpider):
            pass

        self.assertEqual(Child.Meta.some_foo, 'bar')

    def test_explicit_existence_of_abstract(self):
        class SomeSpider(Spider):
            # pylint: disable=no-init
            class Meta:
                some_foo = 'bar'

        self.assertEqual(SomeSpider.Meta.abstract, False)
