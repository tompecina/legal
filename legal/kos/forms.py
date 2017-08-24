# -*- coding: utf-8 -*-
#
# kos/forms.py
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

from legal.common.utils import getpreset
from legal.common.forms import Form
from legal.common.fields import AmountField, IntegerField, DecimalField, BooleanField
from legal.common.widgets import TextWidget


class MainForm(Form):

    netincome = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Čistá mzda',
        localize=True)
    netincome.rounding = 0

    netincome2 = AmountField(
        widget=TextWidget(8),
        min_value=0,
        localize=True,
        initial=0)
    netincome2.rounding = 0

    partner = BooleanField(
        required=False,
        label='Manžel/manželka',
        initial=False)

    partner2 = BooleanField(
        required=True,
        initial=True,
        disabled=True)

    deps = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        label='Počet dalších vyživovaných osob',
        initial=0)

    deps2 = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        initial=0)

    subs = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Zákonné životní minimum',
        localize=True,
        initial=getpreset('SUBS', as_func=True))
    subs.rounding = 0

    apt = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Normativní náklady na bydlení',
        localize=True,
        initial=getpreset('APT', as_func=True))
    apt.rounding = 0

    fee = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Měsíční odměna správce',
        localize=True,
        initial=getpreset('FEE', as_func=True))
    fee.rounding = 0

    fee2 = AmountField(
        widget=TextWidget(8),
        min_value=0,
        localize=True,
        initial=getpreset('FEE2', as_func=True))
    fee2.rounding = 0

    exp = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Měsíční hotové výdaje správce',
        localize=True,
        initial=getpreset('EXP', as_func=True))
    exp.rounding = 0

    exp2 = AmountField(
        widget=TextWidget(8),
        min_value=0,
        label='Měsíční hotové výdaje správce',
        localize=True,
        initial=getpreset('EXP2', as_func=True))
    exp2.rounding = 0

    vat = BooleanField(
        required=False,
        label='Správce je plátcem DPH',
        initial=True)

    vatrate = DecimalField(
        widget=TextWidget(8),
        max_digits=4,
        decimal_places=2,
        min_value=0,
        label='Sazba DPH z odměny správce',
        initial=getpreset('VAT', as_func=True),
        localize=True)
