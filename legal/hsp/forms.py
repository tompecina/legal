# -*- coding: utf-8 -*-
#
# hsp/forms.py
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

from legal.common.glob import CURRENCY_RE
from legal.common import forms, fields, widgets


class MainForm(forms.Form):

    title = fields.CharField(
        widget=widgets.Genw(),
        max_length=255,
        required=False,
        label='Popis')

    note = fields.CharField(
        widget=widgets.Taw(),
        required=False,
        label='Poznámka')

    internal_note = fields.CharField(
        widget=widgets.Taw(),
        required=False,
        label='Interní poznámka')

    rounding = fields.CharField(
        label='Zaokrouhlení')

    next = fields.CharField(
        widget=widgets.Hw(),
        required=False)

    def clean_note(self):
        return self.cleaned_data['note'].replace('\r', '')

    def clean_internal_note(self):
        return self.cleaned_data['internal_note'].replace('\r', '')


DEB_OPTS = (
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


class DebitForm(forms.Form):

    description = fields.CharField(
        widget=widgets.Sdw(),
        max_length=50,
        required=False,
        label='Popis')

    fixed_amount = fields.AmountField(
        widget=widgets.Aw(),
        min_value=.01,
        required=False,
        localize=True)

    fixed_currency = fields.CurrencyField(
        label='v měně',
        initial='CZK')

    fixed_date = fields.DateField(
        widget=widgets.Dw(),
        required=False,
        label='Splatnost')

    principal_debit = fields.IntegerField(
        required=False,
        label='Z')

    principal_amount = fields.AmountField(
        widget=widgets.Aw(),
        min_value=.01,
        required=False,
        label='Částka',
        localize=True)

    principal_currency = fields.CurrencyField(
        label='v měně',
        initial='CZK')

    date_from = fields.DateField(
        widget=widgets.Dw(),
        required=False,
        label='Od')

    date_to = fields.DateField(
        widget=widgets.Dw(),
        required=False,
        label='Do')

    model = fields.ChoiceField(
        widget=widgets.Rs(),
        choices=DEB_OPTS,
        initial='fixed')

    pa_rate = fields.FloatField(
        widget=widgets.Ratew(),
        min_value=0.0,
        required=False,
        localize=True)

    ydconv = fields.CharField(
        label='Konvence',
        required=False)

    pm_rate = fields.FloatField(
        widget=widgets.Ratew(),
        min_value=0.0,
        required=False,
        localize=True)

    mdconv = fields.CharField(
        label='Konvence',
        required=False)

    pd_rate = fields.FloatField(
        widget=widgets.Ratew(),
        min_value=0.0,
        required=False,
        localize=True)

    lock_fixed = fields.BooleanField(
        widget=widgets.Hw(),
        required=False)

    def clean_fixed_amount(self):
        data = self.cleaned_data['fixed_amount']
        if self.data['model'] == 'fixed' and not data:
            raise forms.ValidationError('Amount is required')
        return data

    def clean_fixed_currency(self):
        data = self.cleaned_data['fixed_currency']
        if self.data['model'] == 'fixed' and not data:
            raise forms.ValidationError('Currency is required')
        return data

    def clean_fixed_date(self):
        data = self.cleaned_data['fixed_date']
        if self.data['model'] == 'fixed' and not data:
            raise forms.ValidationError('Date is required')
        return data

    def clean_principal_amount(self):
        data = self.cleaned_data['principal_amount']
        if self.data['model'] != 'fixed' and self.cleaned_data['principal_debit'] == 0 and not data:
            raise forms.ValidationError('Principal amount is required')
        return data

    def clean_principal_currency(self):
        data = self.cleaned_data['principal_currency']
        if self.data['model'] != 'fixed' and self.cleaned_data['principal_debit'] == 0 and not data:
            raise forms.ValidationError('Principal currency is required')
        return data

    def clean_date_from(self):
        data = self.cleaned_data['date_from']
        if self.data['model'] != 'fixed' and self.cleaned_data['principal_debit'] == 0 and not data:
            raise forms.ValidationError('Starting date is required')
        return data

    def clean_pa_rate(self):
        data = self.cleaned_data['pa_rate']
        if self.data['model'] == 'per_annum' and not data:
            raise forms.ValidationError('Interest rate is required')
        return data

    def clean_pm_rate(self):
        data = self.cleaned_data['pm_rate']
        if self.data['model'] == 'per_mensem' and not data:
            raise forms.ValidationError('Interest rate is required')
        return data

    def clean_pd_rate(self):
        data = self.cleaned_data['pd_rate']
        if self.data['model'] == 'per_diem' and not data:
            raise forms.ValidationError('Interest rate is required')
        return data

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from', None)
        date_to = cleaned_data.get('date_to', None)
        if date_from and date_to and date_from > date_to:
            msg = 'Invalid interval'
            self._errors['date_from'] = self.error_class([msg])
            self._errors['date_to'] = self.error_class([msg])
            del cleaned_data['date_from']
            del cleaned_data['date_to']
        return cleaned_data


class CreditForm(forms.Form):

    description = fields.CharField(
        widget=widgets.Sdw(),
        max_length=50,
        required=False,
        label='Popis')

    date = fields.DateField(
        widget=widgets.Dw(),
        label='Datum')

    amount = fields.AmountField(
        widget=widgets.Aw(),
        min_value=.01,
        label='Částka',
        localize=True)

    currency = fields.CurrencyField(
        label='Měna',
        initial='CZK')


class BalanceForm(forms.Form):

    description = fields.CharField(
        widget=widgets.Sdw(),
        max_length=50,
        required=False,
        label='Popis')

    date = fields.DateField(
        widget=widgets.Dw(today=True),
        label='Datum')


class FXform(forms.Form):

    currency_from = fields.CharField(
        widget=widgets.Currw(),
        min_length=3,
        max_length=3)
    del currency_from.widget.attrs['minlength']

    currency_to = fields.CharField(
        widget=widgets.Currw(),
        min_length=3,
        max_length=3)
    del currency_to.widget.attrs['minlength']

    rate_from = fields.FloatField(
        widget=widgets.Fxw(),
        min_value=.001,
        localize=True,
        initial=1)

    rate_to = fields.FloatField(
        widget=widgets.Fxw(),
        min_value=.001,
        localize=True,
        initial=1)

    date_from = fields.DateField(
        widget=widgets.Dw(),
        required=False)

    date_to = fields.DateField(
        widget=widgets.Dw(),
        required=False)

    def clean_currency_from(self):
        data = self.cleaned_data['currency_from'].upper()
        if not CURRENCY_RE.match(data):
            raise forms.ValidationError('Invalid currency format')
        if data == self.data['currency_to'].upper():
            raise forms.ValidationError('Currencies must be different')
        return data

    def clean_currency_to(self):
        data = self.cleaned_data['currency_to'].upper()
        if not CURRENCY_RE.match(data):
            raise forms.ValidationError('Invalid currency format')
        if data == self.data['currency_from'].upper():
            raise forms.ValidationError('Currencies must be different')
        return data

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from', None)
        date_to = cleaned_data.get('date_to', None)
        if date_from and date_to and date_from > date_to:
            msg = 'Invalid interval'
            self._errors['date_from'] = self.error_class([msg])
            self._errors['date_to'] = self.error_class([msg])
            del cleaned_data['date_from']
            del cleaned_data['date_to']
        return cleaned_data
