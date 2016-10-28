# -*- coding: utf-8 -*-
#
# kos/forms.py
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

from datetime import date
from common import forms, fields, widgets
from .models import Preset

def getpreset(id):
    try:
        return Preset.objects.filter(id=id, valid__lte=date.today()) \
            .order_by('-valid')[0].value
    except:
        return 0

class MainForm(forms.Form):
    netincome = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        label='Čistá mzda',
        localize=True)
    netincome.rounding = 0
    netincome2 = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        localize=True,
        initial=0)
    netincome2.rounding = 0
    partner = fields.BooleanField(
        required=False,
        label='Manžel/manželka',
        initial=False)
    partner2 = fields.BooleanField(
        required=True,
        initial=True,
        disabled=True)
    deps = fields.IntegerField(
        widget=widgets.saw(),
        min_value=0,
        label='Počet dalších vyživovaných osob',
        initial=0)
    deps2 = fields.IntegerField(
        widget=widgets.saw(),
        min_value=0,
        initial=0)
    subs = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        label='Zákonné životní minimum',
        localize=True,
        initial=getpreset('SUBS'))
    subs.rounding = 0
    apt = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        label='Normativní náklady na bydlení',
        localize=True,
        initial=getpreset('APT'))
    apt.rounding = 0
    fee = fields.AmountField(
        widget=widgets.saw(),
        min_value=1.0,
        label='Měsíční odměna správce',
        localize=True,
        initial=getpreset(id='FEE'))
    fee.rounding = 0
    fee2 = fields.AmountField(
        widget=widgets.saw(),
        min_value=1.0,
        localize=True,
        initial=getpreset(id='FEE2'))
    fee2.rounding = 0
    exp = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        label='Měsíční hotové výdaje správce',
        localize=True,
        initial=getpreset('EXP'))
    exp.rounding = 0
    exp2 = fields.AmountField(
        widget=widgets.saw(),
        min_value=0,
        label='Měsíční hotové výdaje správce',
        localize=True,
        initial=getpreset('EXP2'))
    exp2.rounding = 0
    vat = fields.BooleanField(
        required=False,
        label='Správce je plátcem DPH',
        initial=True)
    vatrate = fields.DecimalField(
        widget=widgets.saw(),
        max_digits=4,
        decimal_places=2,
        min_value=0,
        label='Sazba DPH z odměny správce',
        initial=getpreset('VAT'),
        localize=True)
