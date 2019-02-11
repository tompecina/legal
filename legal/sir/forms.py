# -*- coding: utf-8 -*-
#
# sir/forms.py
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

from legal.common.forms import Form
from legal.common.fields import CharField, IntegerField, BooleanField
from legal.common.widgets import TextWidget


class InsForm(Form):

    number = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='')

    year = IntegerField(
        widget=TextWidget(8),
        min_value=2008,
        initial='')

    desc = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Popis')

    detailed = BooleanField(
        initial=True,
        label='Všechny události',
        required=False)
