# -*- coding: utf-8 -*-
#
# udn/cron.py
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
from re import compile
from os.path import join
from urllib.parse import quote

from bs4 import BeautifulSoup

from legal.settings import BASE_DIR, TEST, TEST_TEMP_DIR
from legal.common.glob import LOCAL_URL
from legal.common.utils import get, post, composeref, decomposeref, LOGGER, adddoc
from legal.szr.glob import SUPREME_ADMINISTRATIVE_COURT
from legal.szr.models import Court
from legal.sur.cron import sur_check
from legal.udn.glob import FILENAME_RE_STR
from legal.udn.models import Decision, Party, Agenda


APP = __package__.rpartition('.')[2]

ROOT_URL = 'http://www.nssoud.cz/'

FORM_URL = ROOT_URL + 'main2Col.aspx?cls=RozhodnutiList&menu=185'

FIND_URL = ROOT_URL + 'main0Col.aspx?cls=JudikaturaBasicSearch&pageSource=0'

DEC_URL = LOCAL_URL + '/udn/list/?senate={:d}&register={}&number={:d}&year={:d}&page={:d}'

REPO_PREF = TEST_TEMP_DIR if TEST else join(BASE_DIR, 'repo', 'udn')

FRE = compile(FILENAME_RE_STR)

OBS = timedelta(days=360)


def cron_update():

    nss = Court.objects.get(pk=SUPREME_ADMINISTRATIVE_COURT)
    try:
        res = get(FORM_URL)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        dct = {i['name']: i['value'] for i in form.find_all('input') if i['type'] == 'hidden' and i.has_attr('value')}
        while True:
            dct['_ctl0:ContentPlaceMasterPage:_ctl0:ddlSortName'] = '5'
            dct['_ctl0:ContentPlaceMasterPage:_ctl0:ddlSortDirection'] = '1'
            res = post(FORM_URL, dct)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('table.item'):
                try:
                    ttr = item.select('tr')
                    senate, register, number, year, page = decomposeref(ttr[0].td.text.strip())
                    if Decision.objects.filter(
                            senate=senate,
                            register=register,
                            number=number,
                            year=year,
                            page=page).exists():
                        continue
                    fileurl = ttr[4].a['href']
                    filename = fileurl.split('/')[-1]
                    if not FRE.match(filename):
                        continue
                    res = get(ROOT_URL + fileurl)
                    if not res.ok:
                        continue
                    LOGGER.info('Writing abridged decision "{}"'.format(composeref(senate, register, number, year)))
                    with open(join(REPO_PREF, filename), 'wb') as outfile:
                        if not outfile.write(res.content):  # pragma: no cover
                            LOGGER.error(
                                'Failed to write abridged decision "{}"'
                                .format(composeref(senate, register, number, year)))
                            continue
                        adddoc(APP, filename, ROOT_URL + fileurl)
                    agenda = Agenda.objects.get_or_create(desc=ttr[2].td.text.strip())[0]
                    dat = date(*map(int, list(reversed(ttr[3].td.text.split('.')))))
                    dec = Decision(
                        senate=senate,
                        register=register,
                        number=number,
                        year=year,
                        page=page,
                        agenda=agenda,
                        date=dat,
                        filename=filename)
                    dec.save()
                    for query in ttr[1].td:
                        if 'strip' in dir(query):
                            qstrip = query.strip()
                            party = Party.objects.get_or_create(name=qstrip)[0]
                            dec.parties.add(party)
                            sur_check(
                                {'check_udn': True},
                                qstrip,
                                nss,
                                senate,
                                register,
                                number,
                                year,
                                DEC_URL.format(senate, quote(register), number, year, page))
                except:  # pragma: no cover
                    pass
            pagers = soup.select('div#PagingBox2')[0]
            cpag = int(pagers.b.text[1:-1])
            pager = pagers.select('a')
            if cpag > len(pager):
                break
            form = soup.find('form')
            dct = {i['name']: i['value'] for i in form.find_all('input')
                 if i['type'] == 'hidden' and i.has_attr('value')}
            dct['__EVENTTARGET'] = pager[cpag - 1]['href'][70:-34]
            dct['__EVENTARGUMENT'] = ''
    except:  # pragma: no cover
        LOGGER.warning('Update failed')


def cron_find():

    now = datetime.now()
    try:
        dec = Decision.objects.filter(anonfilename='', date__gte=(now - OBS)).earliest('updated')
        dec.updated = now
        dec.save()
        res = get(FIND_URL)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        dct = {i['name']: i['value'] for i in form.find_all('input') if i['type'] == 'hidden' and i.has_attr('value')}
        ref = ('{} '.format(dec.senate) if dec.senate else '')
        ref += '{0.register} {0.number:d}/{0.year:d}'.format(dec)
        dct['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumOd'] = dct['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumDo'] = \
            '{0.day:02d}.{0.month:02d}.{0.year:d}'.format(dec.date)
        dct['_ctl0:ContentPlaceMasterPage:_ctl0:txtSpisovaZnackaFull'] = ref
        dct['_ctl0_ContentPlaceMasterPage__ctl0_rbTypDatum_0'] = 'on'
        res = post(FIND_URL, dct)
        soup = BeautifulSoup(res.text, 'html.parser')
        for anchor in soup.select('table#_ctl0_ContentPlaceMasterPage__ctl0_grwA')[0].select('a[title^=Anonymizovan]'):
            fileurl = anchor['href']
            filename = fileurl.split('/')[-1]
            if not FRE.match(filename):
                continue
            res = get(ROOT_URL + fileurl)
            if not res.ok:
                continue
            LOGGER.info(
                'Writing anonymized decision "{}"'
                .format(composeref(dec.senate, dec.register, dec.number, dec.year)))
            with open(join(REPO_PREF, filename), 'wb') as outfile:
                if not outfile.write(res.content):  # pragma: no cover
                    LOGGER.error(
                        'Failed to write anonymized decision "{}"'
                        .format(composeref(dec.senate, dec.register, dec.number, dec.year)))
                    return
                adddoc(APP, filename, ROOT_URL + fileurl)
            dec.anonfilename = filename
            dec.save()
            return
    except:  # pragma: no cover
        LOGGER.warning('Find failed')
