# -*- coding: utf-8 -*-
#
# dir/models.py
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

from django.core.validators import (
    MinValueValidator, MaxValueValidator)
from django.db import models
from django.contrib.auth.models import User
from datetime import date
from common.glob import text_opts
from sir.models import Vec
from .glob import MAX_LENGTH

curryear = date.today().year

class Debtor(models.Model):
    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    desc = models.CharField(
        max_length=255,
        db_index=True)
    court = models.CharField(
        null=True,
        max_length=20)
    name = models.CharField(
        max_length=MAX_LENGTH,
        null=True)
    name_opt = models.SmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(len(text_opts) - 1)])
    first_name = models.CharField(
        null=True,
        max_length=MAX_LENGTH)
    first_name_opt = models.SmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(len(text_opts) - 1)])
    genid = models.CharField(
        max_length=9,
        null=True)
    taxid = models.CharField(
        max_length=14,
        null=True)
    birthid = models.CharField(
        max_length=10,
        null=True)
    date_birth = models.DateField(
        null=True)
    year_birth_from = models.SmallIntegerField(
        null=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(curryear)])
    year_birth_to = models.SmallIntegerField(
        null=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(curryear)])
    timestamp_add = models.DateTimeField(
        auto_now_add=True,
        db_index=True)
    timestamp_update = models.DateTimeField(
        auto_now=True)
    
    def __str__(self):
        return self.desc
    
class Discovered(models.Model):
    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    desc = models.CharField(
        max_length=255,
        blank=False)
    vec = models.ForeignKey(
        Vec,
        on_delete=models.CASCADE)
    timestamp_add = models.DateTimeField(
        auto_now_add=True)

    class Meta:
        unique_together = ('desc', 'id')
    
    def __str__(self):
        return self.desc
