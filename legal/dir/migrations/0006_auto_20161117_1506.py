# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-17 15:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dir', '0005_auto_20161117_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discovered',
            name='desc',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='discovered',
            unique_together=set([('desc', 'id')]),
        ),
    ]