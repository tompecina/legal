# -*- coding: utf-8 -*-
#
# cin/forms.py
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

from legal.common.forms import Form
from legal.common.fields import DateField
from legal.common.widgets import DateWidget


class MainForm(Form):

    beg_date = DateField(
        widget=DateWidget(today=True),
        label='Počátek',
        help_text='(nezapočítává se)',
    )

    end_date = DateField(
        widget=DateWidget(today=True),
        label='Konec',
        help_text='(započítává se)',
    )
