# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-14 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dir', '0002_auto_20161111_0333'),
    ]

    operations = [
        migrations.RenameField(
            model_name='debtor',
            old_name='timestamp',
            new_name='timestamp_add',
        ),
        migrations.AddField(
            model_name='debtor',
            name='timestamp_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
