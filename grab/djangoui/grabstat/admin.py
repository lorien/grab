# -*- coding: utf-8
import os

from django.contrib import admin

from models import Task


class TaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'start_time', 'end_time', 'elapsed_time_formatted',
                    'is_done', 'is_ok', 'is_process_live', 'pid']
    list_filter = ['is_done', 'is_ok']

    def elapsed_time_formatted(self, obj):
        seconds = obj.elapsed_time
        if seconds < 60:
            return '%d sec.' % seconds
        else:
            minutes, seconds = divmod(seconds, 60)
            if minutes < 60:
                return '%d min.' % minutes
            else:
                hours, minutes = divmod(minutes, 60)
                return '%d hr. %d min.' % (hours, minutes)
    elapsed_time_formatted.short_description = 'Elapsed time'

    def is_process_live(self, obj):
        if obj.pid:
            return 'yes' if os.path.exists('/proc/%d' % obj.pid) else 'no'
        else:
            return 'no'
    is_process_live.short_description = 'Proc. live'


admin.site.register(Task, TaskAdmin)
