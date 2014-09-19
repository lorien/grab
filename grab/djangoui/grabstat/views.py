# -*- coding: utf-8 -*-
import logging
from grab.spider import Spider
from grab.util.module import build_spider_registry, load_spider_class
from grab.util.config import build_root_config

from django.shortcuts import redirect, get_object_or_404, render
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django import forms

from common.pagination import paginate
from common.decorators import ajax_get


class ControlForm(forms.Form):
    spider = forms.ChoiceField(required=False)
    command = forms.ChoiceField(required=False)


def grab_control(request):
    form = ControlForm(request.GET or None)
    spider_registry = build_spider_registry(build_root_config())
    spider_choices = [(x, x) for x in spider_registry.keys()]
    form.fields['spider'].choices = spider_choices
    form.fields['spider'].widget.choices = spider_choices

    command_choices = [(x, x) for x in Spider.get_available_command_names()]
    form.fields['command'].choices = command_choices
    form.fields['command'].widget.choices = command_choices

    context = {
        'form': form,
    }
    return render(request, 'grabstat/control_form.html', context)


@ajax_get
def grab_control_api(request, command):
    args = request.GET 
    cls = load_spider_class(build_root_config(), args['spider'])
    spider = cls()
    iface = spider.controller.add_interface('redis')
    if command == 'put_command':
        result_id = iface.put_command({'name': args['command']})
        return {'result_id': result_id}
    elif command == 'pop_result':
        result = iface.pop_result(args['result_id'])
        if result is None:
            return {'status': 'not-ready'}
        else:
            return {'data': result.get('data', ''),
                    'error': result.get('error', ''),
                    }
    else:
        return {'error': 'unknown-command'}
