# -*- coding: utf-8 -*-
#
# szr/models.py
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

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.contrib.auth.models import User

from legal.common.glob import REGISTER_RE_STR
from legal.common.utils import composeref


class Court(models.Model):

    id = models.CharField(
        max_length=30,
        primary_key=True)

    name = models.CharField(
        max_length=255,
        unique=True)

    reports = models.ForeignKey(
        'self',
        null=True,
        on_delete=models.SET_NULL)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.name


class Proceedings(models.Model):

    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE)

    senate = models.IntegerField(
        validators=(MinValueValidator(0),))

    register = models.CharField(
        max_length=30,
        validators=(RegexValidator(regex=REGISTER_RE_STR),))

    number = models.PositiveIntegerField()

    year = models.IntegerField(
        validators=(MinValueValidator(1990),))

    auxid = models.IntegerField(
        default=0)

    desc = models.CharField(
        max_length=255,
        blank=True,
        db_index=True)

    hash = models.CharField(
        max_length=32,
        blank=True,
        validators=(RegexValidator(regex=r'[0-9a-f]{32}'),))

    changed = models.DateTimeField(
        null=True)

    updated = models.DateTimeField(
        null=True,
        db_index=True)

    notify = models.BooleanField(
        default=False)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    timestamp_update = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return '{}, {}'.format(self.court, composeref(self.senate, self.register, self.number, self.year))
