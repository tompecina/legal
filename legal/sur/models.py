# -*- coding: utf-8 -*-
#
# sur/models.py
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

from django.core.validators import (
    MinValueValidator, MaxValueValidator, MinLengthValidator, RegexValidator)
from django.db import models
from django.contrib.auth.models import User

from legal.common.glob import REGISTER_RE_STR, TEXT_OPTS
from legal.common.utils import composeref
from legal.szr.models import Court
from legal.sur.glob import MIN_LENGTH, MAX_LENGTH


class Party(models.Model):

    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)

    party = models.CharField(
        max_length=MAX_LENGTH,
        validators=(MinLengthValidator(MIN_LENGTH),),
        db_index=True)

    party_opt = models.SmallIntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(len(TEXT_OPTS) - 1)))

    check_psj = models.BooleanField(
        default=True)

    check_uds = models.BooleanField(
        default=True)

    check_udn = models.BooleanField(
        default=True)

    notify = models.BooleanField(
        default=False)

    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    timestamp_update = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return self.party


class Found(models.Model):

    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)

    name = models.CharField(
        max_length=255,
        db_index=True)

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

    url = models.URLField(
        max_length=1024)

    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return '{}, {}'.format(self.court, composeref(self.senate, self.register, self.number, self.year))
