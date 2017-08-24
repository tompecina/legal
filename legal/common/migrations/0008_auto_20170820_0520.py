# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-20 05:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_auto_20170812_0822'),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessionid', models.CharField(max_length=32)),
                ('assetid', models.CharField(max_length=150)),
                ('data', models.TextField()),
                ('expire', models.DateTimeField(db_index=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(db_index=True)),
                ('text', models.TextField()),
                ('expire', models.DateTimeField(db_index=True, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='asset',
            unique_together=set([('sessionid', 'assetid')]),
        ),
    ]