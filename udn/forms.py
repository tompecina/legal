# -*- coding: utf-8 -*-
#
# udn/forms.py
#
# Copyright (C) 2011-16 Tomáš Pecina <tomas@pecina.cz>
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
from datetime import date
from common import forms, fields, widgets
from szr.glob import register_regex

party_opts = (('icontains',  'kdekoliv'),
              ('istartswith',  'na začátku'),
              ('iexact', 'přesně'))

class MainForm(forms.Form):
    error_css_class = 'err'
    use_required_attribute = False
    senate = fields.IntegerField(widget=widgets.saw(),
                                 min_value=0, initial='',
                                 required=False)
    register = fields.CharField(
        widget=widgets.saw(),
        max_length=30,
        validators=[RegexValidator(regex=register_regex)],
        initial='',
        required=False)
    number = fields.IntegerField(
        widget=widgets.saw(),
        min_value=1,
        initial='',
        required=False)
    year = fields.IntegerField(
        widget=widgets.saw(),
        min_value=1990,
        initial='',
        required=False)
    page = fields.IntegerField(
        widget=widgets.saw(),
        min_value=1,
        initial='',
        required=False)
    date_from = fields.DateField(
        widget=widgets.dw(),
        required=False)
    date_to = fields.DateField(
        widget=widgets.dw(),
        required=False)
    agenda = fields.CharField(
        widget=widgets.abbrw(),
        max_length=30,
        required=False,
        label='Oblast',
        initial='0')
    party = fields.CharField(
        widget=widgets.sew(),
        required=False,
        max_length=255,
        label='Účastník řízení')
    party_opt = fields.ChoiceField(
        widget=widgets.rs,
        choices=party_opts,
        initial='icontains')

    def clean_date_from(self):
        cleaned_data = super(MainForm, self).clean()
        date_from = cleaned_data.get('date_from', None)
        date_to = cleaned_data.get('date_to', None)
        if date_from and date_to and (date_from > date_to):
            raise forms.ValidationError('Invalid time interval')
        return date_from

    def clean_date_to(self):
        cleaned_data = super(MainForm, self).clean()
        date_from = cleaned_data.get('date_from', None)
        date_to = cleaned_data.get('date_to', None)
        if date_from and date_to and (date_from > date_to):
            raise forms.ValidationError('Invalid time interval')
        return date_to
