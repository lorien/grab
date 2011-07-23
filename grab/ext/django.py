# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from urlparse import urlsplit

class Extension(object):
    export_attributes = ['django_file']
        
    def django_file(self, name=None):
        """
        Build from response content the django ContentFile instance.
        """
       
        from django.core.files.base import ContentFile

        if not name:
            path = urlsplit(self.response.url).path
            name = path.rstrip('/').split('/')[-1]

        content_file = ContentFile(self.response.body)
        content_file.name = name
        return content_file
