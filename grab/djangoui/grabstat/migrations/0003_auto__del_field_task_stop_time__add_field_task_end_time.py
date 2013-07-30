# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Task.stop_time'
        db.delete_column(u'grabstat_task', 'stop_time')

        # Adding field 'Task.end_time'
        db.add_column(u'grabstat_task', 'end_time',
                      self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Task.stop_time'
        db.add_column(u'grabstat_task', 'stop_time',
                      self.gf('django.db.models.fields.DateTimeField')(blank=True, null=True, db_index=True),
                      keep_default=False)

        # Deleting field 'Task.end_time'
        db.delete_column(u'grabstat_task', 'end_time')


    models = {
        u'grabstat.task': {
            'Meta': {'object_name': 'Task'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'error_traceback': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'record_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'spider_stats': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'spider_timing': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '10', 'db_index': 'True', 'blank': 'True'}),
            'task_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'work_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['grabstat']