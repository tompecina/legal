# -*- coding: utf-8 -*-
#
# uds/validators.py
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

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from legal.uds.models import DocumentIndex


@deconstructible
class SphinxQueryValidator:
    message = 'Syntax error in query.'
    code = 'invalid'

    def __call__(self, val):
        try:
            DocumentIndex.objects.using('sphinx').filter(text__search=val).exists()
        except:
            raise ValidationError(self.message, code=self.code)
