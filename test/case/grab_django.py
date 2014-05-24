from unittest import TestCase

from test.server import SERVER
from test.util import build_grab

class GrabDjangoTestCase(TestCase):
    def setUp(self):
        SERVER.reset()

    def test_response_django_file(self):
        from django.core.files.base import ContentFile

        SERVER.RESPONSE['get'] = 'zzz'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        the_file = g.doc.django_file()
        self.assertTrue(isinstance(the_file, ContentFile))
        self.assertEqual(b'zzz', the_file.read())
        self.assertEqual('', the_file.name)

    def test_response_django_file_with_name(self):
        from django.core.files.base import ContentFile

        SERVER.RESPONSE['get'] = 'zzz'
        g = build_grab()
        g.go(SERVER.BASE_URL)
        the_file = g.doc.django_file(name='movie.flv')
        self.assertEqual(b'zzz', the_file.read())
        self.assertEqual('movie.flv', the_file.name)
