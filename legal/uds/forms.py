# -*- coding: utf-8 -*-
#
# uds/forms.py
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

from legal.common.glob import TEXT_OPTS, FORMAT_OPTS
from legal.common.forms import Form
from legal.common.fields import CharField, DateField, IntegerField, ChoiceField
from legal.common.widgets import TextWidget, DateWidget, RadioWidget, PublisherWidget
from legal.uds.validators import SphinxQueryValidator


class MainForm(Form):

    date_posted_from = DateField(
        widget=DateWidget(),
        required=False)

    date_posted_to = DateField(
        widget=DateWidget(),
        required=False)

    publisher = CharField(
        widget=PublisherWidget(),
        max_length=255,
        required=False,
        label='Soud/státní zastupitelství')

    senate = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        initial='',
        required=False)

    register = CharField(
        widget=TextWidget(8),
        max_length=30,
        initial='',
        required=False)

    number = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='',
        required=False)

    year = IntegerField(
        widget=TextWidget(8),
        min_value=1950,
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
        label='Agenda',
        initial='')

    text = CharField(
        widget=TextWidget(60),
        required=False,
        max_length=255,
        label='V textu',
        validators=(SphinxQueryValidator(),))

    format = ChoiceField(
        widget=RadioWidget(),
        choices=FORMAT_OPTS,
        label='Výstupní formát',
        initial='html')

    def clean(self):
        cleaned_data = super().clean()
        date_posted_from = cleaned_data.get('date_posted_from', None)
        date_posted_to = cleaned_data.get('date_posted_to', None)
        if date_posted_from and date_posted_to and date_posted_from > date_posted_to:
            msg = 'Invalid interval'
            self._errors['date_posted_from'] = self.error_class([msg])
            self._errors['date_posted_to'] = self.error_class([msg])
            del cleaned_data['date_posted_from']
            del cleaned_data['date_posted_to']
        return cleaned_data
