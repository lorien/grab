# -*- coding: utf-8 -*-
from django.conf.urls import *

urlpatterns = patterns('grab.djangoui.grabstat.views',
    url(r'admin/grab_control$', 'grab_control', name='grab_control'),
    url(r'admin/grab_control_api/(\w+)$', 'grab_control_api', name='grab_control_api'),
)
