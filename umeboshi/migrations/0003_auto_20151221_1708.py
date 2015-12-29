# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('umeboshi', '0002_event_task_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='datetime_processed',
            field=models.DateTimeField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='datetime_scheduled',
            field=models.DateTimeField(db_index=True),
        ),
    ]
