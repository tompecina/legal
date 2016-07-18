# -*- coding: utf-8 -*-
#
# udn/cron.py
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

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from re import compile
from os.path import join
from common.settings import BASE_DIR, TEST
from common.utils import get, post
from .glob import filename_regex
from .utils import decomposeref
from .models import Decision, Party, Agenda

root_url = 'http://www.nssoud.cz/'
form_url = root_url + 'main2Col.aspx?cls=RozhodnutiList&menu=185'
find_url = root_url + 'main0Col.aspx?cls=JudikaturaBasicSearch&pageSource=0'

if TEST:
    repo_pref = join(BASE_DIR, 'test')
else:  # pragma: no cover
    repo_pref = join(BASE_DIR, 'repo/udn')

fr = compile(filename_regex)

OBS = timedelta(days=360)

@require_http_methods(['GET'])
def cron_update(request):
    try:
        res = get(form_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form')
        d = {i['name']: i['value'] for i in form.find_all('input') \
             if i['type']=='hidden' and i.has_attr('value')}
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
                    with open(repo_pref + '/' + fn, 'wb') as fo:
                        if not fo.write(res.content):  # pragma: no cover
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
                            p = Party.objects.get_or_create(name=q.strip())[0]
                            dec.parties.add(p)
                except:
                    pass
            pagers = soup.select('div#PagingBox2')[0]
            cp = int(pagers.b.text[1:-1])
            p = pagers.select('a')
            if cp > len(p):
                break
            form = soup.find('form')
            d = {i['name']: i['value'] for i in form.find_all('input') \
                 if i['type']=='hidden' and i.has_attr('value')}
            d['__EVENTTARGET'] = p[cp - 1]['href'][70:-34]
            d['__EVENTARGUMENT'] = ''
    except:  # pragma: no cover
        pass
    return HttpResponse()

@require_http_methods(['GET'])
def cron_find(request):
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
             if i['type']=='hidden' and i.has_attr('value')}
        ref = ('%s ' % dec.senate) if dec.senate else ''
        ref += '%s %d/%d' % (dec.register, dec.number, dec.year)
        d['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumOd'] = \
        d['_ctl0:ContentPlaceMasterPage:_ctl0:txtDatumDo'] = \
            '%02d.%02d.%04d' % (dec.date.day, dec.date.month, dec.date.year) 
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
            with open(repo_pref + '/' + fn, 'wb') as fo:
                if not fo.write(res.content):  # pragma: no cover
                    return HttpResponse()
            dec.anonfilename = fn
            dec.save()
            return HttpResponse()
    except:
        pass
    return HttpResponse()
