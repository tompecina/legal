# -*- coding: utf-8 -*-
#
# udn/forms.py
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

from django.core.validators import RegexValidator

from legal.common.glob import REGISTER_RE_STR, TEXT_OPTS, FORMAT_OPTS
from legal.common.forms import Form
from legal.common.fields import CharField, DateField, IntegerField, ChoiceField
from legal.common.widgets import TextWidget, DateWidget, RadioWidget


class MainForm(Form):

    date_from = DateField(
        widget=DateWidget(),
        required=False)

    date_to = DateField(
        widget=DateWidget(),
        required=False)

    senate = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        initial='',
        required=False)

    register = CharField(
        widget=TextWidget(8),
        max_length=30,
        validators=(RegexValidator(regex=REGISTER_RE_STR),),
        initial='',
        required=False)

    number = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='',
        required=False)

    year = IntegerField(
        widget=TextWidget(8),
        min_value=1990,
        initial='',
        required=False)

    page = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='',
        required=False)

    agenda = CharField(
        max_length=255,
        required=False,
        label='Oblast',
        initial='')

    party = CharField(
        widget=TextWidget(50),
        required=False,
        max_length=255,
        label='Účastník řízení')

    party_opt = ChoiceField(
        widget=RadioWidget(),
        choices=TEXT_OPTS,
        initial='icontains')

    format = ChoiceField(
        widget=RadioWidget(),
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
