# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.ShortUUIDField(unique=True, editable=False, blank=True)),
                ('trigger_name', models.CharField(max_length=50, db_index=True)),
                ('data_pickled', models.TextField(editable=False, blank=True)),
                ('data_hash', models.CharField(max_length=32, db_index=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('datetime_scheduled', models.DateTimeField()),
                ('datetime_processed', models.DateTimeField(null=True)),
                ('status', models.IntegerField(default=-3, db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='event',
            index_together=set([('datetime_processed', 'datetime_scheduled'), ('data_hash', 'datetime_processed', 'trigger_name')]),
        ),
    ]
