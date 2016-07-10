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

from django.db import models
from szr.models import Court

class Courtroom(models.Model):
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE)
    name = models.CharField(
        max_length=255)
    desc = models.CharField(
        max_length=255)
    timestamp = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return '%s, %s' % (self.court, self.name)
