from grab.spider import Spider
from test.util import BaseGrabTestCase, build_spider


class SpiderMetaTestCase(BaseGrabTestCase):

    def test_root_spider_class(self):
        self.assertEqual(Spider.Meta.abstract, True)

    def test_inherited_class(self):
        class Child(Spider):
            pass
        self.assertEqual(Child.Meta.abstract, False)

        class Child(Spider):
            class Meta:
                abstract = True
        self.assertEqual(Child.Meta.abstract, True)

        class ChildOfChild(Child):
            pass
        self.assertEqual(ChildOfChild.Meta.abstract, False)

        class ChildOfChild(Child):
            class Meta:
                abstract = True
        self.assertEqual(ChildOfChild.Meta.abstract, True)

    def test_meta_inheritance(self):
        class SomeSpider(Spider):
            class Meta:
                foo = 'bar'

        class Child(SomeSpider):
            pass

        self.assertEqual(Child.Meta.foo, 'bar')

    def test_explicit_existence_of_abstract(self):
        class SomeSpider(Spider):
            class Meta:
                foo = 'bar'

        self.assertEqual(SomeSpider.Meta.abstract, False)
