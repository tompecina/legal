# -*- coding: utf-8 -*-
#
# hjp/forms.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from legal.common.forms import Form
from legal.common.fields import CharField, ChoiceField, DateField, DecimalField, CurrencyField
from legal.common.widgets import TextWidget, DateWidget, RadioWidget, TextAreaWidget, HiddenWidget


TR_OPTS = (
    ('debit', 'závazek'),
    ('credit', 'splátka'),
    ('balance', 'zůstatek'),
)

REP_OPTS = (
    ('interest', 'napřed úrok'),
    ('principal', 'napřed jistina'),
)


class TransForm(Form):

    description = CharField(
        widget=TextWidget(60),
        max_length=255,
        required=False,
        label='Popis')

    transaction_type = ChoiceField(
        widget=RadioWidget(),
        choices=TR_OPTS,
        label='Typ',
        initial='balance')

    date = DateField(
        widget=DateWidget(today=True),
        label='Datum')

    amount = DecimalField(
        widget=TextWidget(15),
        max_digits=15,
        decimal_places=2,
        min_value=.0,
        required=False,
        label='Částka',
        localize=True)

    repayment_preference = ChoiceField(
        widget=RadioWidget(),
        choices=REP_OPTS,
        required=False,
        label='Přednost',
        initial='interest')

    def clean_amount(self):
        data = self.cleaned_data['amount']
        if self.data['transaction_type'] != 'balance' and not data:
            raise ValidationError('Amount is required')
        return data


INT_OPTS = (
    ('none', 'Bez úroku'),
    ('fixed', 'Pevná částka'),
    ('per_annum', 'Roční úrok'),
    ('per_mensem', 'Měsíční úrok'),
    ('per_diem', 'Denní úrok'),
    ('cust1', 'Úrok z prodlení podle nařízení č. 142/1994 Sb. (účinnost do 27.04.2005)'),
    ('cust2', 'Úrok z prodlení podle nařízení č. 142/1994 Sb. (účinnost od 28.04.2005 do 30.06.2010)'),
    ('cust3', 'Úrok z prodlení podle nařízení č. 142/1994 Sb. (účinnost od 01.07.2010 do 30.06.2013)'),
    ('cust5', 'Úrok z prodlení podle nařízení č. 142/1994 Sb. (účinnost od 01.07.2013 do 31.12.2013)'),
    ('cust6', 'Úrok z prodlení podle nařízení č. 351/2013 Sb.'),
    ('cust4', 'Poplatek z prodlení podle nařízení č. 142/1994 Sb.'),
)


class MainForm(Form):

    title = CharField(
        widget=TextWidget(60),
        max_length=255,
        required=False,
        label='Popis')

    note = CharField(
        widget=TextAreaWidget(),
        required=False,
        label='Poznámka')

    internal_note = CharField(
        widget=TextAreaWidget(),
        required=False,
        label='Interní poznámka')

    currency = CurrencyField(
        label='Měna',
        initial='CZK')

    rounding = CharField(
        label='Zaokrouhlení')

    model = ChoiceField(
        widget=RadioWidget(),
        choices=INT_OPTS,
        label='Úročení')

    fixed_amount = DecimalField(
        widget=TextWidget(15),
        max_digits=15,
        decimal_places=2,
        min_value=0.0,
        required=False,
        localize=True)

    pa_rate = DecimalField(
        widget=TextWidget(15),
        max_digits=12,
        decimal_places=6,
        required=False,
        localize=True)

    ydconv = CharField(
        label='Konvence',
        required=False)

    pm_rate = DecimalField(
        widget=TextWidget(15),
        max_digits=12,
        decimal_places=6,
        required=False,
        localize=True)

    mdconv = CharField(
        label='Konvence',
        required=False)

    pd_rate = DecimalField(
        widget=TextWidget(15),
        max_digits=12,
        decimal_places=6,
        required=False,
        localize=True)

    next = CharField(
        widget=HiddenWidget(),
        required=False)

    def clean_note(self):
        return self.cleaned_data['note'].replace('\r', '')

    def clean_internal_note(self):
        return self.cleaned_data['internal_note'].replace('\r', '')

    def clean_fixed_amount(self):
        data = self.cleaned_data['fixed_amount']
        if self.data['model'] == 'fixed' and not data:
            raise ValidationError('Amount is required')
        return data

    def clean_pa_rate(self):
        data = self.cleaned_data['pa_rate']
        if self.data['model'] == 'per_annum' and not data:
            raise ValidationError('Interest rate is required')
        return data

    def clean_pm_rate(self):
        data = self.cleaned_data['pm_rate']
        if self.data['model'] == 'per_mensem' and not data:
            raise ValidationError('Interest rate is required')
        return data

    def clean_pd_rate(self):
        data = self.cleaned_data['pd_rate']
        if self.data['model'] == 'per_diem' and not data:
            raise ValidationError('Interest rate is required')
        return data
