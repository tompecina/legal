# -*- coding: utf-8 -*-
#
# cnb/forms.py
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

from datetime import date
from common import forms, fields, widgets


class MainForm(forms.Form):

    curr = fields.CurrencyField(
        czk=False,
        label='Měna',
        initial='EUR')

    fx_date = fields.DateField(
        widget=widgets.Dw(today=True),
        label='ke dni',
        initial=date.today)

    basis = fields.AmountField(
        widget=widgets.Aw(),
        min_value=0.01,
        label='Základ',
        localize=True)

    mpi_date = fields.DateField(
        widget=widgets.Dw(today=True),
        label='Ke dni',
        initial=date.today)
