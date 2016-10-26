# -*- coding: utf-8 -*-
#
# sur/forms.py
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

from django.core.validators import MinLengthValidator
from common import forms, fields, widgets
from common.utils import grammar
from common.glob import text_opts, GR_C
from .glob import MIN_LENGTH, MAX_LENGTH

class PartyForm(forms.Form):
    party = fields.CharField(
        widget=widgets.sew(attrs={
            'data-minLen': MIN_LENGTH,
            'data-minLenText': grammar(MIN_LENGTH, GR_C)}),
        max_length=MAX_LENGTH,
        label='Vyhledávací řetězec',
        validators=[MinLengthValidator(MIN_LENGTH)])
    party_opt = fields.ChoiceField(
        widget=widgets.rs,
        choices=text_opts,
        label='Posice',
        initial='istartswith')

class PartyBatchForm(forms.Form):
    next = fields.CharField(
        widget=widgets.hw(),
        required=False)
