# -*- coding: utf-8 -*-
#
# sir/forms.py
#
# Copyright (C) 2011-17 Tomáš Pecina <tomas@pecina.cz>
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

from common import forms, fields, widgets


class InsForm(forms.Form):

    number = fields.IntegerField(
        widget=widgets.saw(),
        min_value=1,
        initial='')

    year = fields.IntegerField(
        widget=widgets.saw(),
        min_value=2008,
        initial='')

    desc = fields.CharField(
        widget=widgets.genw(),
        max_length=255,
        label='Popis')

    detailed = fields.BooleanField(
        initial=True,
        label='Všechny události',
        required=False)
