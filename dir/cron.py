# -*- coding: utf-8 -*-
#
# dir/cron.py
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

from common.utils import text_opt, icmp, LOGGER
from sir.glob import L2S
from dir.models import Debtor, Discovered


def dir_notice(uid):

    text = ''
    debtors = Discovered.objects.filter(uid=uid, vec__link__isnull=False) \
        .order_by('desc', 'id').distinct()
    if debtors:
        text = 'Byli nově zaznamenáni tito dlužníci, ' \
               'které sledujete:\n\n'
        for debtor in debtors:
            text += ' - {0}, sp. zn. {1} {2.senat:d} INS ' \
                '{2.bc:d}/{2.rocnik:d}\n'.format(
                    debtor.desc,
                    L2S[debtor.vec.idOsobyPuvodce],
                    debtor.vec)
            text += '   {}\n\n'.format(debtor.vec.link)
        Discovered.objects.filter(uid=uid, vec__link__isnull=False).delete()
        LOGGER.info(
            'Non-empty notice prepared for user "{}" ({:d})'.format(
                User.objects.get(pk=uid).username, uid))
    return text


def dir_check(osoba, vec):

    for debtor in Debtor.objects.all():
        date_birth = osoba.datumNarozeni
        if date_birth:
            date_birth = date_birth.date()
        if (not debtor.court or debtor.court == osoba.idOsobyPuvodce) \
           and text_opt(debtor.name, osoba.nazevOsoby, debtor.name_opt) \
           and text_opt(debtor.first_name, osoba.jmeno, debtor.first_name_opt) \
           and (not debtor.genid or debtor.genid == osoba.ic) \
           and (not debtor.taxid or icmp(debtor.taxid, osoba.dic)) \
           and (not debtor.birthid or debtor.birthid == osoba.rc) \
           and (not debtor.date_birth or debtor.date_birth == date_birth) \
           and (not debtor.year_birth_from
                or debtor.year_birth_from <= date_birth.year) \
           and (not debtor.year_birth_to
                or debtor.year_birth_to >= date_birth.year):
            if Discovered.objects.update_or_create(
                    uid_id=debtor.uid_id,
                    desc=debtor.desc,
                    vec=vec)[1]:
                LOGGER.info(
                    'New debtor "{}" detected for user "{}" ({:d})'.format(
                        debtor.desc,
                        User.objects.get(pk=debtor.uid_id).username,
                        debtor.uid_id))
