# -*- coding: utf-8 -*-
#
# common/fields.py
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

from decimal import Decimal
from datetime import datetime, date

from django import forms
from django.core.validators import EMPTY_VALUES

from common.utils import LocalFloat
from common.forms import ValidationError
from common import widgets


def proc_num(string):

    return string.replace(' ', '').replace('.', '').replace(',', '.').replace('−', '-')


STYPES = (str,)


class BooleanField(forms.BooleanField):

    pass


class InlineBooleanField(forms.BooleanField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


class CharField(forms.CharField):

    pass


class ChoiceField(forms.ChoiceField):

    pass


class EmailField(forms.EmailField):

    pass


class DateField(forms.DateField):

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return super().to_python(value.replace(' ', ''))


class AmountField(forms.FloatField):

    rounding = 0

    def prepare_value(self, value):
        if value in EMPTY_VALUES:
            return None
        if not isinstance(value, STYPES):
            value = '{:.{prec}f}'.format(
                LocalFloat(value),
                prec=self.rounding)
        return value

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, STYPES):
            value = proc_num(value)
        try:
            return round(float(value), self.rounding)
        except:
            raise ValidationError('Conversion error')


class DecimalField(forms.DecimalField):

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, STYPES):
            value = proc_num(value)
        try:
            return Decimal(value)
        except:
            raise ValidationError('Conversion error')


class FloatField(forms.FloatField):

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, STYPES):
            value = proc_num(value)
        try:
            return float(value)
        except:
            raise ValidationError('Conversion error')


class IntegerField(forms.IntegerField):

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, STYPES):
            value = proc_num(value)
        try:
            return int(float(value))
        except:
            raise ValidationError('Conversion error')


class CurrencyField(forms.MultiValueField):

    def __init__(self, czk=True, *args, **kwargs):
        kwargs['required'] = False
        super().__init__(
            widget=widgets.CurrencyWidget(czk=czk),
            fields=(
                forms.CharField(),
                forms.CharField(min_length=3, max_length=3)),
            *args,
            **kwargs)

    def compress(self, data_list):
        if data_list:
            return data_list[1].upper() if data_list[0] == 'OTH' else data_list[0]
        return None

    def validate(self, value):
        if not value:
            self.widget.widgets[1].attrs['class'] += ' err'
            raise ValidationError('Currency is required')
