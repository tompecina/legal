# -*- coding: utf-8 -*-
#
# pir/forms.py
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

from django.core.validators import RegexValidator

from legal.common.glob import TEXT_OPTS, FORMAT_OPTS, IC_RE_STR, RC_FULL_RE_STR
from legal.common.forms import Form
from legal.common.fields import CharField, DateField, IntegerField, ChoiceField, InlineBooleanField
from legal.common.widgets import TextWidget, DateWidget, RadioWidget, CourtWidget


CURRYEAR = date.today().year


class MainForm(Form):

    court = CharField(
        widget=CourtWidget(ins_courts=True),
        max_length=255,
        required=False,
        label='Insolvenční soud',
        initial='')

    senate = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        initial='',
        required=False)

    number = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='',
        required=False)

    year = IntegerField(
        widget=TextWidget(8),
        min_value=2008,
        initial='',
        required=False)

    date_first_from = DateField(
        widget=DateWidget(),
        required=False)

    date_first_to = DateField(
        widget=DateWidget(),
        required=False)

    date_last_from = DateField(
        widget=DateWidget(),
        required=False)

    date_last_to = DateField(
        widget=DateWidget(),
        required=False)

    name = CharField(
        widget=TextWidget(35),
        required=False,
        max_length=255,
        label='Příjmení/název')

    name_opt = ChoiceField(
        widget=RadioWidget(),
        choices=TEXT_OPTS,
        initial='istartswith')

    first_name = CharField(
        widget=TextWidget(35),
        required=False,
        max_length=255,
        label='Jméno')

    first_name_opt = ChoiceField(
        widget=RadioWidget(),
        choices=TEXT_OPTS,
        initial='istartswith')

    city = CharField(
        widget=TextWidget(35),
        required=False,
        max_length=255,
        label='Obec')

    city_opt = ChoiceField(
        widget=RadioWidget(),
        choices=TEXT_OPTS,
        initial='istartswith')

    genid = CharField(
        widget=TextWidget(20),
        required=False,
        max_length=9,
        validators=(RegexValidator(regex=IC_RE_STR),),
        label='IČO')

    taxid = CharField(
        widget=TextWidget(20),
        required=False,
        max_length=14,
        label='DIČ')

    birthid = CharField(
        widget=TextWidget(20),
        required=False,
        max_length=11,
        validators=(RegexValidator(regex=RC_FULL_RE_STR),),
        label='Rodné číslo')

    date_birth = DateField(
        widget=DateWidget(),
        required=False,
        label='Datum narození')

    year_birth_from = IntegerField(
        widget=TextWidget(4),
        min_value=1900,
        max_value=CURRYEAR,
        initial='',
        required=False)

    year_birth_to = IntegerField(
        widget=TextWidget(4),
        min_value=1900,
        max_value=CURRYEAR,
        initial='',
        required=False)

    role_debtor = InlineBooleanField(
        initial=True,
        required=False,
        label='dlužník')

    role_trustee = InlineBooleanField(
        required=False,
        label='správce')

    role_creditor = InlineBooleanField(
        required=False,
        label='věřitel')

    deleted = InlineBooleanField(
        required=False,
        label='včetně vyškrtnutých')

    creditors = InlineBooleanField(
        required=False,
        label='včetně seznamu věřitelů')

    format = ChoiceField(
        widget=RadioWidget(),
        choices=FORMAT_OPTS,
        label='Výstupní formát',
        initial='html')

    def clean(self):
        cleaned_data = super().clean()
        date_first_from = cleaned_data.get('date_first_from', None)
        date_first_to = cleaned_data.get('date_first_to', None)
        if date_first_from and date_first_to and date_first_from > date_first_to:
            msg = 'Invalid interval'
            self._errors['date_first_from'] = self.error_class([msg])
            self._errors['date_first_to'] = self.error_class([msg])
            del cleaned_data['date_first_from']
            del cleaned_data['date_first_to']
        date_last_from = cleaned_data.get('date_last_from', None)
        date_last_to = cleaned_data.get('date_last_to', None)
        if date_last_from and date_last_to and date_last_from > date_last_to:
            msg = 'Invalid interval'
            self._errors['date_last_from'] = self.error_class([msg])
            self._errors['date_last_to'] = self.error_class([msg])
            del cleaned_data['date_last_from']
            del cleaned_data['date_last_to']
        year_birth_from = cleaned_data.get('year_birth_from', None)
        year_birth_to = cleaned_data.get('year_birth_to', None)
        if year_birth_from and year_birth_to and year_birth_from > year_birth_to:
            msg = 'Invalid interval'
            self._errors['year_birth_from'] = self.error_class([msg])
            self._errors['year_birth_to'] = self.error_class([msg])
            del cleaned_data['year_birth_from']
            del cleaned_data['year_birth_to']
        return cleaned_data
