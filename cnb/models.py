# -*- coding: utf-8 -*-
#
# cnb/models.py
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

class FXrate(models.Model):
    date = models.DateField(
        db_index=True)
    text = models.TextField()

    def __str__(self):
        return "%s" % self.date

class MPIrate(models.Model):
    type = models.CharField(
        max_length=20,
        unique_for_date='valid')
    rate = models.FloatField()
    valid = models.DateField(
        db_index=True)

    def __str__(self):
        return self.type

class MPIstat(models.Model):
    type = models.CharField(
        max_length=20,
        primary_key=True)
    timestamp_update = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return self.type
