# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-14 13:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sir', '0019_auto_20161111_0333'),
    ]

    operations = [
        migrations.AddField(
            model_name='adresa',
            name='timestamp_add',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vec',
            name='timestamp_update',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='adresa',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]