# -*- coding: utf-8 -*-
#
# psj/models.py
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

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from common.utils import composeref
from common.glob import register_regex
from szr.models import Court

class Courtroom(models.Model):
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE)
    desc = models.CharField(
        max_length=255,
        db_index=True)
    timestamp = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return '%s, %s' % (self.court, self.desc)

class Party(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True)
    timestamp = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.name

class Judge(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True)
    timestamp = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.name

class Form(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True)
    timestamp = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.name

class Hearing(models.Model):
    courtroom = models.ForeignKey(
        Courtroom,
        on_delete=models.CASCADE)
    time = models.DateTimeField()
    senate = models.IntegerField(
        validators=[MinValueValidator(0)])
    register = models.CharField(
        max_length=30,
        validators=[RegexValidator(regex=register_regex)])
    number = models.PositiveIntegerField()
    year = models.IntegerField(
        validators=[MinValueValidator(1990)])
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE)
    judge = models.ForeignKey(
        Judge,
        on_delete=models.CASCADE)
    parties = models.ManyToManyField(
        Party)
    closed = models.BooleanField(
        default=False)
    cancelled = models.BooleanField(
        default=False)
    timestamp = models.DateTimeField(
        auto_now_add=True)

    class Meta:
        unique_together = ('time', 'id')
    
    def __str__(self):
        return '%s, %s' % (self.courtroom.court.id,
            composeref(self.senate, self.register, self.number, self.year))

class Task(models.Model):
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE)
    date = models.DateField()
    timestamp = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return '%s, %s' % (self.court, self.date)
