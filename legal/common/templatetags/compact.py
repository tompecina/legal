# -*- coding: utf-8 -*-
#
# common/templatetags/compact.py
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

from re import compile, sub

from django.utils.functional import keep_lazy_text
from django.utils.encoding import force_text
from django.template import Library
from django.template.defaulttags import SpacelessNode


register = Library()


COMP_RE1 = compile(r'>\s+([^<]*)<')
COMP_RE2 = compile(r'>(\S*)\s+<')
COMP_RE3 = compile(r'>\s+<')
COMP_RE4 = compile(r'\s+(\S+)="\s*(\S+)\s*"')
COMP_RE5 = compile(r'\s+class=""')
COMP_RE6 = compile(r'\s+(\S+)=""')
COMP_RE7 = compile(r' +')


@keep_lazy_text
def compactify_html(value):
    res = force_text(value)
    res = sub(COMP_RE1, r'> \1<', res)
    res = sub(COMP_RE2, r'>\1 <', res)
    res = sub(COMP_RE3, r'><', res)
    res = sub(COMP_RE4, r' \1="\2"', res)
    res = sub(COMP_RE5, r' ', res)
    res = sub(COMP_RE6, r' \1', res)
    res = sub(COMP_RE7, r' ', res)
    return res


class CompactNode(SpacelessNode):

    def render(self, context):
        return compactify_html(self.nodelist.render(context).strip())


@register.tag
def compact(parser, token):

    nodelist = parser.parse(('endcompact',))
    parser.delete_first_token()
    return CompactNode(nodelist)
