# -*- coding: utf-8 -*-
#
# psj/cron.py
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

from datetime import date, datetime, timedelta
from urllib.parse import quote
from bs4 import BeautifulSoup
from django.http import QueryDict
from common.utils import get, decomposeref, normreg, sleep, logger
from common.glob import localurl
from szr.models import Court
from szr.glob import supreme_court, supreme_administrative_court
from sur.cron import sur_check
from psj.models import Courtroom, Judge, Form, Hearing, Party, Task


list_courtrooms = \
    'http://infosoud.justice.cz/InfoSoud/seznamJednacichSini?okres={}'

hearingurl = localurl + '/psj/list/?court={}&senate={:d}&register={}&' \
    'number={:d}&year={:d}&date_from={}&date_to={}'


def cron_courtrooms():

    for c in Court.objects.exclude(id=supreme_administrative_court):
        try:
            sleep(1)
            res = get(list_courtrooms.format(c.pk))
            soup = BeautifulSoup(res.text, 'xml')
            for r in soup.find_all('jednaciSin'):
                cr, crc = Courtroom.objects.get_or_create(
                    court=c,
                    desc=r.nazev.string)
                if not crc:
                    cr.save()
        except:  # pragma: no cover
            logger.warning('Error downloading courtrooms')
    logger.info('Courtrooms downloaded')


def cron_schedule(*args):

    dd = []
    for a in args:
        if len(a) > 2:
            s = a.split('.')
            dd.append(date(int(s[2]), int(s[1]), int(s[0])))
        else:
            dd.append(date.today() + timedelta(int(a)))
    for court in Court.objects.all():
        if court.id in [supreme_court, supreme_administrative_court]:
            continue
        for d in dd:
            Task.objects.get_or_create(court=court, date=d)
    logger.info('Tasks scheduled')


root_url = 'http://infosoud.justice.cz/'

get_hear = 'InfoSoud/public/searchJednani.do?'


def cron_update():

    t = Task.objects.all()
    if not t.exists():
        return
    t = t.earliest('timestamp_update')
    t.save()
    if t.court.reports:
        c0 = 'os'
        c1 = t.court.reports.id
        c2 = t.court.id
    else:
        c0 = 'os'
        c1 = t.court.id
        c2 = ''
    tdate = str(t.date)
    try:
        for cr in Courtroom.objects.filter(court=t.court):
            q = QueryDict(mutable=True)
            q['type'] = 'jednani'
            q['typSoudu'] = c0
            q['krajOrg'] = c1
            q['org'] = c2
            q['sin'] = cr.desc
            q['datum'] = '{0.day:d}.{0.month:d}.{0.year:d}'.format(t.date)
            q['spamQuestion'] = '23'
            q['druhVec'] = ''
            url = root_url + get_hear + q.urlencode()
            sleep(1)
            res = get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            sched = soup.select('table tr td + td table tr td table tr')[6]
            if sched.select('b'):
                continue
            for tr in sched.td.table.children:
                try:
                    td = tr.td
                    tm = td.text.split(':')
                    tm = datetime(
                        t.date.year,
                        t.date.month,
                        t.date.day,
                        int(tm[0]),
                        int(tm[1]))
                    td = td.find_next_sibling('td')
                    senate, register, number, year = \
                        decomposeref(td.text.replace(' / ', '/'))
                    register = normreg(register)
                    td = td.find_next_sibling('td')
                    form = Form.objects.get_or_create(name=td.text.strip())[0]
                    td = td.find_next_sibling('td')
                    judge = Judge.objects.get_or_create(name=td.text.strip())[0]
                    td = td.find_next_sibling('td')
                    parties = td.select('td')
                    td = td.find_next_sibling('td')
                    closed = 'Ano' in td.text
                    td = td.find_next_sibling('td')
                    cancelled = 'Ano' in td.text
                    hearing = Hearing.objects.update_or_create(
                        courtroom=cr,
                        time=tm,
                        senate=senate,
                        register=register,
                        number=number,
                        year=year,
                        form=form,
                        judge=judge,
                        defaults={
                            'closed': closed,
                            'cancelled': cancelled})
                    if hearing[1]:
                        for q in parties:
                            qts = q.text.strip()
                            if qts:
                                p = Party.objects.get_or_create(
                                    name=q.text.strip())[0]
                                hearing[0].parties.add(p)
                                sur_check(
                                    qts,
                                    t.court,
                                    senate,
                                    register,
                                    number,
                                    year,
                                    hearingurl.format(
                                        t.court.id,
                                        senate,
                                        quote(register),
                                        number,
                                        year,
                                        tdate,
                                        tdate))
                except:
                    pass
        t.delete()
    except:
        logger.warning(
            'Failed to download hearings for {0}, '
            '{1.year:d}-{1.month:02d}-{1.day:02d}'
                .format(t.court_id, t.date))
        return
    logger.debug(
        'Downloaded hearings for {0}, {1.year:d}-{1.month:02d}-{1.day:02d}'
            .format(t.court_id, t.date))
