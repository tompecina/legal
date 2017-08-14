# -*- coding: utf-8 -*-
#
# udn/forms.py
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

from django.core.validators import RegexValidator

from legal.common.glob import REGISTER_RE_STR, TEXT_OPTS, FORMAT_OPTS
from legal.common import forms, fields, widgets


class MainForm(forms.Form):

    date_from = fields.DateField(
        widget=widgets.Dw(),
        required=False)

    date_to = fields.DateField(
        widget=widgets.Dw(),
        required=False)

    senate = fields.IntegerField(
        widget=widgets.Saw(),
        min_value=0,
        initial='',
        required=False)

    register = fields.CharField(
        widget=widgets.Saw(),
        max_length=30,
        validators=(RegexValidator(regex=REGISTER_RE_STR),),
        initial='',
        required=False)

    number = fields.IntegerField(
        widget=widgets.Saw(),
        min_value=1,
        initial='',
        required=False)

    year = fields.IntegerField(
        widget=widgets.Saw(),
        min_value=1990,
        initial='',
        required=False)

    page = fields.IntegerField(
        widget=widgets.Saw(),
        min_value=1,
        initial='',
        required=False)

    agenda = fields.CharField(
        max_length=255,
        required=False,
        label='Oblast',
        initial='')

    party = fields.CharField(
        widget=widgets.Sew(),
        required=False,
        max_length=255,
        label='Účastník řízení')

    party_opt = fields.ChoiceField(
        widget=widgets.Rs(),
        choices=TEXT_OPTS,
        initial='icontains')

    format = fields.ChoiceField(
        widget=widgets.Rs(),
        choices=FORMAT_OPTS,
        label='Výstupní formát',
        initial='html')

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
