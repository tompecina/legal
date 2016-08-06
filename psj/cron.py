# -*- coding: utf-8 -*-
#
# psj/cron.py
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

from django.http import QueryDict
from bs4 import BeautifulSoup
from time import sleep
from datetime import date, datetime, timedelta
from common.utils import get, decomposeref, normreg
from szr.models import Court
from szr.glob import supreme_court, supreme_administrative_court
from .models import Courtroom, Judge, Form, Hearing, Party, Task

list_courtrooms = \
    'http://infosoud.justice.cz/InfoSoud/seznamJednacichSini?okres=%s'

def courtrooms():
    for c in Court.objects.exclude(id=supreme_administrative_court):
        try:
            sleep(1)
            res = get(list_courtrooms % c.pk)
            soup = BeautifulSoup(res.text, 'xml')
            for r in soup.find_all('jednaciSin'):
                Courtroom.objects.get_or_create(
                    court=c,
                    desc=r.nazev.string)
        except:
            pass

def importpj():

    ct = {
        'KSJIMBM': 'krajsky-soud-v-brne',
        'KSJICCB': 'krajsky-soud-v-ceskych-budejovicich',
        'KSVYCHK': 'krajsky-soud-v-hradci-kralove',
        'KSSEMOS': 'krajsky-soud-v-ostrave',
        'KSZPCPM': 'krajsky-soud-v-plzni',
        'KSSTCAB': 'krajsky-soud-v-praze',
        'KSSCEUL': 'krajsky-soud-v-usti-nad-labem',
        'OSJIMBM': 'mestsky-soud-v-brne',
        'MSPHAAB': 'mestsky-soud-v-praze',
        'OSPHA01': 'obvodni-soud-pro-prahu-1',
        'OSPHA02': 'obvodni-soud-pro-prahu-2',
        'OSPHA03': 'obvodni-soud-pro-prahu-3',
        'OSPHA04': 'obvodni-soud-pro-prahu-4',
        'OSPHA05': 'obvodni-soud-pro-prahu-5',
        'OSPHA06': 'obvodni-soud-pro-prahu-6',
        'OSPHA07': 'obvodni-soud-pro-prahu-7',
        'OSPHA08': 'obvodni-soud-pro-prahu-8',
        'OSPHA09': 'obvodni-soud-pro-prahu-9',
        'OSPHA10': 'obvodni-soud-pro-prahu-10',
        'OSSTCBN': 'okresni-soud-v-benesove',
        'OSSTCBE': 'okresni-soud-v-beroune',
        'OSJIMBK': 'okresni-soud-v-blansku',
        'OSJIMBO': 'okresni-soud-brno-venkov',
        'OSSEMBR': 'okresni-soud-v-bruntale',
        'OSJIMBV': 'okresni-soud-v-breclavi',
        'OSSCECL': 'okresni-soud-v-ceske-lipe',
        'OSJICCB': 'okresni-soud-v-ceskych-budejovicich',
        'OSJICCK': 'okresni-soud-v-ceskem-krumlove',
        'OSSCEDC': 'okresni-soud-v-decine',
        'OSZPCDO': 'okresni-soud-v-domazlicich',
        'OSSEMFM': 'okresni-soud-ve-frydku-mistku',
        'OSVYCHB': 'okresni-soud-v-havlickove-brode',
        'OSJIMHO': 'okresni-soud-v-hodonine',
        'OSVYCHK': 'okresni-soud-v-hradci-kralove',
        'OSZPCCH': 'okresni-soud-v-chebu',
        'OSSCECV': 'okresni-soud-v-chomutove',
        'OSVYCCR': 'okresni-soud-v-chrudimi',
        'OSSCEJN': 'okresni-soud-v-jablonci-nad-nisou',
        'OSSEMJE': 'okresni-soud-v-jeseniku',
        'OSVYCJC': 'okresni-soud-v-jicine',
        'OSJIMJI': 'okresni-soud-v-jihlave',
        'OSJICJH': 'okresni-soud-v-jindrichove-hradci',
        'OSZPCKV': 'okresni-soud-v-karlovych-varech',
        'OSSEMKA': 'okresni-soud-v-karvine',
        'OSSTCKL': 'okresni-soud-v-kladne',
        'OSZPCKT': 'okresni-soud-v-klatovech',
        'OSSTCKO': 'okresni-soud-v-koline',
        'OSJIMKM': 'okresni-soud-v-kromerizi',
        'OSSTCKH': 'okresni-soud-v-kutne-hore',
        'OSSCELB': 'okresni-soud-v-liberci',
        'OSSCELT': 'okresni-soud-v-litomericich',
        'OSSCELN': 'okresni-soud-v-lounech',
        'OSSTCME': 'okresni-soud-v-melniku',
        'OSSTCMB': 'okresni-soud-v-mlade-boleslavi',
        'OSSCEMO': 'okresni-soud-v-moste',
        'OSVYCNA': 'okresni-soud-v-nachode',
        'OSSEMNJ': 'okresni-soud-v-novem-jicine',
        'OSSTCNB': 'okresni-soud-v-nymburce',
        'OSSEMOC': 'okresni-soud-v-olomouci',
        'OSSEMOP': 'okresni-soud-v-opave',
        'OSSEMOS': 'okresni-soud-v-ostrave',
        'OSVYCPA': 'okresni-soud-v-pardubicich',
        'OSJICPE': 'okresni-soud-v-pelhrimove',
        'OSJICPI': 'okresni-soud-v-pisku',
        'OSZPCPJ': 'okresni-soud-plzen-jih',
        'OSZPCPM': 'okresni-soud-plzen-mesto',
        'OSZPCPS': 'okresni-soud-plzen-sever',
        'OSSTCPY': 'okresni-soud-praha-vychod',
        'OSSTCPZ': 'okresni-soud-praha-zapad',
        'OSJICPT': 'okresni-soud-v-prachaticich',
        'OSJIMPV': 'okresni-soud-v-prostejove',
        'OSSEMPR': 'okresni-soud-v-prerove',
        'OSSTCPB': 'okresni-soud-v-pribrami',
        'OSSTCRA': 'okresni-soud-v-rakovniku',
        'OSZPCRO': 'okresni-soud-v-rokycanech',
        'OSVYCRK': 'okresni-soud-v-rychnove-nad-kneznou',
        'OSVYCSM': 'okresni-soud-v-semilech',
        'OSZPCSO': 'okresni-soud-v-sokolove',
        'OSJICST': 'okresni-soud-v-strakonicich',
        'OSVYCSY': 'okresni-soud-ve-svitavach',
        'OSSEMSU': 'okresni-soud-v-sumperku',
        'OSJICTA': 'okresni-soud-v-tabore',
        'OSZPCTC': 'okresni-soud-v-tachove',
        'OSSCETP': 'okresni-soud-v-teplicich',
        'OSVYCTU': 'okresni-soud-v-trutnove',
        'OSJIMTR': 'okresni-soud-v-trebici',
        'OSJIMUH': 'okresni-soud-v-uherskem-hradisti',
        'OSSCEUL': 'okresni-soud-v-usti-nad-labem',
        'OSVYCUO': 'okresni-soud-v-usti-nad-orlici',
        'OSSEMVS': 'okresni-soud-ve-vsetine',
        'OSJIMVY': 'okresni-soud-ve-vyskove',
        'OSJIMZL': 'okresni-soud-ve-zline',
        'OSJIMZN': 'okresni-soud-ve-znojme',
        'OSJIMZR': 'okresni-soud-ve-zdaru-nad-sazavou',
        'VSSEMOL': 'vrchni-soud-v-olomouci',
        'VSPHAAB': 'vrchni-soud-v-praze',
    }

    for court in ct:
        url = 'http://www.prehledjednani.cz/%s.html' % ct[court]
        res = get(url)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        hh = soup.select('h2')
        for h in hh:
            d = h.text.split()
            dt = [int(d[3]), int(d[2][:-1]), int(d[1][:-1])]
            rr = h.find_next('tbody').select('tr')
            for r in rr:
                try:
                    dd = r.select('td')
                    tm = dd[0].text.split(':')
                    tm = datetime(*dt, int(tm[0]), int(tm[1]))
                    senate, register, number, year = \
                        decomposeref(dd[1].text.replace(' / ', '/'))
                    register = normreg(register)
                    courtroom = Courtroom.objects.get_or_create(
                        court_id=court,
                        desc=dd[2].text)[0]
                    judge = Judge.objects.get_or_create(name=dd[3].text)[0]
                    form = Form.objects.get_or_create(name=dd[5].text)[0]
                    closed = 'ano' in dd[6].text
                    cancelled = 'ano' in dd[7].text
                    hearing = Hearing.objects.update_or_create(
                        courtroom=courtroom,
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
                        for q in dd[4]:
                            if 'strip' in dir(q):
                                p = Party.objects.get_or_create(
                                    name=q.strip())[0]
                                hearing[0].parties.add(p)
                except:
                    pass

def schedule():
    for court in Court.objects.all():
        if court.id in [supreme_court, supreme_administrative_court]:
            continue
        for d in [14, 28]:
            dt = date.today() + timedelta(d)
            Task.objects.get_or_create(court=court, date=dt)

root_url = 'http://infosoud.justice.cz/'
get_hear = 'InfoSoud/public/searchJednani.do?'

def update():
    t = Task.objects.all()
    if not t:
        return
    t = t.earliest('timestamp')
    t.save()
    if t.court.reports:
        c0 = 'os'
        c1 = t.court.reports.id
        c2 = t.court.id
    else:
        c0 = 'os'
        c1 = t.court.id
        c2 = ''
    try:
        for cr in Courtroom.objects.filter(court=t.court):
            q = QueryDict(mutable=True)
            q['type'] = 'jednani'
            q['typSoudu'] = c0
            q['krajOrg'] = c1
            q['org'] = c2
            q['sin'] = cr.desc
            q['datum'] = '%d.%d.%d' % (t.date.day, t.date.month, t.date.year)
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
                            if q.text.strip():
                                p = Party.objects.get_or_create(
                                    name=q.text.strip())[0]
                                hearing[0].parties.add(p)
                except:
                    pass
        t.delete()
    except:
        pass
