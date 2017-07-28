# -*- coding: utf-8 -*-
#
# pir/forms.py
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
from common import forms, fields, widgets
from common.glob import text_opts, format_opts, ic_regex, rc_full_regex


curryear = date.today().year


class MainForm(forms.Form):

    court = fields.CharField(
        max_length=255,
        required=False,
        label='Insolvenční soud',
        initial='')

    senate = fields.IntegerField(
        widget=widgets.saw(),
        min_value=0,
        initial='',
        required=False)

    number = fields.IntegerField(
        widget=widgets.saw(),
        min_value=1,
        initial='',
        required=False)

    year = fields.IntegerField(
        widget=widgets.saw(),
        min_value=2008,
        initial='',
        required=False)

    date_first_from = fields.DateField(
        widget=widgets.dw(),
        required=False)

    date_first_to = fields.DateField(
        widget=widgets.dw(),
        required=False)

    date_last_from = fields.DateField(
        widget=widgets.dw(),
        required=False)

    date_last_to = fields.DateField(
        widget=widgets.dw(),
        required=False)

    name = fields.CharField(
        widget=widgets.msew(),
        required=False,
        max_length=255,
        label='Příjmení/název')

    name_opt = fields.ChoiceField(
        widget=widgets.rs,
        choices=text_opts,
        initial='istartswith')

    first_name = fields.CharField(
        widget=widgets.msew(),
        required=False,
        max_length=255,
        label='Jméno')

    first_name_opt = fields.ChoiceField(
        widget=widgets.rs,
        choices=text_opts,
        initial='istartswith')

    city = fields.CharField(
        widget=widgets.msew(),
        required=False,
        max_length=255,
        label='Obec')

    city_opt = fields.ChoiceField(
        widget=widgets.rs,
        choices=text_opts,
        initial='istartswith')

    genid = fields.CharField(
        widget=widgets.ssew(),
        required=False,
        max_length=9,
        validators=[RegexValidator(regex=ic_regex)],
        label='IČO')

    taxid = fields.CharField(
        widget=widgets.ssew(),
        required=False,
        max_length=14,
        label='DIČ')

    birthid = fields.CharField(
        widget=widgets.ssew(),
        required=False,
        max_length=11,
        validators=[RegexValidator(regex=rc_full_regex)],
        label='Rodné číslo')

    date_birth = fields.DateField(
        widget=widgets.dw(),
        required=False,
        label='Datum narození')

    year_birth_from = fields.IntegerField(
        widget=widgets.yw(),
        min_value=1900,
        max_value=curryear,
        initial='',
        required=False)

    year_birth_to = fields.IntegerField(
        widget=widgets.yw(),
        min_value=1900,
        max_value=curryear,
        initial='',
        required=False)

    role_debtor = fields.InlineBooleanField(
        initial=True,
        required=False,
        label='dlužník')

    role_trustee = fields.InlineBooleanField(
        required=False,
        label='správce')

    role_creditor = fields.InlineBooleanField(
        required=False,
        label='věřitel')

    deleted = fields.InlineBooleanField(
        required=False,
        label='včetně vyškrtnutých')

    creditors = fields.InlineBooleanField(
        required=False,
        label='včetně seznamu věřitelů')

    format = fields.ChoiceField(
        widget=widgets.rs,
        choices=format_opts,
        label='Výstupní formát',
        initial='html')

    def clean(self):
        cleaned_data = super().clean()
        date_first_from = cleaned_data.get('date_first_from', None)
        date_first_to = cleaned_data.get('date_first_to', None)
        if date_first_from and date_first_to \
           and date_first_from > date_first_to:
            msg = 'Invalid interval'
            self._errors['date_first_from'] = self.error_class([msg])
            self._errors['date_first_to'] = self.error_class([msg])
            del cleaned_data['date_first_from']
            del cleaned_data['date_first_to']
        date_last_from = cleaned_data.get('date_last_from', None)
        date_last_to = cleaned_data.get('date_last_to', None)
        if date_last_from and date_last_to \
           and date_last_from > date_last_to:
            msg = 'Invalid interval'
            self._errors['date_last_from'] = self.error_class([msg])
            self._errors['date_last_to'] = self.error_class([msg])
            del cleaned_data['date_last_from']
            del cleaned_data['date_last_to']
        year_birth_from = cleaned_data.get('year_birth_from', None)
        year_birth_to = cleaned_data.get('year_birth_to', None)
        if year_birth_from and year_birth_to \
           and year_birth_from > year_birth_to:
            msg = 'Invalid interval'
            self._errors['year_birth_from'] = self.error_class([msg])
            self._errors['year_birth_to'] = self.error_class([msg])
            del cleaned_data['year_birth_from']
            del cleaned_data['year_birth_to']
        return cleaned_data
