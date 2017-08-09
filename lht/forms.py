# -*- coding: utf-8 -*-
#
# lht/forms.py
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

from django.core.validators import MinValueValidator, MaxValueValidator

from common import forms, fields, widgets
from lht.glob import MIN_DATE, MAX_DATE, MIN_DUR, MAX_DUR


PRESETS = (
    ('d3', '3 dny'),
    ('w1', '1 týden'),
    ('d8', '8 dnů'),
    ('w2', '2 týdny'),
    ('d15', '15 dnů'),
    ('d30', '30 dnů'),
    ('m1', '1 měsíc'),
    ('d60', '60 dnů'),
    ('m2', '2 měsíce'),
    ('m3', '3 měsíce'),
    ('m6', '6 měsíců'),
    ('y1', '1 rok'),
    ('none', 'jiná'),
)


class MainForm(forms.Form):

    beg_date = fields.DateField(
        widget=widgets.Dw(today=True),
        label='Počátek',
        validators=(
            MinValueValidator(MIN_DATE),
            MaxValueValidator(MAX_DATE)),
        initial=date.today)

    dur = fields.IntegerField(
        widget=widgets.Shw(),
        validators=(
            MinValueValidator(MIN_DUR),
            MaxValueValidator(MAX_DUR)),
        required=False)

    unit = fields.CharField(
        required=False)

    preset = fields.ChoiceField(
        widget=widgets.Rs(),
        choices=PRESETS,
        label='Délka',
        initial='none')

    def clean_dur(self):
        data = self.cleaned_data['dur']
        if 'submit_set_beg_date' not in self.data and self.data['preset'] == 'none' and data is None:
            raise forms.ValidationError('Duration may not be empty')
        return data
