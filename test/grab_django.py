from test.util import BaseGrabTestCase
from test.util import build_grab


class GrabDjangoTestCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_response_django_file(self):
        from django.core.files.base import ContentFile

        self.server.response['get.data'] = 'zzz'
        g = build_grab()
        g.go(self.server.get_url())
        the_file = g.doc.django_file()
        self.assertTrue(isinstance(the_file, ContentFile))
        self.assertEqual(b'zzz', the_file.read())
        self.assertEqual('', the_file.name)

    def test_response_django_file_with_name(self):
        self.server.response['get.data'] = 'zzz'
        g = build_grab()
        g.go(self.server.get_url())
        the_file = g.doc.django_file(name='movie.flv')
        self.assertEqual(b'zzz', the_file.read())
        self.assertEqual('movie.flv', the_file.name)
