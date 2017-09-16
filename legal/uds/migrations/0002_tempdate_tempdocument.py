# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-10 09:50
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posted', models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='TempDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docid', models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('publisher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uds.Publisher')),
            ],
        ),
    ]
