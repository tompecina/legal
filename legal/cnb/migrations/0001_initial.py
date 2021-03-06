# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-26 10:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FXrate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MPIrate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20)),
                ('rate', models.FloatField()),
                ('valid', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='MPIstat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20)),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
