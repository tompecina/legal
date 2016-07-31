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

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from bs4 import BeautifulSoup
from time import sleep
from datetime import date, datetime
from common.utils import get, decomposeref, normreg
from szr.models import Court
from szr.glob import supreme_administrative_court
from .models import Courtroom, Judge, Form, Hearing, Party

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

@require_http_methods(['GET'])
def cron_import(request):
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
                                p = Party.objects.get_or_create(name=q.strip())[0]
                                hearing[0].parties.add(p)
                except:
                    pass
    return HttpResponse()
