# -*- coding: utf-8 -*-
#
# uds/models.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from sphinxsearch.models import SphinxModel, SphinxField, SphinxIntegerField, SphinxDateTimeField
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.contrib.auth.models import User

from legal.sur.models import Party


class Publisher(models.Model):

    name = models.CharField(
        max_length=255,
        unique=True)

    type = models.CharField(
        max_length=150,
        db_index=True)

    pubid = models.IntegerField(
        validators=(MinValueValidator(1),))

    high = models.BooleanField(
        default=False,
        db_index=True)

    subsidiary_region = models.BooleanField(
        default=False,
        db_index=True)

    subsidiary_county = models.BooleanField(
        default=False,
        db_index=True)

    reports = models.ForeignKey(
        'self',
        null=True,
        on_delete=models.SET_NULL)

    updated = models.DateTimeField(
        null=True,
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    timestamp_update = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return self.name


class Agenda(models.Model):

    desc = models.CharField(
        max_length=255,
        unique=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.desc


class Document(models.Model):

    docid = models.IntegerField(
        validators=(MinValueValidator(1),),
        unique=True)

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE)

    desc = models.CharField(
        max_length=255)

    ref = models.CharField(
        max_length=255)

    senate = models.IntegerField(
        null=True,
        validators=(MinValueValidator(0),),
        db_index=True)

    register = models.CharField(
        null=True,
        max_length=30,
        db_index=True)

    number = models.PositiveIntegerField(
        null=True,
        db_index=True)

    year = models.IntegerField(
        null=True,
        validators=(MinValueValidator(1950),),
        db_index=True)

    page = models.PositiveIntegerField(
        null=True,
        db_index=True)

    agenda = models.ForeignKey(
        Agenda,
        on_delete=models.CASCADE)

    posted = models.DateField(
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    def __str__(self):
        return '{}, {}'.format(self.publisher.name, self.ref)


class DocumentIndex(SphinxModel):

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE)

    senate = SphinxIntegerField(
        validators=(MinValueValidator(0),),
        default=0)

    register = models.CharField(
        max_length=30,
        default='')

    number = SphinxIntegerField(
        default=0)

    year = SphinxIntegerField(
        validators=(MinValueValidator(1970),),
        default=0)

    page = SphinxIntegerField(
        default=0)

    agenda = models.ForeignKey(
        Agenda,
        on_delete=models.CASCADE)

    posted = SphinxDateTimeField()

    text = SphinxField()

    class Meta:
        managed = False


class File(models.Model):

    fileid = models.IntegerField(
        validators=(MinValueValidator(1),),
        unique=True)

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE)

    name = models.CharField(
        max_length=255)

    text = models.TextField()

    ocr = models.BooleanField(
        default=False,
        db_index=True)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    def __str__(self):
        return '{}, {}, {}'.format(self.document.publisher.name, self.document.desc, self.name)


class Retrieved(models.Model):

    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)

    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE)

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.party.party
