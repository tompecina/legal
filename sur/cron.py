# -*- coding: utf-8 -*-
#
# sur/cron.py
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

from common.utils import text_opt
from .models import Party, Found

def sur_notice(uid):
    text = ''
    ff = Found.objects.filter(uid=uid).order_by('name', 'id').distinct()
    if ff:
        text = 'Byli nově zaznamenáni tito účastníci řízení, které sledujete:\n\n'
        for f in ff:
            text += ' - %s, %s, sp. zn. %d %s %d/%d\n' % \
                    (f.name, f.court, f.senate, f.register, f.number, f.year)
            text += '   %s\n\n' % f.url
        Found.objects.filter(uid=uid).delete()
    return text

def sur_check(name, court, senate, register, number, year, url):
    for p in Party.objects.all():
        if text_opt(p.party, name, p.party_opt):
            Found(
                uid_id=p.uid_id,
                name=name,
                court=court,
                senate=senate,
                register=register,
                number=number,
                year=year,
                url=url).save()