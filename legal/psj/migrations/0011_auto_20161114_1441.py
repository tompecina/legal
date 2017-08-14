# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-14 14:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('psj', '0010_auto_20161114_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hearing',
            name='timestamp_add',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='party',
            name='timestamp_add',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='timestamp_add',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='timestamp_update',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]