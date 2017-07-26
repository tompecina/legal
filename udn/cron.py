# -*- coding: utf-8 -*-
#
# udn/cron.py
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
from re import compile
from os.path import join
from urllib.parse import quote
from bs4 import BeautifulSoup
from common.settings import BASE_DIR, TEST
from common.utils import get, post, composeref, decomposeref, logger
from common.glob import localurl
from szr.glob import supreme_administrative_court
from szr.models import Court
from sur.cron import sur_check
from udn.glob import filename_regex
from udn.models import Decision, Party, Agenda


root_url = 'http://www.nssoud.cz/'

form_url = root_url + 'main2Col.aspx?cls=RozhodnutiList&menu=185'

find_url = root_url + 'main0Col.aspx?cls=JudikaturaBasicSearch&pageSource=0'

decurl = localurl + \
    '/udn/list/?senate={:d}&register={}&number={:d}&year={:d}&page={:d}'

if TEST:
    repo_pref = join(BASE_DIR, 'test')
else:  # pragma: no cover
    repo_pref = join(BASE_DIR, 'repo', 'udn')

fr = compile(filename_regex)

OBS = timedelta(days=360)


def cron_update():

    NSS = Court.objects.get(pk=supreme_administrative_court)
    try:
        res = get(form_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        d = {i['name']: i['value'] for i in form.find_all('input') \
             if i['type'] == 'hidden' and i.has_attr('value')}
        while True:
            d['_ctl0:ContentPlaceMasterPage:_ctl0:ddlSortName'] = '5'
            d['_ctl0:ContentPlaceMasterPage:_ctl0:ddlSortDirection'] = '1'
            res = post(form_url, d)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('table.item'):
                try:
                    r = item.select('tr')
                    senate, register, number, year, page = \
                        decomposeref(r[0].td.text.strip())
                    if Decision.objects.filter(
                            senate=senate,
                            register=register,
                            number=number,
                            year=year,
                            page=page).exists():
                        continue
                    furl = r[4].a['href']
                    fn = furl.split('/')[-1]
                    if not fr.match(fn):
                        continue
                    res = get(root_url + furl)
                    if not res.ok:
                        continue
                    logger.info(
                        'Writing abridged decision "{}"' \
                            .format(
                                composeref(
                                    senate,
                                    register,
                                    number,
                                    year)))
                    with open(join(repo_pref, fn), 'wb') as fo:
                        if not fo.write(res.content):  # pragma: no cover
                            logger.error(
                                'Failed to write abridged decision "{}"' \
                                    .format(
                                        composeref(
                                            senate,
                                            register,
                                            number,
                                            year)))
                            continue
                    a = Agenda.objects.get_or_create( \
                        desc=r[2].td.text.strip())[0]
                    dt = date(*map(int, list(reversed(r[3].td.text \
                        .split('.')))))
                    dec = Decision(
                        senate=senate,
                        register=register,
                        number=number,
                        year=year,
                        page=page,
                        agenda=a,
                        date=dt,
                        filename=fn)
                    dec.save()
                    for q in r[1].td:
                        if 'strip' in dir(q):
                            qs = q.strip()
                            p = Party.objects.get_or_create(name=qs)[0]
                            dec.parties.add(p)
                            sur_check(
                                qs,
                                NSS,
                                senate,
                                register,
                                number,
                                year,
                                decurl.format(
                                    senate,
                                    quote(register),
                                    number,
                                    year,
                                    page))
                except:  # pragma: no cover
                    pass
            pagers = soup.select('div#PagingBox2')[0]
            cp = int(pagers.b.text[1:-1])
            p = pagers.select('a')
            if cp > len(p):
                break
            form = soup.find('form')
            d = {i['name']: i['value'] for i in form.find_all('input') \
                 if i['type'] == 'hidden' and i.has_attr('value')}
            d['__EVENTTARGET'] = p[cp - 1]['href'][70:-34]
            d['__EVENTARGUMENT'] = ''
    except:  # pragma: no cover
        logger.warning('Update failed')


def cron_find():

    now = datetime.now()
    try:
        dec = Decision.objects.filter(
            anonfilename='',
            date__gte=(now - OBS)).earliest('updated')
        dec.updated = now
        dec.save()
        res = get(find_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        d = {i['name']: i['value'] for i in form.find_all('input') \
             if i['type'] == 'hidden' and i.has_attr('value')}
        ref = ('{} '.format(dec.senate) if dec.senate else '')
        ref += '{} {:d}/{:d}'.format(dec.register, dec.number, dec.year)
        d['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumOd'] = \
        d['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumDo'] = \
            '{:02d}.{:02d}.{:d}' \
                .format(dec.date.day, dec.date.month, dec.date.year)
        d['_ctl0:ContentPlaceMasterPage:_ctl0:txtSpisovaZnackaFull'] = ref
        d['_ctl0_ContentPlaceMasterPage__ctl0_rbTypDatum_0'] = 'on'
        res = post(find_url, d)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.select('table#_ctl0_ContentPlaceMasterPage__ctl0_grwA') \
            [0].select('a[title^=Anonymizovan]'):
            furl = a['href']
            fn = furl.split('/')[-1]
            if not fr.match(fn):
                continue
            res = get(root_url + furl)
            if not res.ok:
                continue
            logger.info(
                'Writing anonymized decision "{}"' \
                    .format(
                        composeref(
                            dec.senate,
                            dec.register,
                            dec.number,
                            dec.year)))
            with open(join(repo_pref, fn), 'wb') as fo:
                if not fo.write(res.content):  # pragma: no cover
                    logger.error(
                        'Failed to write anonymized decision "{}"' \
                            .format(
                                composeref(
                                    dec.senate,
                                    dec.register,
                                    dec.number,
                                    dec.year)))
                    return
            dec.anonfilename = fn
            dec.save()
            return
    except:  # pragma: no cover
        logger.warning('Find failed')
