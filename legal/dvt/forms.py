# -*- coding: utf-8 -*-
#
# dvt/forms.py
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

from legal.common import forms, fields, widgets


class MainForm(forms.Form):

    beg_date = fields.DateField(
        widget=widgets.DateWidget(),
        label='Nástup trestu')

    years = fields.IntegerField(
        widget=widgets.XXXSWidget(),
        required=False,
        min_value=0,
        label='let')

    months = fields.IntegerField(
        widget=widgets.XXXSWidget(),
        required=False,
        min_value=0,
        label='měsíců')

    days = fields.IntegerField(
        widget=widgets.XXXSWidget(),
        required=False,
        min_value=0,
        label='dnů')

    def clean_years(self):
        data = self.cleaned_data['years']
        if not (data or self.data['months'] or self.data['days']):
            raise forms.ValidationError('Missing duration')
        return data

    def clean_months(self):
        data = self.cleaned_data['months']
        if not (data or self.data['years'] or self.data['days']):
            raise forms.ValidationError('Missing duration')
        return data

    def clean_days(self):
        data = self.cleaned_data['days']
        if not (data or self.data['years'] or self.data['months']):
            raise forms.ValidationError('Missing duration')
        return data
