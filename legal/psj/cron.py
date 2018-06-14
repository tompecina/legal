# -*- coding: utf-8 -*-
#
# psj/cron.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from legal.common.glob import LOCAL_URL
from legal.common.utils import get, decomposeref, normreg, sleep, LOGGER
from legal.szr.models import Court
from legal.szr.glob import SUPREME_COURT, SUPREME_ADMINISTRATIVE_COURT
from legal.sur.cron import sur_check
from legal.psj.models import Courtroom, Judge, Form, Hearing, Party, Task


LIST_COURTROOMS = 'http://infosoud.justice.cz/InfoSoud/seznamJednacichSini?okres={}'

HEARING_URL = LOCAL_URL + '/psj/list/?court={}&senate={:d}&register={}&number={:d}&year={:d}&date_from={}&date_to={}'

def cron_courtrooms():

    for court in Court.objects.exclude(id=SUPREME_ADMINISTRATIVE_COURT):
        try:
            sleep(1)
            res = get(LIST_COURTROOMS.format(court.pk))
            soup = BeautifulSoup(res.text, 'xml')
            for room in soup.find_all('jednaciSin'):
                croom, croomc = Courtroom.objects.get_or_create(
                    court=court,
                    desc=room.nazev.string)
                if not croomc:
                    croom.save()
        except:  # pragma: no cover
            LOGGER.warning('Error downloading courtrooms')
    LOGGER.info('Courtrooms downloaded')


def cron_schedule(*args):

    dates = []
    for arg in args:
        if len(arg) > 2:
            string = arg.split('.')
            dates.append(date(*map(int, string[2::-1])))
        else:
            dates.append(date.today() + timedelta(int(arg)))
    for court in Court.objects.all():
        if court.id in {SUPREME_COURT, SUPREME_ADMINISTRATIVE_COURT}:
            continue
        for dat in dates:
            Task.objects.get_or_create(court=court, date=dat)
    LOGGER.info('Tasks scheduled')


ROOT_URL = 'http://infosoud.justice.cz/'

GET_HEARINGS = 'InfoSoud/public/searchJednani.do?'


def cron_update():

    tasks = Task.objects.all()
    if not tasks.exists():
        return
    task = tasks.earliest('timestamp_update')
    task.save()
    court0 = 'os'
    if task.court.reports:
        court1 = task.court.reports.id
        court2 = task.court.id
    else:
        court1 = task.court.id
        court2 = ''
    tdate = str(task.date)
    try:
        for croom in Courtroom.objects.filter(court=task.court):
            query = QueryDict(mutable=True)
            query['type'] = 'jednani'
            query['typSoudu'] = court0
            query['krajOrg'] = court1
            query['org'] = court2
            query['sin'] = croom.desc
            query['datum'] = '{0.day:d}.{0.month:d}.{0.year:d}'.format(task.date)
            query['spamQuestion'] = '23'
            query['druhVec'] = ''
            url = ROOT_URL + GET_HEARINGS + query.urlencode()
            sleep(1)
            res = get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            sched = soup.select('table tr td + td table tr td table tr')[6]
            if sched.select('b'):
                continue
            for ttr in sched.td.table.children:
                try:
                    ttd = ttr.td
                    ttm = ttd.text.split(':')
                    ttm = datetime(
                        task.date.year,
                        task.date.month,
                        task.date.day,
                        int(ttm[0]),
                        int(ttm[1]))
                    ttd = ttd.find_next_sibling('td')
                    senate, register, number, year = decomposeref(ttd.text.replace(' / ', '/'))
                    register = normreg(register)
                    ttd = ttd.find_next_sibling('td')
                    form = Form.objects.get_or_create(name=ttd.text.strip())[0]
                    ttd = ttd.find_next_sibling('td')
                    judge = Judge.objects.get_or_create(name=ttd.text.strip())[0]
                    ttd = ttd.find_next_sibling('td')
                    parties = ttd.select('td')
                    ttd = ttd.find_next_sibling('td')
                    closed = 'Ano' in ttd.text
                    ttd = ttd.find_next_sibling('td')
                    cancelled = 'Ano' in ttd.text
                    hearing = Hearing.objects.update_or_create(
                        courtroom=croom,
                        time=ttm,
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
                        for query in parties:
                            qts = query.text.strip()
                            if qts:
                                party = Party.objects.get_or_create(name=query.text.strip())[0]
                                hearing[0].parties.add(party)
                                sur_check(
                                    {'check_psj': True},
                                    qts,
                                    task.court,
                                    senate,
                                    register,
                                    number,
                                    year,
                                    HEARING_URL.format(
                                        task.court.id,
                                        senate,
                                        quote(register),
                                        number,
                                        year,
                                        tdate,
                                        tdate))
                except:
                    pass
        task.delete()
    except:
        LOGGER.warning(
            'Failed to download hearings for {0}, {1.year:d}-{1.month:02d}-{1.day:02d}'
            .format(task.court_id, task.date))
        return
    LOGGER.debug(
        'Downloaded hearings for {0}, {1.year:d}-{1.month:02d}-{1.day:02d}'.format(task.court_id, task.date))


LIST_COURTROOMS2 = 'http://www.nssoud.cz/main2col.aspx?cls=verejnejednanilist'

def cron_update2():

    nss = Court.objects.get(pk=SUPREME_ADMINISTRATIVE_COURT)
    croom = Courtroom.objects.get_or_create(court=nss, desc='(neuvedeno)')[0]
    form = Form.objects.get_or_create(name='Veřejné jednání')[0]
    try:
        res = get(LIST_COURTROOMS2)
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('table.item'):
            try:
                senate = register = number = year = judge = ttm = None
                parties = []
                for trow in item.select('tr'):
                    ths = trow.th.text.strip()
                    tds = trow.td.text.strip()
                    if ths.startswith('Spisová značka:'):
                        senate, register, number, year = decomposeref(tds)
                    elif ths.startswith('Účastníci řízení:'):
                        for query in trow.td:
                            if 'strip' in dir(query):
                                party = Party.objects.get_or_create(name=query.strip())[0]
                                parties.append(party)
                    elif ths.startswith('Předseda senátu:'):
                        judge = Judge.objects.get_or_create(name=tds)[0]
                    elif ths.startswith('Datum jednání:'):
                        dtm = tds.split()
                        dat = list(map(int, dtm[0].split('.')))
                        tim = list(map(int, dtm[2].split(':')))
                        ttm = datetime(dat[2], dat[1], dat[0], tim[0], tim[1])
                hearing = Hearing.objects.update_or_create(
                    courtroom=croom,
                    time=ttm,
                    senate=senate,
                    register=register,
                    number=number,
                    year=year,
                    form=form,
                    judge=judge,
                    closed=False,
                    cancelled=False)
                if hearing[1]:
                    for party in parties:
                        hearing[0].parties.add(party)
                        sur_check(
                            {'check_psj': True},
                            party.name,
                            nss,
                            senate,
                            register,
                            number,
                            year,
                            HEARING_URL.format(
                                nss.id,
                                senate,
                                quote(register),
                                number,
                                year,
                                ttm.date(),
                                ttm.date()))
            except:  # pragma: no cover
                pass
    except:  # pragma: no cover
        LOGGER.warning('Supreme Administrative Court update failed')
