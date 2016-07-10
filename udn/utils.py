# -*- coding: utf-8 -*-
#
# udn/utils.py
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

def composeref(*args):
    if args[0]:
        s = '%d ' % args[0]
    else:
        s = ''
    s += '%s %d/%d' % args[1:4]
    if len(args) == 5:
        s += '-%d' % args[4]
    return s

def decomposeref(ref):
    s = ref.split('-')
    if len(s) == 1:
        page = 0
    else:
        page = int(s[1])
    s = s[0].split()
    if s[0].isdigit():
        senate = int(s[0])
        del s[0]
    else:
        senate = 0
    register = s[0]
    t = s[1].split('/')
    if page:
        return senate, register, int(t[0]), int(t[1]), page
    else:
        return senate, register, int(t[0]), int(t[1])
