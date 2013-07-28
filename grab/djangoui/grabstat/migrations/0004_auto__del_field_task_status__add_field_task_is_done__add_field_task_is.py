# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Task.status'
        db.delete_column(u'grabstat_task', 'status')

        # Adding field 'Task.is_done'
        db.add_column(u'grabstat_task', 'is_done',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Task.is_failed'
        db.add_column(u'grabstat_task', 'is_failed',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Task.status'
        db.add_column(u'grabstat_task', 'status',
                      self.gf('django.db.models.fields.CharField')(default='new', max_length=10, blank=True, db_index=True),
                      keep_default=False)

        # Deleting field 'Task.is_done'
        db.delete_column(u'grabstat_task', 'is_done')

        # Deleting field 'Task.is_failed'
        db.delete_column(u'grabstat_task', 'is_failed')


    models = {
        u'grabstat.task': {
            'Meta': {'object_name': 'Task'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'error_traceback': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'record_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'spider_stats': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'spider_timing': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'task_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'work_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['grabstat']