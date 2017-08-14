# -*- coding: utf-8 -*-
#
# szr/cron.py
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

from datetime import datetime, timedelta
from hashlib import md5
from urllib.parse import quote

from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.db.models import Q

from legal.common.utils import get, post, sleep, LOGGER, composeref
from legal.szr.models import Court, Proceedings
from legal.szr.glob import SUPREME_COURT, SUPREME_ADMINISTRATIVE_COURT


LIST_COURTS = 'public/search.jsp'

LIST_REPORTS = 'InfoSoud/seznamOkresnichSoudu?kraj={}'

ROOT_URL = 'http://infosoud.justice.cz/'

GET_PROC = (
    'InfoSoud/public/search.do?org={}&krajOrg={}&cisloSenatu={:d}&druhVec={}&bcVec={:d}&rocnik={:d}&typSoudu={}'
    '&autoFill=true&type=spzn')

NSS_URL = 'http://www.nssoud.cz/main0Col.aspx?cls=JudikaturaSimpleSearch&pageSource=1&menu=187'

NSS_GET_PROC = 'http://www.nssoud.cz/mainc.aspx?cls=InfoSoud&kau_id={:d}'

UPDATE_DELAY = timedelta(hours=6)


def addauxid(proc):

    if proc.court_id == SUPREME_ADMINISTRATIVE_COURT and not proc.auxid:
        try:
            res = get(NSS_URL)
            soup = BeautifulSoup(res.text, 'html.parser')
            form = soup.find('form')
            dct = {
                i['name']: i['value'] for i in form.find_all('input') if i['type'] == 'hidden' and i.has_attr('value')}
            if int(proc.senate):
                ref = '{} '.format(proc.senate)
            else:
                ref = ''
            ref += '{0.register} {0.number:d}/{0.year:d}'.format(proc)
            dct['_ctl0:ContentPlaceMasterPage:_ctl0:txtSpisovaZnackaFull'] = ref
            res = post(NSS_URL, dct)
            soup = BeautifulSoup(res.text, 'html.parser')
            oncl = (
                soup.select('table#_ctl0_ContentPlaceMasterPage__ctl0_grwA')[0]
                .select('img[src="/Image/infosoud.gif"]')[0]['onclick'])
            proc.auxid = int(oncl.split('=')[-1].split("'")[0])
        except:
            pass


def isreg(court):

    string = court.pk
    return string.startswith('KS') or string == 'MSPHAAB'


def cron_courts():

    try:
        res = get(ROOT_URL + LIST_COURTS)
        soup = BeautifulSoup(res.text, 'html.parser')
        Court.objects.get_or_create(id=SUPREME_COURT, name='Nejvyšší soud')
        Court.objects.get_or_create(id=SUPREME_ADMINISTRATIVE_COURT, name='Nejvyšší správní soud')
        upper = soup.find(id='kraj').find_all('option')[1:]
        lower = soup.find(id='soudy').find_all('option')[1:]
        for court in upper + lower:
            Court.objects.get_or_create(id=court['value'], name=court.string.encode('utf-8'))
    except:  # pragma: no cover
        LOGGER.warning('Error importing courts')
    Court.objects.all().update(reports=None)
    for court in Court.objects.all():
        if isreg(court):
            try:
                sleep(1)
                res = get(ROOT_URL + LIST_REPORTS.format(court.pk))
                soup = BeautifulSoup(res.text, 'xml')
                for item in soup.find_all('okresniSoud'):
                    Court.objects.filter(pk=item.id.string).update(reports=court)
            except:  # pragma: no cover
                LOGGER.warning('Error setting hierarchy for {}'.format(court.id))
    LOGGER.info('Courts imported')


def p2s(proc):

    return '{}, {}'.format(proc.court_id, composeref(proc.senate, proc.register, proc.number, proc.year))


def updateproc(proc):

    notnew = bool(proc.updated)
    proc.updated = datetime.now()
    proc.save()
    court = proc.court_id
    try:
        if court == SUPREME_ADMINISTRATIVE_COURT:
            addauxid(proc)
            if not proc.auxid:
                return
            url = NSS_GET_PROC.format(proc.auxid)
            res = get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', 'frm')
        else:
            court_type = 'ns' if court == SUPREME_COURT else 'os'
            url = ROOT_URL + GET_PROC.format(
                court,
                proc.court.reports.id if proc.court.reports else proc.court.id,
                proc.senate,
                quote(proc.register.upper()),
                proc.number,
                proc.year,
                court_type)
            res = get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('tr', 'AAAA')
        assert table
    except:  # pragma: no cover
        LOGGER.warning(
            'Failed to check proceedings "{0.desc}" ({1}) for user "{2}" ({0.uid_id:d})'
            .format(proc, p2s(proc), User.objects.get(pk=proc.uid_id).username))
        return False
    hsh = md5(str(table).encode()).hexdigest()
    if court != SUPREME_ADMINISTRATIVE_COURT:
        changed = None
        try:
            tbl = table.find_next_sibling().find_next_sibling().table.tr.td.find_next_sibling().text.split()
            if len(tbl) == 4:
                changed = datetime(*map(int, list(reversed(tbl[0].split('.'))) + tbl[1].split(':')))
        except:  # pragma: no cover
            LOGGER.warning(
                'Failed to check proceedings "{0.desc}" ({1}) for user "{2}" ({0.uid_id:d})'
                .format(proc, p2s(proc), User.objects.get(pk=proc.uid_id).username))
        if changed != proc.changed or hsh != proc.hash:
            proc.notify |= notnew
            if changed:
                proc.changed = changed
                LOGGER.info(
                    'Change detected in proceedings "{0.desc}" ({1}) for user "{2}" ({0.uid_id:d})'
                    .format(proc, p2s(proc), User.objects.get(pk=proc.uid_id).username))
    elif hsh != proc.hash:
        proc.notify |= notnew
        if notnew:
            proc.changed = proc.updated
            if proc.changed:
                LOGGER.info(
                    'Change detected in proceedings "{0.desc}" ({1}) for user "{2}" ({0.uid_id:d})'
                    .format(proc, p2s(proc), User.objects.get(pk=proc.uid_id).username))
    proc.hash = hsh
    LOGGER.debug(
        'Proceedings "{0.desc}" ({1}) updated for user "{2}" ({0.uid_id:d})'
        .format(proc, p2s(proc), User.objects.get(pk=proc.uid_id).username))
    return True


def cron_update():

    proc = Proceedings.objects.filter(Q(updated__lte=datetime.now()-UPDATE_DELAY) | Q(updated__isnull=True))
    if proc:
        proc = proc.earliest('updated')
        if updateproc(proc):
            proc.save()


def szr_notice(uid):

    text = ''
    res = Proceedings.objects.filter(uid=uid, notify=True).order_by('desc', 'id')
    if res:
        text = 'V těchto soudních řízeních, která sledujete, došlo ke změně:\n\n'
        for proc in res:
            desc = ' ({})'.format(proc.desc) if proc.desc else ''
            text += ' - {0.court}, sp. zn. {0.senate:d} {0.register} {0.number:d}/{0.year:d}{1}\n'.format(proc, desc)
            if proc.court_id != SUPREME_ADMINISTRATIVE_COURT:
                court_type = 'ns' if proc.court_id == SUPREME_COURT else 'os'
                text += '   {}\n\n'.format(ROOT_URL + GET_PROC.format(
                    proc.court.id,
                    proc.court.reports.id if proc.court.reports
                    else proc.court.id,
                    proc.senate,
                    quote(proc.register.upper()),
                    proc.number,
                    proc.year,
                    court_type))
            elif proc.auxid:
                text += '   {}\n\n'.format(NSS_GET_PROC.format(proc.auxid))
            proc.notify = False
            proc.save()
        LOGGER.info('Non-empty notice prepared for user "{}" ({:d})'.format(User.objects.get(pk=uid).username, uid))
    return text
