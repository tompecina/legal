# -*- coding: utf-8 -*-
#
# udn/models.py
#
# Copyright (C) 2011-16 Tomáš Pecina <tomas@pecina.cz>
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
from django.core.validators import MinValueValidator, RegexValidator
from common.utils import composeref
from common.glob import register_regex
from .glob import filename_regex

class Agenda(models.Model):
    desc = models.CharField(
        max_length=255,
        unique=True)
    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.desc

class Party(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True)
    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)

    def __str__(self):
        return self.name

class Decision(models.Model):
    senate = models.IntegerField(
        validators=[MinValueValidator(0)])
    register = models.CharField(
        max_length=30,
        validators=[RegexValidator(regex=register_regex)])
    number = models.PositiveIntegerField()
    year = models.IntegerField(
        validators=[MinValueValidator(1990)])
    page = models.PositiveIntegerField()
    agenda = models.ForeignKey(
        Agenda,
        on_delete=models.CASCADE)
    parties = models.ManyToManyField(
        Party)
    date = models.DateField()
    filename = models.CharField(
        max_length=255,
        validators=[RegexValidator(regex=filename_regex)])
    anonfilename = models.CharField(
        max_length=255,
        blank=True,
        validators=[RegexValidator(regex=filename_regex)])
    updated = models.DateTimeField(
        null=True,
        db_index=True)
    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)
    timestamp_update = models.DateTimeField(
        auto_now=True)

    class Meta:
        unique_together = ('date', 'id')

    def __str__(self):
        return composeref(
            self.senate,
            self.register,
            self.number,
            self.year,
            self.page)
