# -*- coding: utf-8 -*-
#
# knr/forms.py
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

from common import forms, fields, widgets
from .glob import fuels
from .utils import getVAT

class PlaceForm(forms.Form):
    abbr = fields.CharField(
        widget=widgets.abbrw(),
        max_length=30,
        label='Zkratka')
    name = fields.CharField(
        widget=widgets.genw(),
        max_length=255,
        label='Název')
    addr = fields.CharField(
        widget=widgets.genw(),
        max_length=255,
        label='Adresa')
    lat = fields.FloatField(
        widget=widgets.gpsw(),
        min_value=-90.0,
        max_value=90.0,
        label='Zeměpisná šířka',
        localize=True)
    lon = fields.FloatField(
        widget=widgets.gpsw(),
        min_value=-180.0,
        max_value=180.0,
        label='Zeměpisná délka',
        localize=True)

class CarForm(forms.Form):
    abbr = fields.CharField(
        widget=widgets.abbrw(),
        max_length=30,
        label='Zkratka')
    name = fields.CharField(
        widget=widgets.genw(),
        max_length=255,
        label='Název')
    fuel = fields.CharField(
        widget=widgets.abbrw(),
        max_length=30,
        label='Palivo',
        initial='BA95')
    for i in range(3):
        exec(("cons{:d} = fields.DecimalField(widget=widgets.consw(), " \
              "max_digits=3, decimal_places=1, min_value=0, initial='', " \
              "localize=True)").format(i + 1))

class FormulaForm(forms.Form):
    abbr = fields.CharField(
        widget=widgets.abbrw(),
        max_length=30,
        label='Zkratka')
    name = fields.CharField(
        widget=widgets.genw(),
        max_length=255,
        label='Název')
    flat = fields.DecimalField(
        widget=widgets.saw(),
        max_digits=5,
        decimal_places=2,
        min_value=0,
        label='Paušální náhrada',
        localize=True)
    for f in fuels:
        exec(("rate_{0} = fields.DecimalField(widget=widgets.saw(), " \
              "max_digits=5, decimal_places=2, min_value=0, " \
              "required=False, label='{0}', localize=True)").format(f))

class CalcForm(forms.Form):
    title = fields.CharField(
        max_length=255,
        required=False)
    calculation_note = fields.CharField(
        required=False)
    internal_note = fields.CharField(
        required=False)
    vat_rate = fields.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=0,
        initial=getVAT(),
        localize=True)

    def clean_calculation_note(self):
        return self.cleaned_data['calculation_note'].replace('\r', '')

    def clean_internal_note(self):
        return self.cleaned_data['internal_note'].replace('\r', '')

class GeneralForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    amount = fields.AmountField(
        min_value=0,
        localize=True)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)

class ServiceForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    major_number = fields.IntegerField(
        min_value=0)
    rate = fields.AmountField(
        min_value=0,
        localize=True)
    minor_number = fields.IntegerField(
        min_value=0)
    multiple_number = fields.IntegerField(
        min_value=1)
    off10_flag = fields.BooleanField(
        required=False)
    off30_flag = fields.BooleanField(
        required=False)
    off30limit5000_flag = fields.BooleanField(
        required=False)
    off20limit5000_flag = fields.BooleanField(
        required=False)
    basis = fields.CharField(
        required=False)

    def clean_off10_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if (off10_flag + off30_flag + off30limit5000_flag + \
            off20limit5000_flag) > 1:
            raise forms.ValidationError("Incompatible flags")
        return off10_flag

    def clean_off30_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if (off10_flag + off30_flag + off30limit5000_flag + \
            off20limit5000_flag) > 1:
            raise forms.ValidationError("Incompatible flags")
        return off30_flag

    def clean_off30limit5000_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if (off10_flag + off30_flag + off30limit5000_flag + \
            off20limit5000_flag) > 1:
            raise forms.ValidationError("Incompatible flags")
        return off30limit5000_flag

    def clean_off20limit5000_flag(self):
        off10_flag = 'off10_flag' in self.data
        off30_flag = 'off30_flag' in self.data
        off30limit5000_flag = 'off30limit5000_flag' in self.data
        off20limit5000_flag = 'off20limit5000_flag' in self.data
        if (off10_flag + off30_flag + off30limit5000_flag + \
            off20limit5000_flag) > 1:
            raise forms.ValidationError("Incompatible flags")
        return off20limit5000_flag

class ServiceSubform(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        required=False)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    major_number = fields.CharField(
        required=False)
    rate = fields.CharField(
        required=False)
    multiple_number = fields.CharField(
        required=False)
    minor_number = fields.CharField(
        required=False)
    off10_flag = fields.BooleanField(
        required=False)
    off30_flag = fields.BooleanField(
        required=False)
    off30limit5000_flag = fields.BooleanField(
        required=False)
    off20limit5000_flag = fields.BooleanField(
        required=False)
    basis = fields.AmountField(
        min_value=0,
        localize=True)

class FlatForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    rate = fields.AmountField(
        min_value=0,
        localize=True)
    collection_flag = fields.BooleanField(
        required=False)
    multiple_flag = fields.BooleanField(
        required=False)
    multiple50_flag = fields.BooleanField(
        required=False)
    single_flag = fields.BooleanField(
        required=False)
    halved_flag = fields.BooleanField(
        required=False)
    halved_appeal_flag = fields.BooleanField(
        required=False)
    basis = fields.CharField(
        required=False)

    def clean_halved_flag(self):
        halved_flag = 'halved_flag' in self.data
        halved_appeal_flag = 'halved_appeal_flag' in self.data
        if halved_flag and halved_appeal_flag:
            raise forms.ValidationError("Incompatible flags")
        return halved_flag

    def clean_halved_appeal_flag(self):
        halved_flag = 'halved_flag' in self.data
        halved_appeal_flag = 'halved_appeal_flag' in self.data
        if halved_flag and halved_appeal_flag:
            raise forms.ValidationError("Incompatible flags")
        return halved_appeal_flag

    def clean_multiple_flag(self):
        multiple_flag = 'multiple_flag' in self.data
        multiple50_flag = 'multiple50_flag' in self.data
        if multiple_flag and multiple50_flag:
            raise forms.ValidationError("Incompatible flags")
        return multiple_flag

    def clean_multiple50_flag(self):
        multiple_flag = 'multiple_flag' in self.data
        multiple50_flag = 'multiple50_flag' in self.data
        if multiple_flag and multiple50_flag:
            raise forms.ValidationError("Incompatible flags")
        return multiple50_flag

class FlatSubform(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        required=False)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    rate = fields.CharField(
        required=False)
    collection_flag = fields.BooleanField(
        required=False)
    multiple_flag = fields.BooleanField(
        required=False)
    multiple50_flag = fields.BooleanField(
        required=False)
    single_flag = fields.BooleanField(
        required=False)
    halved_flag = fields.BooleanField(
        required=False)
    halved_appeal_flag = fields.BooleanField(
        required=False)
    basis = fields.AmountField(
        min_value=0,
        localize=True)

class AdministrativeForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    number = fields.IntegerField(
        min_value=0)
    rate = fields.AmountField(
        min_value=0,
        localize=True)

class AdministrativeSubform(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        required=False)
    vat = fields.BooleanField(
        required=False)
    item_note = fields.CharField(
        required=False)
    number = fields.CharField(
        required=False)
    rate = fields.CharField(
        required=False)

class TimeForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
    time_number = fields.IntegerField(
        min_value=0)
    time_rate = fields.AmountField(
        min_value=0,
        localize=True)

class TimeSubform(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        required=False)
    vat = fields.BooleanField(
        required=False)
    item_note = fields.CharField(
        required=False)
    time_number = fields.CharField(
        required=False)
    time_rate = fields.CharField(
        required=False)

class TravelForm(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        max_length=255)
    from_name = fields.CharField(
        max_length=255)
    from_address = fields.CharField(
        max_length=255)
    from_lat = fields.FloatField(
        min_value=-90.0,
        max_value=90.0,
        required=False,
        localize=True)
    from_lon = fields.FloatField(
        min_value=-180.0,
        max_value=180.0,
        required=False,
        localize=True)
    to_name = fields.CharField(
        max_length=255)
    to_address = fields.CharField(
        max_length=255)
    to_lat = fields.FloatField(
        min_value=-90.0,
        max_value=90.0,
        required=False,
        localize=True)
    to_lon = fields.FloatField(
        min_value=-180.0,
        max_value=180.0,
        required=False,
        localize=True)
    trip_distance = fields.IntegerField(
        min_value=0)
    time_number = fields.IntegerField(
        min_value=0)
    time_rate = fields.AmountField(
        min_value=0,
        localize=True)
    trip_number = fields.IntegerField(
        min_value=0)
    car_name = fields.CharField(
        max_length=255)
    fuel_name = fields.CharField(
        max_length=30)
    cons1 = fields.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)
    cons2 = fields.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)
    cons3 = fields.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        localize=True)
    formula_name = fields.CharField(
        max_length=255)
    flat_rate = fields.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        localize=True)
    fuel_price = fields.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        localize=True)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)

class TravelSubform(forms.Form):
    idx = fields.IntegerField(
        widget=widgets.hw())
    description = fields.CharField(
        required=False)
    from_name = fields.CharField(
        required=False)
    from_address = fields.CharField(
        required=False)
    from_lat = fields.CharField(
        required=False)
    from_lon = fields.CharField(
        required=False)
    to_name = fields.CharField(
        required=False)
    to_address = fields.CharField(
        required=False)
    to_lat = fields.CharField(
        required=False)
    to_lon = fields.CharField(
        required=False)
    trip_distance = fields.CharField(
        required=False)
    time_number = fields.CharField(
        required=False)
    time_rate = fields.CharField(
        required=False)
    trip_number = fields.CharField(
        required=False)
    car_name = fields.CharField(
        required=False)
    fuel_name = fields.CharField(
        required=False)
    cons1 = fields.CharField(
        required=False)
    cons2 = fields.CharField(
        required=False)
    cons3 = fields.CharField(
        required=False)
    formula_name = fields.CharField(
        required=False)
    flat_rate = fields.CharField(
        required=False)
    fuel_price = fields.CharField(
        required=False)
    vat = fields.BooleanField(
        required=False)
    numerator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    denominator = fields.IntegerField(
        min_value=1,
        widget=widgets.shw())
    item_note = fields.CharField(
        required=False)
