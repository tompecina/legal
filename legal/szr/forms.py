# -*- coding: utf-8 -*-
#
# szr/forms.py
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
from django.core.exceptions import ValidationError

from legal.common.glob import REGISTER_RE_STR
from legal.common.forms import Form
from legal.common.fields import CharField, EmailField, IntegerField
from legal.common.widgets import TextWidget, CourtWidget
from legal.szr.glob import SUPREME_COURT
from legal.szr.models import Court


class EmailForm(Form):

    email = EmailField(
        widget=TextWidget(35),
        max_length=60,
        label='E-mail')


def courtval(court):

    if not Court.objects.filter(id=court).exists():
        raise ValidationError('Court does not exist')


class ProcForm(Form):

    court = CharField(
        widget=CourtWidget(supreme_court=True, supreme_administrative_court=True),
        max_length=30,
        label='Soud',
        initial=SUPREME_COURT,
        validators=(courtval,))

    senate = IntegerField(
        widget=TextWidget(8),
        min_value=0,
        initial='',
        required=False)

    register = CharField(
        widget=TextWidget(8),
        max_length=30,
        initial='',
        validators=(RegexValidator(regex=REGISTER_RE_STR),))

    number = IntegerField(
        widget=TextWidget(8),
        min_value=1,
        initial='')

    year = IntegerField(
        widget=TextWidget(8),
        min_value=1990,
        initial='')

    desc = CharField(
        widget=TextWidget(60),
        max_length=255,
        label='Popis',
        required=False)
