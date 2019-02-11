# -*- coding: utf-8 -*-
#
# knr/py
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

from django.core.exceptions import ValidationError

from legal.common.utils import more
from legal.common.forms import Form
from legal.common.fields import CharField, AmountField, IntegerField, FloatField, DecimalField, BooleanField
from legal.common.widgets import TextWidget, HiddenWidget
from legal.knr.glob import FUELS
from legal.knr.utils import getvat


class PlaceForm(Form):

    abbr = CharField(
        widget=TextWidget(12),
        max_length=150,
        label='Zkratka')

    name = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Název')

    addr = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Adresa')

    lat = FloatField(
        widget=TextWidget(12),
        min_value=-90,
        max_value=90,
        label='Zeměpisná šířka',
        localize=True)

    lon = FloatField(
        widget=TextWidget(12),
        min_value=-180,
        max_value=180,
        label='Zeměpisná délka',
        localize=True)


class CarForm(Form):

    abbr = CharField(
        widget=TextWidget(12),
        max_length=150,
        label='Zkratka')

    name = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Název')

    fuel = CharField(
        widget=TextWidget(12),
        max_length=150,
        label='Palivo',
        initial='BA95')

    for idx in range(1, 4):
        locals()['cons{:d}'.format(idx)] = DecimalField(
            widget=TextWidget(4),
            max_digits=3,
            decimal_places=1,
            min_value=0,
            initial='',
            localize=True)


class FormulaForm(Form):

    abbr = CharField(
        widget=TextWidget(12),
        max_length=150,
        label='Zkratka')

    name = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Název')

    flat = DecimalField(
        widget=TextWidget(8),
        max_digits=5,
        decimal_places=2,
        min_value=0,
        label='Paušální náhrada',
        localize=True)

    for fuel in FUELS:
        locals()['rate_' + fuel] = DecimalField(
            widget=TextWidget(8),
            max_digits=5,
            decimal_places=2,
            min_value=0,
            required=False,
            label=fuel,
            localize=True)


class CalcForm(Form):

    title = CharField(
        max_length=255,
        required=False)

    calculation_note = CharField(
        required=False)

    internal_note = CharField(
        required=False)

    vat_rate = DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=0,
        initial=getvat(),
        localize=True)

    def clean_calculation_note(self):
        return self.cleaned_data['calculation_note'].replace('\r', '')

    def clean_internal_note(self):
        return self.cleaned_data['internal_note'].replace('\r', '')


class GeneralForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    amount = AmountField(
        min_value=0,
        localize=True)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)


class ServiceForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    major_number = IntegerField(
        min_value=0)

    rate = AmountField(
        min_value=0,
        localize=True)

    minor_number = IntegerField(
        min_value=0)

    multiple_number = IntegerField(
        min_value=1)

    off10_flag = BooleanField(
        required=False)

    off30_flag = BooleanField(
        required=False)

    off30limit5000_flag = BooleanField(
        required=False)

    off20limit5000_flag = BooleanField(
        required=False)

    basis = CharField(
        required=False)

    def clean_off10_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if more(off10_flag, off30_flag, off30limit5000_flag,
            off20limit5000_flag):
            raise ValidationError("Incompatible flags")
        return off10_flag

    def clean_off30_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if more(off10_flag, off30_flag, off30limit5000_flag,
            off20limit5000_flag):
            raise ValidationError("Incompatible flags")
        return off30_flag

    def clean_off30limit5000_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if more(off10_flag, off30_flag, off30limit5000_flag,
            off20limit5000_flag):
            raise ValidationError("Incompatible flags")
        return off30limit5000_flag

    def clean_off20limit5000_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if more(off10_flag, off30_flag, off30limit5000_flag,
            off20limit5000_flag):
            raise ValidationError("Incompatible flags")
        return off20limit5000_flag

    def clean(self):
        cleaned_data = super().clean()
        major_number = cleaned_data.get('major_number', 0)
        minor_number = cleaned_data.get('minor_number', 0)
        if not (major_number or minor_number):
            msg = 'Invalid data'
            self._errors['major_number'] = self.error_class([msg])
            self._errors['minor_number'] = self.error_class([msg])
            cleaned_data.pop('major_number', None)
            cleaned_data.pop('minor_number', None)
        return cleaned_data


class ServiceSubform(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        required=False)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    major_number = CharField(
        required=False)

    rate = CharField(
        required=False)

    multiple_number = CharField(
        required=False)

    minor_number = CharField(
        required=False)

    off10_flag = BooleanField(
        required=False)

    off30_flag = BooleanField(
        required=False)

    off30limit5000_flag = BooleanField(
        required=False)

    off20limit5000_flag = BooleanField(
        required=False)

    basis = AmountField(
        min_value=0,
        localize=True)


class FlatForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    rate = AmountField(
        min_value=0,
        localize=True)

    collection_flag = BooleanField(
        required=False)

    multiple_flag = BooleanField(
        required=False)

    multiple50_flag = BooleanField(
        required=False)

    single_flag = BooleanField(
        required=False)

    halved_flag = BooleanField(
        required=False)

    halved_appeal_flag = BooleanField(
        required=False)

    basis = CharField(
        required=False)

    def clean_halved_flag(self):
        halved_flag = 'halved_flag' in self.data
        halved_appeal_flag = 'halved_appeal_flag' in self.data
        if halved_flag and halved_appeal_flag:
            raise ValidationError("Incompatible flags")
        return halved_flag

    def clean_halved_appeal_flag(self):
        halved_flag = 'halved_flag' in self.data
        halved_appeal_flag = 'halved_appeal_flag' in self.data
        if halved_flag and halved_appeal_flag:
            raise ValidationError("Incompatible flags")
        return halved_appeal_flag

    def clean_multiple_flag(self):
        multiple_flag = 'multiple_flag' in self.data
        multiple50_flag = 'multiple50_flag' in self.data
        if multiple_flag and multiple50_flag:
            raise ValidationError("Incompatible flags")
        return multiple_flag

    def clean_multiple50_flag(self):
        multiple_flag = 'multiple_flag' in self.data
        multiple50_flag = 'multiple50_flag' in self.data
        if multiple_flag and multiple50_flag:
            raise ValidationError("Incompatible flags")
        return multiple50_flag


class FlatSubform(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        required=False)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    rate = CharField(
        required=False)

    collection_flag = BooleanField(
        required=False)

    multiple_flag = BooleanField(
        required=False)

    multiple50_flag = BooleanField(
        required=False)

    single_flag = BooleanField(
        required=False)

    halved_flag = BooleanField(
        required=False)

    halved_appeal_flag = BooleanField(
        required=False)

    basis = AmountField(
        min_value=0,
        localize=True)


class AdministrativeForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    number = IntegerField(
        min_value=0)

    rate = AmountField(
        min_value=0,
        localize=True)


class AdministrativeSubform(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        required=False)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    number = CharField(
        required=False)

    rate = CharField(
        required=False)


class TimeForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    time_number = IntegerField(
        min_value=0)

    time_rate = AmountField(
        min_value=0,
        localize=True)


class TimeSubform(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        required=False)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)

    time_number = CharField(
        required=False)

    time_rate = CharField(
        required=False)


class TravelForm(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        max_length=255)

    from_name = CharField(
        max_length=255)

    from_address = CharField(
        max_length=255)

    from_lat = FloatField(
        min_value=-90,
        max_value=90,
        required=False,
        localize=True)

    from_lon = FloatField(
        min_value=-180,
        max_value=180,
        required=False,
        localize=True)

    to_name = CharField(
        max_length=255)

    to_address = CharField(
        max_length=255)

    to_lat = FloatField(
        min_value=-90,
        max_value=90,
        required=False,
        localize=True)

    to_lon = FloatField(
        min_value=-180,
        max_value=180,
        required=False,
        localize=True)

    trip_distance = IntegerField(
        min_value=0)

    time_number = IntegerField(
        min_value=0)

    time_rate = AmountField(
        min_value=0,
        localize=True)

    trip_number = IntegerField(
        min_value=0)

    car_name = CharField(
        max_length=255)

    fuel_name = CharField(
        max_length=150)

    cons1 = DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)

    cons2 = DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)

    cons3 = DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)

    formula_name = CharField(
        max_length=255)

    flat_rate = DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        localize=True)

    fuel_price = DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        localize=True)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)


class TravelSubform(Form):

    idx = IntegerField(
        widget=HiddenWidget())

    description = CharField(
        required=False)

    from_name = CharField(
        required=False)

    from_address = CharField(
        required=False)

    from_lat = CharField(
        required=False)

    from_lon = CharField(
        required=False)

    to_name = CharField(
        required=False)

    to_address = CharField(
        required=False)

    to_lat = CharField(
        required=False)

    to_lon = CharField(
        required=False)

    trip_distance = CharField(
        required=False)

    time_number = CharField(
        required=False)

    time_rate = CharField(
        required=False)

    trip_number = CharField(
        required=False)

    car_name = CharField(
        required=False)

    fuel_name = CharField(
        required=False)

    cons1 = CharField(
        required=False)

    cons2 = CharField(
        required=False)

    cons3 = CharField(
        required=False)

    formula_name = CharField(
        required=False)

    flat_rate = CharField(
        required=False)

    fuel_price = CharField(
        required=False)

    vat = BooleanField(
        required=False)

    numerator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    denominator = IntegerField(
        min_value=1,
        widget=TextWidget(4))

    item_note = CharField(
        required=False)
