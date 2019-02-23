# -*- coding: utf-8 -*-
#
# common/models.py
#
# Copyright (C) 2011-19 Tomáš Pecina <tomas@pecina.cz>
#
# This file is part of legal.pecina.cz, a web-based toolbox for lawyers.
#
# This application is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This application is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.db import models
from django.contrib.auth.models import User


class PwResetLink(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE)

    link = models.CharField(
        max_length=32,
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    def __str__(self):
        return self.link


class Preset(models.Model):

    name = models.CharField(
        max_length=150,
        db_index=True,
        unique_for_date='valid')

    value = models.FloatField()

    valid = models.DateField(
        db_index=True)

    def __str__(self):
        return '{}, {}'.format(self.name, str(self.valid))


class Lock(models.Model):

    name = models.CharField(
        max_length=150,
        primary_key=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return '{}, {}'.format(self.name, str(self.timestamp_add))


class Pending(models.Model):

    name = models.CharField(
        max_length=150)

    args = models.CharField(
        max_length=255)

    lock = models.CharField(
        max_length=150)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    def __str__(self):
        return '{}, {}'.format(self.name, str(self.timestamp_add))


class Cache(models.Model):

    url = models.URLField(
        max_length=255,
        unique=True)

    text = models.TextField()

    expire = models.DateTimeField(
        null=True,
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.url


class Asset(models.Model):

    sessionid = models.CharField(
        max_length=32)

    assetid = models.CharField(
        max_length=150)

    data = models.TextField()

    expire = models.DateTimeField(
        null=True,
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    timestamp_update = models.DateTimeField(
        auto_now=True)

    class Meta:
        unique_together = ('sessionid', 'assetid')

    def __str__(self):
        return self.sessionid


class Doc(models.Model):

    app = models.CharField(
        max_length=32)

    filename = models.CharField(
        max_length=255)

    url = models.URLField()

    class Meta:
        unique_together = ('app', 'filename')

    def __str__(self):
        return '{}/{}'.format(self.app, self.filename)
