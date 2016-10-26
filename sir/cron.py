# -*- coding: utf-8 -*-
#
# sir/cron.py
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

from django.db.models import Max
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
from os.path import join
from common.settings import BASE_DIR, TEST
from common.utils import normalize, get, post
from szr.glob import root_url, get_proc
from .glob import COURTS, l2n, l2r, l2s, SELIST, BELIST
from .models import (
    DruhStavRizeni, Vec, DruhRoleVRizeni, Osoba, DruhAdresy, Adresa, Counter,
    Transaction, Insolvency, Tracked)

PREF = 20
                
def convdt(s):
    return datetime.strptime(s.string[:19], "%Y-%m-%dT%H:%M:%S")

def convd(s):
    return datetime.strptime(s.string[:10], "%Y-%m-%d")

def cron_gettr():
    id = Counter.objects.get(id='DL').number
    while True:
        soup = BeautifulSoup('', 'lxml')
        soup.is_xml = True

        envelope = soup.handle_starttag(
            'Envelope', None,
            'soapenv', {
                'xmlns:soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xmlns:typ': 'http://isirpublicws.cca.cz/types/'})
        header = soup.new_tag('Header', None, 'soapenv')
        envelope.append(header)
        body = soup.new_tag('Body', None, 'soapenv')
        envelope.append(body)
        req = soup.new_tag('getIsirWsPublicIdDataRequest', None, 'typ')
        body.append(req)
        idPodnetu = soup.new_tag('idPodnetu', None, None)
        idPodnetu.append(str(id))
        req.append(idPodnetu)
        url = 'https://isir.justice.cz:8443/isir_public_ws/IsirWsPublicService'

        headers = {
            'content-type': 'text/xml; charset=utf-8',
            'SOAPAction': '"http://isirpublicws.cca.cz/types/"',
        }

        res = post(url, soup.renderContents(), headers=headers)

        xml = res.content.decode('utf-8')
        
        soup = BeautifulSoup(xml, 'lxml')
        soup.is_xml = True

        if (not soup.stav) or \
           (soup.stav.string != 'OK') or \
           (not soup.find('data')):
            break

        l = []
        for t_data in soup.find_all('data'):
            id = int(t_data.id.string)
            l.append(Transaction(
                id=id,
                datumZalozeniUdalosti=convdt(t_data.datumzalozeniudalosti),
                datumZverejneniUdalosti=convdt(t_data.datumzverejneniudalosti),
                dokumentUrl=(t_data.dokumenturl.string.strip() \
                    if t_data.dokumenturl else None),
                spisovaZnacka=t_data.spisovaznacka.string.strip(),
                typUdalosti=t_data.typudalosti.string.strip(),
                popisUdalosti=t_data.popisudalosti.string.strip(),
                oddil=t_data.oddil.string.strip() if t_data.oddil else None,
                cisloVOddilu=(int(t_data.cislovoddilu.string) \
                    if t_data.cislovoddilu else None),
                poznamkaText=(t_data.poznamka.string.strip() \
                    if t_data.poznamka else None)))

        Transaction.objects.bulk_create(l)

def cron_proctr():
    id = Counter.objects.get(id='DL').number
    for tr in Transaction.objects.filter(id__gt=id).order_by('id'):
        id = tr.id
        try:
            bc, rocnik = \
                map(int, tr.spisovaZnacka.split()[-1].split('/'))
            if (bc <= 0) or (rocnik <= 0):
                continue
            datumZalozeniUdalosti = tr.datumZalozeniUdalosti

            poznamkaText = tr.poznamkaText.strip()
            subsoup = BeautifulSoup(poznamkaText, 'lxml')
            subsoup.is_xml = True

            t_udalost = subsoup.find('ns2:udalost')
            t_vec = t_udalost.vec
            t_osoba = t_udalost.osoba

            idOsobyPuvodce = t_udalost.idosobypuvodce.string.strip()
            druhStavRizeni = None
            if t_vec:
                if t_vec.druhstavrizeni:
                    druhStavRizeni = DruhStavRizeni.objects.get_or_create(
                        desc=t_vec.druhstavrizeni.string.strip())[0]

            vec, c_vec = Vec.objects.get_or_create(
                idOsobyPuvodce=idOsobyPuvodce,
                bc=bc,
                rocnik=rocnik,
                defaults={
                    'firstAction': datumZalozeniUdalosti.date(),
                    'lastAction': datumZalozeniUdalosti.date()})

            if druhStavRizeni:
                vec.druhStavRizeni = druhStavRizeni

            if t_udalost.datumvyskrtnuti:
                vec.datumVyskrtnuti = convd(t_udalost.datumvyskrtnuti)
            elif (not vec.lastAction) or \
                 (datumZalozeniUdalosti.date() > vec.lastAction):
                vec.lastAction = datumZalozeniUdalosti.date()

            vec.save()

            if tr.oddil and tr.typUdalosti:
                typUdalosti = int(tr.typUdalosti)
                if typUdalosti not in SELIST:
                    for i in Insolvency.objects.filter(number=bc, year=rocnik):
                        if i.detailed or (typUdalosti in BELIST):
                            Tracked.objects.get_or_create(
                                uid=i.uid,
                                desc=i.desc,
                                vec=vec)

            if t_osoba:
                idOsoby = t_osoba.idosoby.string.strip()
                druhRoleVRizeni = DruhRoleVRizeni.objects.get_or_create(
                    desc=t_osoba.druhrolevrizeni.string.strip())[0]
                nazevOsoby = normalize(t_osoba.nazevosoby.string)
                osoba, c_osoba = Osoba.objects.get_or_create(
                    idOsobyPuvodce=idOsobyPuvodce,
                    idOsoby=idOsoby,
                    defaults={
                        'druhRoleVRizeni': druhRoleVRizeni,
                        'nazevOsoby': nazevOsoby})
                if t_osoba.nazevosobyobchodni:
                    nazevOsobyObchodni = \
                        normalize(t_osoba.nazevosobyobchodni.string)
                else:
                    nazevOsobyObchodni = None
                if t_osoba.jmeno:
                    jmeno = normalize(t_osoba.jmeno.string)
                else:
                    jmeno = None
                if t_osoba.titulpred:
                    titulPred = normalize(t_osoba.titulpred.string)
                else:
                    titulPred = None
                if t_osoba.titulza:
                    titulZa = normalize(t_osoba.titulza.string)
                else:
                    titulZa = None
                if t_osoba.ic:
                    ic = normalize(t_osoba.ic.string)
                else:
                    ic = None
                if t_osoba.dic:
                    dic = normalize(t_osoba.dic.string)
                else:
                    dic = None
                if t_osoba.datumnarozeni:
                    datumNarozeni = convd(t_osoba.datumnarozeni)
                else:
                    datumNarozeni = None
                if t_osoba.rc:
                    rc = t_osoba.rc.string.strip().replace('/', '')
                else:
                    rc = None
                if (not datumNarozeni) and rc:
                    year = int(rc[:2]) + 2000
                    if year > rocnik:
                        year -= 100
                    month = int(rc[2:4]) % 50
                    day = int(rc[4:6])
                    datumNarozeni = datetime(year, month, day)

                osoba.druhRoleVRizenid = druhRoleVRizeni
                osoba.nazevOsoby=nazevOsoby
                osoba.nazevOsobyObchodni=nazevOsobyObchodni
                osoba.jmeno=jmeno
                osoba.titulPred=titulPred
                osoba.titulZa=titulZa
                osoba.ic=ic
                osoba.dic=dic
                osoba.rc=rc
                osoba.datumNarozeni=datumNarozeni

                osoba.save()
                vec.osoby.add(osoba)

                if t_osoba.datumosobavevecizrusena:
                    vec.osoby.remove(osoba)
                else:
                    t_adresa = t_udalost.adresa

                    if t_adresa:
                        druhAdresy = DruhAdresy.objects.get_or_create(
                            desc=t_adresa.druhadresy.string.strip())[0]
                        if t_adresa.mesto:
                            mesto = normalize(t_osoba.mesto.string)
                        else:
                            mesto = None
                        if t_adresa.ulice:
                            ulice = normalize(t_osoba.ulice.string)
                        else:
                            ulice = None
                        if t_adresa.cislopopisne:
                            cisloPopisne = \
                                normalize(t_osoba.cislopopisne.string)
                        else:
                            cisloPopisne = None
                        if t_adresa.okres:
                            okres = normalize(t_osoba.okres.string)
                        else:
                            okres = None
                        if t_adresa.zeme:
                            zeme = normalize(t_osoba.zeme.string)
                        else:
                            zeme = None
                        if t_adresa.psc:
                            psc = t_osoba.psc.string \
                                .replace(' ', '').replace('/', '')[:5]
                        else:
                            psc = None
                        if t_adresa.telefon:
                            telefon = normalize(t_osoba.telefon.string)
                        else:
                            telefon = None
                        if t_adresa.fax:
                            fax = normalize(t_osoba.fax.string)
                        else:
                            fax = None
                        if t_adresa.textadresy:
                            textAdresy = normalize(t_osoba.textadresy.string)
                        else:
                            textAdresy = None

                        adresa, c_adresa = Adresa.objects.get_or_create(
                            druhAdresy=druhAdresy,
                            mesto=mesto,
                            ulice=ulice,
                            cisloPopisne=cisloPopisne,
                            okres=okres,
                            zeme=zeme,
                            psc=psc,
                            telefon=telefon,
                            fax=fax,
                            textAdresy=textAdresy)

                        osoba.adresy.add(adresa)

                        if t_adresa.datumpobytdo:
                            osoba.adresy.remove(adresa)
        except:
            print('Error, id =', id)

    Counter.objects.update_or_create(id='DL', defaults={'number': id})

def cron_deltr():
    Transaction.objects.all().delete()

def cron_getws2():
    id = Counter.objects.get(id='PR').number

    for vec in Vec.objects.filter(id__gt=id, link__isnull=True).order_by('id'):
        soup = BeautifulSoup('', 'lxml')
        soup.is_xml = True

        envelope = soup.handle_starttag(
            'Envelope', None,
            'soapenv', {
                'xmlns:soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xmlns:typ': 'http://isirws.cca.cz/types/'})
        header = soup.new_tag('Header', None, 'soapenv')
        envelope.append(header)
        body = soup.new_tag('Body', None, 'soapenv')
        envelope.append(body)
        req = soup.new_tag('getIsirWsCuzkDataRequest', None, 'typ')
        body.append(req)
        bcVec = soup.new_tag('bcVec', None, None)
        bcVec.append(str(vec.bc))
        req.append(bcVec)
        rocnik = soup.new_tag('rocnik', None, None)
        rocnik.append(str(vec.rocnik))
        req.append(rocnik)
        

        url = 'https://isir.justice.cz:8443/isir_cuzk_ws/IsirWsCuzkService'

        headers = {
            'content-type': 'text/xml; charset=utf-8',
            'SOAPAction': '"http://isirws.cca.cz/types/"',
        }

        res = post(url, soup.renderContents(), headers=headers)

        xml = res.content

        subsoup = BeautifulSoup(xml, 'xml')
        subsoup.is_xml = True

        if subsoup.pocetVysledku and \
           subsoup.cisloSenatu and \
           subsoup.urlDetailRizeni and \
           (subsoup.nazevOrganizace.string.strip()[:PREF] == \
            l2n[vec.idOsobyPuvodce][:PREF]):
            Vec.objects.filter(id=vec.id).update(
                senat=int(subsoup.cisloSenatu.string),
                link=subsoup.urlDetailRizeni.string.strip())

        id = vec.id

    Counter.objects.update_or_create(id='PR', defaults={'number': id})

def cron_delerr():
    Vec.objects \
       .filter(druhStavRizeni=DruhStavRizeni.objects.get(desc='MYLNÝ ZÁP.')) \
       .delete()

def cron_update():
    cron_getws2()
    cron_gettr()
    cron_proctr()
    cron_deltr()
    cron_delerr()

def sir_notice(uid):
    text = ''
    tt = Tracked.objects.filter(uid=uid, vec__link__isnull=False) \
        .order_by('desc', 'id').distinct()
    if tt:
        text = 'Došlo ke změně v těchto insolvenčních řízeních, ' \
               'která sledujete:\n\n'
        for t in tt:
            text += ' - %s, sp. zn. %s %d INS %d/%d\n' % \
                    (t.desc,
                     l2s[t.vec.idOsobyPuvodce],
                     t.vec.senat,
                     t.vec.bc,
                     t.vec.rocnik)
            text += '   %s\n\n' % t.vec.link
        Tracked.objects.filter(uid=uid, vec__link__isnull=False).delete()
    return text
