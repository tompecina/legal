# -*- coding: utf-8 -*-
#
# sur/cron.py
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

from django.contrib.auth.models import User

from legal.common.utils import text_opt, LOGGER
from legal.sur.models import Party, Found


def sur_notice(uid):

    text = ''
    res = Found.objects.filter(uid=uid).order_by('name', 'id').distinct()
    if res:
        text = 'Byli nově zaznamenáni tito účastníci řízení, které sledujete:\n\n'
        for item in res:
            text += ' - {0.name}, {0.court}, sp. zn. {0.senate:d} {0.register} {0.number:d}/{0.year:d}\n'.format(item)
            text += '   {}\n\n'.format(item.url)
        Found.objects.filter(uid=uid).delete()
        LOGGER.info('Non-empty notice prepared for user "{}" ({:d})'.format(User.objects.get(pk=uid).username, uid))
    return text


def sur_check(name, court, senate, register, number, year, url):

    for party in Party.objects.all():
        if text_opt(party.party, name, party.party_opt):
            if Found.objects.update_or_create(
                    uid_id=party.uid_id,
                    name=name,
                    court=court,
                    senate=senate,
                    register=register,
                    number=number,
                    year=year,
                    url=url)[1]:
                LOGGER.info(
                    'New party "{}" detected for user "{}" ({:d})'
                    .format(name, User.objects.get(pk=party.uid_id).username, party.uid_id))
