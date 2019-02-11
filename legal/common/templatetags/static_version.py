# -*- coding: utf-8 -*-
#
# common/templatetags/static_version.py
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

from os.path import join, getmtime

from django.template import Library

from legal.settings import STATIC_ROOT


register = Library()


def ver(filename):

    return "?v={:08x}".format(int(getmtime(join(STATIC_ROOT, filename))))


@register.simple_tag
def ts_common_css():

    return ver('common.css')


@register.simple_tag
def ts_common_js():

    return ver('common.js')


@register.simple_tag(takes_context=True)
def ts_app_css(context):

    return ver(context['app'] + '.css')


@register.simple_tag(takes_context=True)
def ts_app_js(context):

    return ver(context['app'] + '.js')


@register.simple_tag
def ts_acc_css():

    return ver('acc.css')


@register.simple_tag
def ts_acc_js():

    return ver('acc.js')


@register.simple_tag
def ts_favicon():

    return ver('favicon.ico')
