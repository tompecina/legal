# -*- coding: utf-8 -*-
#
# cnb/forms.py
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

from datetime import date

from legal.common.forms import Form
from legal.common.fields import CurrencyField, DateField, AmountField
from legal.common.widgets import TextWidget, DateWidget


class MainForm(Form):

    curr = CurrencyField(
        czk=False,
        label='Měna',
        initial='EUR')

    fx_date = DateField(
        widget=DateWidget(today=True),
        label='ke dni',
        initial=date.today)

    basis = AmountField(
        widget=TextWidget(15),
        min_value=.01,
        label='Základ',
        localize=True)

    mpi_date = DateField(
        widget=DateWidget(today=True),
        label='Ke dni',
        initial=date.today)
