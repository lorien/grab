# -*- coding: utf-8
from django.contrib import admin

from grab.django.grabstat.models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'start_time', 'end_time', 'is_done', 'is_ok']
    list_filter = ['is_done', 'is_ok']


admin.site.register(Task, TaskAdmin)
