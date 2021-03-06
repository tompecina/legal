# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-17 15:06
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sir', '0027_auto_20161117_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='insolvency',
            name='desc',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='vec',
            name='firstAction',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='vec',
            name='rocnik',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(2008)]),
        ),
    ]
