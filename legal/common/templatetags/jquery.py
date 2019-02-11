# -*- coding: utf-8 -*-
#
# common/templatetags/jquery.py
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

from django.template import Library

from legal.settings import JQUERY_VERSION, JQUERY_UI_VERSION


register = Library()


@register.simple_tag
def jquery_ui_css():

    return 'jquery-ui-{}.css'.format(JQUERY_UI_VERSION)


@register.simple_tag
def jquery_js():

    return 'jquery-{}.min.js'.format(JQUERY_VERSION)



@register.simple_tag
def jquery_ui_js():

    return 'jquery-ui-{}.min.js'.format(JQUERY_UI_VERSION)


@register.simple_tag
def datepicker_js():

    return 'datepicker-cs.js'
