# -*- coding: utf-8 -*-
from django.db import models
from django.core.urlresolvers import reverse


class Task(models.Model):
    task_name = models.CharField(max_length=40, blank=True)
    record_date = models.DateTimeField(auto_now_add=True, db_index=True)
    start_time = models.DateTimeField(null=True, db_index=True, blank=True)
    end_time = models.DateTimeField(null=True, db_index=True, blank=True)
    is_done = models.BooleanField(default=False, blank=True)
    is_ok = models.BooleanField(default=True, blank=True)
    error_traceback = models.TextField(blank=True)    
    spider_stats = models.TextField(blank=True)
    spider_timing = models.TextField(blank=True)
    elapsed_time = models.IntegerField(blank=True, default=0)
    pid = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.task_name
