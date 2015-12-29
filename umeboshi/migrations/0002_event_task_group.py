# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('umeboshi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='task_group',
            field=models.CharField(max_length=256, null=True, db_index=True),
        ),
    ]
