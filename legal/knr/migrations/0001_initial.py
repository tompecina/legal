# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-26 10:39
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Car',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=255)),
                ('fuel', models.CharField(max_length=30)),
                ('cons1', models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0)])),
                ('cons2', models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0)])),
                ('cons3', models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0)])),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Formula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=255)),
                ('flat', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0)])),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbr', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=255)),
                ('addr', models.CharField(max_length=255)),
                ('lat', models.FloatField(validators=[django.core.validators.MinValueValidator(-90.0), django.core.validators.MaxValueValidator(90.0)])),
                ('lon', models.FloatField(validators=[django.core.validators.MinValueValidator(-180.0), django.core.validators.MaxValueValidator(180.0)])),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fuel', models.CharField(max_length=30)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0)])),
                ('formula', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knr.Formula')),
            ],
        ),
    ]
