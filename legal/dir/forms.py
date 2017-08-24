# -*- coding: utf-8 -*-
#
# dir/forms.py
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

from django.core.validators import RegexValidator

from legal.common.glob import TEXT_OPTS, IC_RE_STR, RC_FULL_RE_STR
from legal.common import forms, fields, widgets
from legal.dir.glob import MAX_LENGTH


class DebtorForm(forms.Form):

    curr_year = date.today().year

    desc = fields.CharField(
        widget=widgets.XXLWidget(),
        max_length=255,
        label='Popis')

    court = fields.CharField(
        widget=widgets.CourtWidget(ins_courts=True),
        max_length=255,
        required=False,
        label='Insolvenční soud',
        initial='')

    name = fields.CharField(
        widget=widgets.XXLWidget(),
        max_length=MAX_LENGTH,
        required=False,
        label='Příjmení/název')

    name_opt = fields.ChoiceField(
        widget=widgets.RadioWidget(),
        choices=TEXT_OPTS,
        label='Posice',
        initial='icontains')

    first_name = fields.CharField(
        widget=widgets.XXLWidget(),
        max_length=MAX_LENGTH,
        required=False,
        label='Jméno')

    first_name_opt = fields.ChoiceField(
        widget=widgets.RadioWidget(),
        choices=TEXT_OPTS,
        label='Posice',
        initial='icontains')

    genid = fields.CharField(
        widget=widgets.LWidget(),
        required=False,
        max_length=9,
        validators=(RegexValidator(regex=IC_RE_STR),),
        label='IČO')

    taxid = fields.CharField(
        widget=widgets.LWidget(),
        required=False,
        max_length=14,
        label='DIČ')

    birthid = fields.CharField(
        widget=widgets.LWidget(),
        required=False,
        max_length=11,
        validators=(RegexValidator(regex=RC_FULL_RE_STR),),
        label='Rodné číslo')

    date_birth = fields.DateField(
        widget=widgets.DateWidget(),
        required=False,
        label='Datum narození')

    year_birth_from = fields.IntegerField(
        widget=widgets.XXXSWidget(),
        min_value=1900,
        max_value=curr_year,
        initial='',
        required=False)

    year_birth_to = fields.IntegerField(
        widget=widgets.XXXSWidget(),
        min_value=1900,
        max_value=curr_year,
        initial='',
        required=False)

    def clean(self):
        cleaned_data = super().clean()
        year_birth_from = cleaned_data.get('year_birth_from', None)
        year_birth_to = cleaned_data.get('year_birth_to', None)
        if year_birth_from and year_birth_to and year_birth_from > year_birth_to:
            msg = 'Invalid interval'
            self._errors['year_birth_from'] = self.error_class([msg])
            self._errors['year_birth_to'] = self.error_class([msg])
            del cleaned_data['year_birth_from']
            del cleaned_data['year_birth_to']
        return cleaned_data
