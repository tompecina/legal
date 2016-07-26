# -*- coding: utf-8 -*-
#
# knr/models.py
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

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User

class Place(models.Model):
    uid = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE)
    abbr = models.CharField(
        max_length=30)
    name = models.CharField(
        max_length=255)
    addr = models.CharField(
        max_length=255)
    lat = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    lon = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])

    def __str__(self):
        return self.abbr

    class Meta:
        unique_together = (('uid', 'abbr'),)
    
class Car(models.Model):
    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    abbr = models.CharField(
        max_length=30)
    name = models.CharField(
        max_length=255)
    fuel = models.CharField(
        max_length=30)
    cons1 = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0)])
    cons2 = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0)])
    cons3 = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0)])

    def __str__(self):
        return self.abbr

    class Meta:
        unique_together = (('uid', 'abbr'),)
    
class Formula(models.Model):
    uid = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE)
    abbr = models.CharField(
        max_length=30)
    name = models.CharField(
        max_length=255)
    flat = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)])

    def __str__(self):
        return self.abbr

    class Meta:
        unique_together = (('uid', 'abbr'),)
    
class Rate(models.Model):
    formula = models.ForeignKey(
        Formula,
        on_delete=models.CASCADE)
    fuel = models.CharField(
        max_length=30)
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)])

    def __str__(self):
        return '%s/%s' % (self.formula.abbr, self.fuel)

    class Meta:
        unique_together = (('formula', 'fuel'),)
    
class VATrate(models.Model):
    rate = models.FloatField()
    valid = models.DateField(
        db_index=True)

    def __str__(self):
        return "%s" % self.valid
