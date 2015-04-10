# coding: utf-8
from json import loads

from weblib.structured import Structure as x

from test.util import build_grab
from test.util import BaseGrabTestCase


XML = b'''
    <issue index="2">
        <title>XML today</title>
        <date>12.09.98</date>
        <about>XML</about>
        <home-url>www.j.ru/issues/</home-url>
        <number>448</number>
        <detail>
            <description>

                issue 2
                detail description

            </description>
            <number>445</number>
        </detail>
        <articles>
            <article ID="3">
                <title>Issue overview</title>
                <url>/article1</url>
                <hotkeys>
                    <hotkey>language</hotkey>
                    <hotkey>marckup</hotkey>
                    <hotkey>hypertext</hotkey>
                </hotkeys>
                <article-finished/>
            </article>
            <article>
                <title>Latest reviews</title>
                <url>/article2</url>
                <author ID="3"/>
                <hotkeys>
                    <hotkey/>
                </hotkeys>
            </article>
            <article ID="4">
                <title/>
                <url/>
                <hotkeys/>
            </article>
        </articles>
    </issue>
'''


class StructuredExtensionTest(BaseGrabTestCase):
    def setUp(self):
        self.g = build_grab(document_body=XML)

    def test_1(self):
        result = self.g.doc.structure(
            '//issue',
            title='./title/text()',
            date='./date/text()',
            about='./about/text()',
            number=('./number/text()', int),
            home_url='./home-url/text()',
        )
        self.assertEqual(
            result,
            loads('''
                [
                    {
                        "date": "12.09.98",
                        "about": "XML",
                        "home_url": "www.j.ru/issues/",
                        "number": 448,
                        "title": "XML today"
                    }
                ]
            ''')
        )

    def test_2(self):
        result = self.g.doc.structure(
            '//issue',
            x(
                './detail',
                description=('./description/text()',
                             lambda item: ' '.join(item.split())),
                detail_number=('./number/text()', int)
            ),
            title='./title/text()',
            date='./date/text()',
        )
        self.assertEqual(
            result,
            loads('''
                [
                    {
                        "detail_number": 445,
                        "date": "12.09.98",
                        "description": "issue 2 detail description",
                        "title": "XML today"
                    }
                ]
            ''')
        )

    def test_3(self):
        result = self.g.doc.structure(
            '//issue',
            home_url='./home-url/text()',
            articles=x(
                './articles/article',
                id='./@id',
                title='./title/text()',
                url='./url/text()',
                hotkeys=x(
                    './hotkeys',
                    hotkey='./hotkey/text()'
                )
            )
        )
        self.assertEqual(
            result,
            loads('''
                [
                    {
                        "articles": [
                            {
                                "url": "/article1",
                                "id": "3",
                                "hotkeys": [
                                    {
                                        "hotkey": "language"
                                    }
                                ],
                                "title": "Issue overview"
                            },
                            {
                                "url": "/article2",
                                "id": null,
                                "hotkeys": [
                                    {
                                        "hotkey": null
                                    }
                                ],
                                "title": "Latest reviews"
                            },
                            {
                                "url": null,
                                "id": "4",
                                "hotkeys": [
                                    {
                                        "hotkey": null
                                    }
                                ],
                                "title": null
                            }
                        ],
                        "home_url": "www.j.ru/issues/"
                    }
                ]
            ''')
        )
