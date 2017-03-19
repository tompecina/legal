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
from common.utils import text_opt, icmp, logger
from sir.glob import l2s
from .models import Debtor, Discovered

def dir_notice(uid):
    text = ''
    dd = Discovered.objects.filter(uid=uid, vec__link__isnull=False) \
        .order_by('desc', 'id').distinct()
    if dd:
        text = 'Byli nově zaznamenáni tito dlužníci, ' \
               'které sledujete:\n\n'
        for d in dd:
            text += ' - %s, sp. zn. %s %d INS %d/%d\n' % \
                    (d.desc,
                     l2s[d.vec.idOsobyPuvodce],
                     d.vec.senat,
                     d.vec.bc,
                     d.vec.rocnik)
            text += '   %s\n\n' % d.vec.link
        Discovered.objects.filter(uid=uid, vec__link__isnull=False).delete()
        logger.info(
            'Non-empty notice prepared for user "%s" (%d)' % \
            (User.objects.get(pk=uid).username, uid))
    return text

def dir_check(osoba, vec):
    for d in Debtor.objects.all():
        od = osoba.datumNarozeni
        if od:
            od = od.date()
        if ((not d.court) or (d.court == osoba.idOsobyPuvodce)) and \
           text_opt(d.name, osoba.nazevOsoby, d.name_opt) and \
           text_opt(d.first_name, osoba.jmeno, d.first_name_opt) and \
           ((not d.genid) or (d.genid == osoba.ic)) and \
           ((not d.taxid) or icmp(d.taxid, osoba.dic)) and \
           ((not d.birthid) or (d.birthid == osoba.rc)) and \
           ((not d.date_birth) or (d.date_birth == od)) and \
           ((not d.year_birth_from) or (d.year_birth_from <= od.year)) and \
           ((not d.year_birth_to) or (d.year_birth_to >= od.year)):
            if Discovered.objects.update_or_create(
                    uid_id=d.uid_id,
                    desc=d.desc,
                    vec=vec)[1]:
                logger.info('New debtor detected: "' + d.desc + '"')
