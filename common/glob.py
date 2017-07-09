# -*- coding: utf-8 -*-
#
# common/glob.py
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

from datetime import timedelta

MIN_PWLEN = 6

wn = ('Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne')

LIM = 0.005

inerr = 'Chybné zadání, prosím, opravte údaje'
inerr_short = 'Chybné zadání'

registers = [
    'T', 'C', 'P a Nc', 'D', 'E', 'P', 'Nc', 'ERo', 'Ro', 'EC',
    'EVC', 'EXE', 'EPR', 'PP', 'Cm', 'Sm', 'Ca', 'Cad', 'Az', 'To',
    'Nt', 'Co', 'Ntd', 'Cmo', 'Ko', 'Nco', 'Ncd', 'Ncp', 'ECm',
    'ICm', 'INS', 'K', 'Kv', 'EVCm', 'A', 'Ad', 'Af', 'Na', 'UL',
    'Cdo', 'Odo', 'Tdo', 'Tz', 'Ncu', 'Ads', 'Afs', 'Ans', 'Ao',
    'Aos', 'Aprk', 'Aprn', 'Aps', 'Ars', 'As', 'Asz', 'Azs', 'Komp',
    'Konf', 'Kse', 'Kseo', 'Kss', 'Ksz', 'Na', 'Nad', 'Nao', 'Ncn',
    'Nk', 'Ntn', 'Obn', 'Plen', 'Plsn', 'Pst', 'Rozk', 'Rs', 'S',
    'Spr', 'Sst', 'Vol', 'Tm', 'Tmo', 'Ntm'
]
register_regex = '^({})$'.format('|'.join(registers))

hd = (
    {'f': None, 't': None, 'd':  1, 'm':  1},
    {'f': None, 't': None, 'd':  1, 'm':  5},
    {'f': 1992, 't': None, 'd':  8, 'm':  5},
    {'f': None, 't': 1991, 'd':  9, 'm':  5},
    {'f': None, 't': None, 'd':  5, 'm':  7},
    {'f': None, 't': None, 'd':  6, 'm':  7},
    {'f': 2000, 't': None, 'd': 28, 'm':  9},
    {'f': None, 't': None, 'd': 28, 'm': 10},
    {'f': 2000, 't': None, 'd': 17, 'm': 11},
    {'f': None, 't': None, 'd': 24, 'm': 12},
    {'f': None, 't': None, 'd': 25, 'm': 12},
    {'f': None, 't': None, 'd': 26, 'm': 12},
)

ydconvs = (
    'ACT/ACT',
    'ACT/365',
    'ACT/360',
    'ACT/364',
    '30U/360',
    '30E/360',
    '30E/360 ISDA',
    '30E+/360'
)

mdconvs = (
    'ACT',
    '30U',
    '30E',
    '30E ISDA',
    '30E+'
)

odp = timedelta(days=1)
odm = timedelta(days=-1)

TEXTOPTS = [
    {
        'sql': 'icontains',
        'abbr': '*', 'desc':
        'kdekoliv'},
    {
        'sql': 'istartswith',
        'abbr': '<',
        'desc': 'na začátku'},
    {
        'sql': 'iendswith',
        'abbr': '>',
        'desc': 'na konci'},
    {
        'sql': 'iexact',
        'abbr': '=',
        'desc': 'přesně'},
]
text_opts = [[x['sql'], x['desc']] for x in TEXTOPTS]
text_opts_keys = [x['sql'] for x in TEXTOPTS]
text_opts_abbr = [x['abbr'] for x in TEXTOPTS]
text_opts_ai = {x: text_opts_abbr.index(x) for x in text_opts_abbr}
text_opts_ca = [(':' + x) for x in text_opts_abbr]

localdomain = 'pecina.cz'
localsubdomain = 'legal.' + localdomain
localemail = 'legal@' + localdomain
localscheme = 'https'
localprefix = localscheme + '://'
localurl = localprefix + localsubdomain
repourl = localurl + '/repo/'

exlim_title = 'Příliš velký počet záznamů'

GR_C = ('znak', 'znaky', 'znaků')
GR_D = ('den', 'dny', 'dnů')
GR_B = ('pracovní den', 'pracovní dny', 'pracovních dnů')
GR_M = ('měsíc', 'měsíce', 'měsíců')
GR_Y = ('rok', 'roky', 'let')

format_opts = (
    ('html', 'HTML'),
    ('xml', 'XML'),
    ('csv', 'CSV'),
    ('json', 'JSON'),
)

ic_regex = r'^\d{1,9}$'
rc_regex = r'^\d{9,10}$'
rc_full_regex = r'^\d{6}/\d{3,4}$'
psc_regex = r'^\d{5}$'

DTF = '%Y-%m-%d'
