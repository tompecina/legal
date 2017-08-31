# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-27 22:47
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0008_auto_20170827_2205'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fileid', models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('name', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('timestamp_add', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uds.Document')),
            ],
        ),
    ]