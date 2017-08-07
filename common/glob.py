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

from datetime import date, timedelta


MIN_PWLEN = 6

WD_NAMES = ('Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne')

LIM = .005

INERR = 'Chybné zadání, prosím, opravte údaje'
INERR_SHORT = 'Chybné zadání'

REGISTERS = (
    'T', 'C', 'P a Nc', 'D', 'E', 'P', 'Nc', 'ERo', 'Ro', 'EC',
    'EVC', 'EXE', 'EPR', 'PP', 'Cm', 'Sm', 'Ca', 'Cad', 'Az', 'To',
    'Nt', 'Co', 'Ntd', 'Cmo', 'Ko', 'Nco', 'Ncd', 'Ncp', 'ECm',
    'ICm', 'INS', 'K', 'Kv', 'EVCm', 'A', 'Ad', 'Af', 'Na', 'UL',
    'Cdo', 'Odo', 'Tdo', 'Tz', 'Ncu', 'Ads', 'Afs', 'Ans', 'Ao',
    'Aos', 'Aprk', 'Aprn', 'Aps', 'Ars', 'As', 'Asz', 'Azs', 'Komp',
    'Konf', 'Kse', 'Kseo', 'Kss', 'Ksz', 'Na', 'Nad', 'Nao', 'Ncn',
    'Nk', 'Ntn', 'Obn', 'Plen', 'Plsn', 'Pst', 'Rozk', 'Rs', 'S',
    'Spr', 'Sst', 'Vol', 'Tm', 'Tmo', 'Ntm'
)
REGISTER_REGEX = '^({})$'.format('|'.join(REGISTERS))

CURRENCY_REGEX = r'^[A-Z]{3}$'

UNC_DATE = date(1925, 4, 15)

YDCONVS = (
    'ACT/ACT',
    'ACT/365',
    'ACT/360',
    'ACT/364',
    '30U/360',
    '30E/360',
    '30E/360 ISDA',
    '30E+/360'
)

MDCONVS = (
    'ACT',
    '30U',
    '30E',
    '30E ISDA',
    '30E+'
)

ODP = timedelta(days=1)
ODM = timedelta(days=-1)

ASSET_EXP = timedelta(weeks=1)

TEXT_OPTS_RAW = (
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
)
TEXT_OPTS = [(x['sql'], x['desc']) for x in TEXT_OPTS_RAW]
TEXT_OPTS_KEYS = [x['sql'] for x in TEXT_OPTS_RAW]
TEXT_OPTS_ABBR = [x['abbr'] for x in TEXT_OPTS_RAW]
TEXT_OPTS_AI = {x: TEXT_OPTS_ABBR.index(x) for x in TEXT_OPTS_ABBR}
TEXT_OPTS_CA = [':' + x for x in TEXT_OPTS_ABBR]

LOCAL_DOMAIN = 'pecina.cz'
LOCAL_SUBDOMAIN = 'legal.' + LOCAL_DOMAIN
LOCAL_EMAIL = 'legal@' + LOCAL_DOMAIN
LOCAL_SCHEME = 'https'
LOCAL_PREFIX = LOCAL_SCHEME + '://'
LOCAL_URL = LOCAL_PREFIX + LOCAL_SUBDOMAIN
REPO_URL = LOCAL_URL + '/repo/'

EXLIM_TITLE = 'Příliš velký počet záznamů'

GR_CHAR = ('znak', 'znaky', 'znaků')
GR_DAY = ('den', 'dny', 'dnů')
GR_BUSDAY = ('pracovní den', 'pracovní dny', 'pracovních dnů')
GR_MONTH = ('měsíc', 'měsíce', 'měsíců')
GR_YEAR = ('rok', 'roky', 'let')

FORMAT_OPTS = (
    ('html', 'HTML'),
    ('xml', 'XML'),
    ('csv', 'CSV'),
    ('json', 'JSON'),
)

IC_REGEX = r'^\d{1,9}$'
RC_REGEX = r'^\d{9,10}$'
RC_FULL_REGEX = r'^\d{6}/\d{3,4}$'
PSC_REGEX = r'^\d{5}$'

DTF = '%Y-%m-%d'
