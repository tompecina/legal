# -*- coding: utf-8 -*-
#
# sop/forms.py
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

from django.core.exceptions import ValidationError

from legal.common.forms import Form
from legal.common.fields import CharField, AmountField, CurrencyField, DateField, ChoiceField
from legal.common.widgets import TextWidget, DateWidget, RadioWidget


OPTS = (
    ('none', 'sine'),
    ('epr', 'elektronický platební rozkaz'),
    ('nmu', 'nemajetková újma'),
    ('vyz', 'výživné'),
    ('vyk', 'výkon rozhodnutí'),
    ('sm', 'smír'),
    ('inc', 'incidence'),
    ('usch', 'úschova'),
)


class MainForm(Form):

    basis = AmountField(
        widget=TextWidget(15),
        min_value=1,
        label='Základ',
        localize=True)
    basis.rounding = 2

    curr = CurrencyField(
        label='Měna',
        czk=True,
        initial='CZK')

    today = date.today()
    fx_date = DateField(
        widget=DateWidget(),
        required=False,
        label='ke dni',
        initial=date(today.year, today.month, 1))

    model = CharField(
        label='Úprava',
        initial='4')

    opt = ChoiceField(
        widget=RadioWidget(),
        choices=OPTS,
        label='Zvláštní případy',
        initial='none')

    def clean_fx_date(self):
        data = self.cleaned_data['fx_date']
        if self.data['curr_0'] != 'CZK' and not data:
            raise ValidationError('Date is required')
        return data
