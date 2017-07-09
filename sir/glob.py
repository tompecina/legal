# -*- coding: utf-8 -*-
#
# sir/glob.py
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

COURTS = [
    {
        'long': 'KSJIMBM',
        'short': 'KSBR',
        'name': 'Krajský soud v Brně',
        'reg': 'KSJIMBM'},
    {
        'long': 'KSJIMBMP1',
        'short': 'KSJI',
        'name': 'Krajský soud v Brně, pobočka v Jihlavě',
        'reg': 'KSJIMBM'},
    {
        'long': 'KSJICCB',
        'short': 'KSCB',
        'name': 'Krajský soud v Českých Budějovicích',
        'reg': 'KSJICCB'},
    {
        'long': 'KSJICCBP1',
        'short': 'KSTA',
        'name': 'Krajský soud v Českých Budějovicích, pobočka v Táboře',
        'reg': 'KSJICCB'},
    {
        'long': 'KSVYCHK',
        'short': 'KSHK',
        'name': 'Krajský soud v Hradci Králové',
        'reg': 'KSVYCHK'},
    {
        'long': 'KSVYCHKP1',
        'short': 'KSPA',
        'name': 'Krajský soud v Hradci Králové, pobočka v Pardubicích',
        'reg': 'KSVYCHK'},
    {
        'long': 'KSSEMOS',
        'short': 'KSOS',
        'name': 'Krajský soud v Ostravě',
        'reg': 'KSSEMOS'},
    {
        'long': 'KSSEMOSP1',
        'short': 'KSOL',
        'name': 'Krajský soud v Ostravě, pobočka v Olomouci',
        'reg': 'KSSEMOS'},
    {
        'long': 'KSZPCPM',
        'short': 'KSPL',
        'name': 'Krajský soud v Plzni',
        'reg': 'KSZPCPM'},
    {
        'long': 'KSZPCPMP1',
        'short': 'KSKV',
        'name': 'Krajský soud v Plzni, pobočka v Karlových Varech',
        'reg': 'KSZPCPM'},
    {
        'long': 'KSSTCAB',
        'short': 'KSPH',
        'name': 'Krajský soud v Praze',
        'reg': 'KSSTCAB'},
    {
        'long': 'KSSCEUL',
        'short': 'KSUL',
        'name': 'Krajský soud v Ústí nad Labem',
        'reg': 'KSSCEUL'},
    {
        'long': 'KSSECULP1',
        'short': 'KSLB',
        'name': 'Krajský soud v Ústí nad Labem, pobočka v Liberci',
        'reg': 'KSSCEUL'},
    {
        'long': 'MSPHAAB',
        'short': 'MSPH',
        'name': 'Městský soud v Praze',
        'reg': 'MSPHAAB'},
]
l2n = {c['long']: c['name'] for c in COURTS}
l2r = {c['long']: c['reg'] for c in COURTS}
l2s = {c['long']: c['short'] for c in COURTS}

SERVICE_EVENTS = [
    {
        'id': 330,
        'desc': 'Změna XSD dokumentu poznámky',
        'ws': True},
    {
        'id': 371,
        'desc':
        'Informační zpráva',
        'ws': True},
    {
        'id': 4,
        'desc': 'Změna v číselníku událostí',
        'ws': True},
    {
        'id': 2,
        'desc': 'Změna adresy osoby',
        'ws': True},
    {
        'id': 1,
        'desc': 'Změna osoby',
        'ws': True},
    {
        'id': 405,
        'desc': 'Změna senátu věci',
        'ws': True},
    {
        'id': 372,
        'desc': 'Změna stavu věci',
        'ws': True},
    {
        'id': 3,
        'desc': 'Změna věci',
        'ws': True},
    {
        'id': 620,
        'desc': 'Zaslání údajů, které se neposílají',
        'ws': False},
    {
        'id': 626,
        'desc': 'Zasílání neveřejných údaju o změně osoby věřitele v přihlášce',
        'ws': False},
    {
        'id': 641,
        'desc': 'Přenos údajů o konkursu',
        'ws': False},
    {
        'id': 642,
        'desc': 'Smazání údajů o konkursu',
        'ws': False},
    {
        'id': 645, 'desc':
        'Přenos změn údajů ve věci ke konkursu',
        'ws': False},
    {
        'id': 1021,
        'desc': 'Přenos změn údajů o úpadku',
        'ws': False},
    {
        'id': 1022,
        'desc': 'Smazání údajů o úpadku',
        'ws': False},
]
SELIST = [x['id'] for x in SERVICE_EVENTS]

BELIST = [75, 76, 77, 78, 84]

STATES = [
    {
        'id': 'ODDLUŽENÍ',
        'desc': 'Povoleno oddlužení'},
    {
        'id': 'VYRIZENA',
        'desc': 'Vyřízená věc'},
    {
        'id': 'MYLNÝ ZÁP.',
        'desc': 'Mylný zápis do rejstříku'},
    {
        'id': 'REORGANIZ',
        'desc': 'Povolena reorganisace'},
    {
        'id': 'NEVYRIZENA',
        'desc': 'Před rozhodnutím o úpadku'},
    {
        'id': 'NEVYR-POST',
        'desc': 'Postoupená věc'},
    {
        'id': 'ÚPADEK',
        'desc': 'V úpadku'},
    {
        'id': 'MORATORIUM',
        'desc': 'Moratorium'},
    {
        'id': 'OBZIVLA',
        'desc': 'Obživlá věc'},
    {
        'id': 'ZRUŠENO VS',
        'desc': 'Zrušeno vrchním soudem'},
    {
        'id': 'PRAVOMOCNA',
        'desc': 'Pravomocná věc'},
    {
        'id': 'K-PO ZRUŠ.',
        'desc': 'Prohlášený konkurs po zrušení VS'},
    {
        'id': 'ODSKRTNUTA',
        'desc': 'Odškrtnutá – skončená věc'},
    {
        'id': 'KONKURS',
        'desc': 'Prohlášený konkurs'},
]
s2d = {s['id']: s['desc'] for s in STATES}

ROLES = [
    {
        'field': 'debtor',
        'id': 'DLUŽNÍK',
        'desc': 'dlužník'},
    {
        'field': 'trustee',
        'id': 'SPRÁVCE',
        'desc': 'správce'},
    {
        'field': 'creditor',
        'id': 'VĚŘITEL',
        'desc': 'věřitel'},
    {
        'field': 'motioner',
        'id': 'VĚŘIT-NAVR',
        'desc': ' věřitel, který podal insolvenční návrh'},
]
r2i = {x['field']: x['id'] for x in ROLES}
r2d = {x['id']: x['desc'] for x in ROLES}

ADDRESSES = [
    {
        'id': 'E-MAIL',
        'desc': 'email'},
    {
        'id': 'ODDĚLENÍ',
        'desc': 'oddělení'},
    {
        'id': 'OSTATNÍ',
        'desc': 'ostatní'},
    {
        'id': 'POBOČKA',
        'desc': 'pobočka'},
    {
        'id': 'PŘECHODNÁ',
        'desc': 'přechodná'},
    {
        'id': 'SÍDLO FY',
        'desc': 'sídlo firmy'},
    {
        'id': 'SÍDLO ORG.',
        'desc': 'sídlo organizace'},
    {
        'id': 'TRVALÁ',
        'desc': 'trvalá'},
    {
        'id': 'MÍSTO PODN',
        'desc': 'místo podnikání'},
]
a2d = {x['id']: x['desc'] for x in ADDRESSES}
