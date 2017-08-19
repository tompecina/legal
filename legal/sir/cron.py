# -*- coding: utf-8 -*-
#
# sir/cron.py
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

from datetime import datetime

from bs4 import BeautifulSoup
from django.contrib.auth.models import User

from legal.common.utils import normalize, post, LOGGER
from legal.dir.cron import dir_check
from legal.sir.glob import L2N, L2S, SELIST, BELIST
from legal.sir.models import (
    DruhStavRizeni, Vec, DruhRoleVRizeni, Osoba, Role, DruhAdresy, Adresa, Counter, Transaction, Insolvency, Tracked)


PREF = 20


def convdt(string):

    return datetime.strptime(string.string[:19], "%Y-%m-%dT%H:%M:%S")


def convd(string):

    return datetime.strptime(string.string[:10], "%Y-%m-%d")


def cron_gettr():

    idx = Counter.objects.get(id='DL').number
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
        idPodnetu.append(str(idx))
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

        if not (soup.stav and soup.stav.string == 'OK' and soup.find('data')):
            break

        lst = []
        for t_data in soup.find_all('data'):
            idx = int(t_data.id.string)
            lst.append(Transaction(
                id=idx,
                datumZalozeniUdalosti=convdt(t_data.datumzalozeniudalosti),
                datumZverejneniUdalosti=convdt(t_data.datumzverejneniudalosti),
                dokumentUrl=(t_data.dokumenturl.string.strip() if t_data.dokumenturl else None),
                spisovaZnacka=t_data.spisovaznacka.string.strip(),
                typUdalosti=t_data.typudalosti.string.strip(),
                popisUdalosti=t_data.popisudalosti.string.strip(),
                oddil=(t_data.oddil.string.strip() if t_data.oddil else None),
                cisloVOddilu=(int(t_data.cislovoddilu.string) if t_data.cislovoddilu else None),
                poznamkaText=(t_data.poznamka.string.strip() if t_data.poznamka else None),
                error=False))

        Transaction.objects.bulk_create(lst)
        LOGGER.debug('Read {:d} transaction(s)'.format(len(lst)))


def p2s(ins):

    return 'INS {0.number:d}/{0.year:d}'.format(ins)


def cron_proctr():

    idx = Counter.objects.get(id='DL').number
    debtor = DruhRoleVRizeni.objects.get_or_create(desc='DLUŽNÍK')[0]
    for trans in Transaction.objects.filter(error=False).order_by('id'):
        idx = trans.id
        try:
            bc, rocnik = map(int, trans.spisovaZnacka.split()[-1].split('/'))
            if bc <= 0 or rocnik <= 0:
                continue
            datumZalozeniUdalosti = trans.datumZalozeniUdalosti

            poznamkaText = trans.poznamkaText.strip()
            subsoup = BeautifulSoup(poznamkaText, 'lxml')
            subsoup.is_xml = True

            t_udalost = subsoup.find('ns2:udalost')
            t_vec = t_udalost.vec
            t_osoba = t_udalost.osoba

            idOsobyPuvodce = t_udalost.idosobypuvodce.string.strip()
            druhStavRizeni = None
            if t_vec:
                if t_vec.druhstavrizeni:
                    druhStavRizeni = DruhStavRizeni.objects.get_or_create(desc=t_vec.druhstavrizeni.string.strip())[0]

            vec = Vec.objects.get_or_create(
                idOsobyPuvodce=idOsobyPuvodce,
                bc=bc,
                rocnik=rocnik,
                defaults={
                    'firstAction': datumZalozeniUdalosti.date(),
                    'lastAction': datumZalozeniUdalosti.date()})[0]

            if druhStavRizeni:
                vec.druhStavRizeni = druhStavRizeni

            if t_udalost.datumvyskrtnuti:
                vec.datumVyskrtnuti = convd(t_udalost.datumvyskrtnuti)
            elif not vec.lastAction or datumZalozeniUdalosti.date() > vec.lastAction:
                vec.lastAction = datumZalozeniUdalosti.date()

            vec.save()

            if trans.oddil and trans.typUdalosti:
                typUdalosti = int(trans.typUdalosti)
                if typUdalosti not in SELIST:
                    for ins in Insolvency.objects.filter(number=bc, year=rocnik):
                        if ins.detailed or typUdalosti in BELIST:
                            if Tracked.objects.get_or_create(
                                    uid_id=ins.uid_id,
                                    desc=ins.desc,
                                    vec=vec)[1]:
                                LOGGER.info(
                                    'Change detected in proceedings "{}" ({}) for user "{}" ({:d})'
                                    .format(
                                        ins.desc,
                                        p2s(ins),
                                        User.objects.get(pk=ins.uid_id).username,
                                        ins.uid_id))

            if t_osoba:
                idOsoby = t_osoba.idosoby.string.strip()
                druhRoleVRizeni = DruhRoleVRizeni.objects.get_or_create(desc=t_osoba.druhrolevrizeni.string.strip())[0]
                nazevOsoby = normalize(t_osoba.nazevosoby.string)
                osoba = Osoba.objects.get_or_create(
                    idOsobyPuvodce=idOsobyPuvodce,
                    idOsoby=idOsoby,
                    defaults={
                        'nazevOsoby': nazevOsoby})[0]
                role = Role.objects.get_or_create(
                    osoba=osoba,
                    druhRoleVRizeni=druhRoleVRizeni)[0]
                if t_osoba.nazevosobyobchodni:
                    nazevOsobyObchodni = normalize(t_osoba.nazevosobyobchodni.string)
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
                if not datumNarozeni and rc:
                    year = int(rc[:2]) + 2000
                    if year > rocnik:
                        year -= 100
                    month = int(rc[2:4]) % 50
                    day = int(rc[4:6])
                    datumNarozeni = datetime(year, month, day)

                osoba.nazevOsoby = nazevOsoby
                osoba.nazevOsobyObchodni = nazevOsobyObchodni
                osoba.jmeno = jmeno
                osoba.titulPred = titulPred
                osoba.titulZa = titulZa
                osoba.ic = ic
                osoba.dic = dic
                osoba.rc = rc
                osoba.datumNarozeni = datumNarozeni

                osoba.save()
                if druhRoleVRizeni == debtor and role not in vec.roles.all():
                    dir_check(osoba, vec)
                vec.roles.add(role)

                if t_osoba.datumosobavevecizrusena:
                    vec.roles.remove(role)
                else:
                    t_adresa = t_udalost.adresa

                    if t_adresa:
                        druhAdresy = DruhAdresy.objects.get_or_create(
                            desc=t_adresa.druhadresy.string.strip())[0]
                        if t_adresa.mesto:
                            mesto = normalize(t_adresa.mesto.string)
                        else:
                            mesto = None
                        if t_adresa.ulice:
                            ulice = normalize(t_adresa.ulice.string)
                        else:
                            ulice = None
                        if t_adresa.cislopopisne:
                            cisloPopisne = normalize(t_adresa.cislopopisne.string)
                        else:
                            cisloPopisne = None
                        if t_adresa.okres:
                            okres = normalize(t_adresa.okres.string)
                        else:
                            okres = None
                        if t_adresa.zeme:
                            zeme = normalize(t_adresa.zeme.string)
                        else:
                            zeme = None
                        if t_adresa.psc:
                            psc = t_adresa.psc.string.replace(' ', '').replace('/', '')[:5]
                        else:
                            psc = None
                        if t_adresa.telefon:
                            telefon = normalize(t_adresa.telefon.string)
                        else:
                            telefon = None
                        if t_adresa.fax:
                            fax = normalize(t_adresa.fax.string)
                        else:
                            fax = None
                        if t_adresa.textadresy:
                            textAdresy = normalize(t_adresa.textadresy.string)
                        else:
                            textAdresy = None

                        adresa = Adresa.objects.get_or_create(
                            druhAdresy=druhAdresy,
                            mesto=mesto,
                            ulice=ulice,
                            cisloPopisne=cisloPopisne,
                            okres=okres,
                            zeme=zeme,
                            psc=psc,
                            telefon=telefon,
                            fax=fax,
                            textAdresy=textAdresy)[0]

                        osoba.adresy.add(adresa)

                        if t_adresa.datumpobytdo:
                            osoba.adresy.remove(adresa)
        except:
            trans.error = True
            trans.save()

    Counter.objects.update_or_create(id='DL', defaults={'number': idx})
    LOGGER.debug('Transactions processed')


def cron_deltr():

    Transaction.objects.filter(error=False).delete()
    LOGGER.debug('Transactions deleted')


def get_ws2(vec):

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

    return subsoup


def refresh_link(vec):

    try:
        subsoup = get_ws2(vec)
        Vec.objects.filter(id=vec.id).update(refreshed=datetime.now())

        if not subsoup.pocetVysledku:
            return 1

        link = subsoup.urlDetailRizeni.text
        if not link:
            return 2

        if vec.link != link:
            Vec.objects.filter(id=vec.id).update(link=link)
            return 3

        return 4

    except:
        return 0


REFRESH_BATCH = 10


def cron_refresh_links():

    batch = (
        Vec.objects.filter(datumVyskrtnuti__isnull=True, link__isnull=False)
        .order_by('refreshed', 'timestamp_add')[:REFRESH_BATCH])

    num = 0
    matrix = [0] * 5
    for vec in batch:
        matrix[refresh_link(vec)] += 1

    LOGGER.debug('Refreshed {:d} links(s), results: {}'.format(num, matrix))


def cron_getws2():

    idx = Counter.objects.get(id='PR').number

    for vec in Vec.objects.filter(id__gt=idx, link__isnull=True).order_by('id'):

        subsoup = get_ws2(vec)

        if (subsoup.pocetVysledku and subsoup.cisloSenatu and subsoup.urlDetailRizeni
            and (subsoup.nazevOrganizace.string.strip()[:PREF] == L2N[vec.idOsobyPuvodce][:PREF])):
            Vec.objects.filter(id=vec.id).update(
                senat=int(subsoup.cisloSenatu.string),
                link=subsoup.urlDetailRizeni.string.strip())

        idx = vec.id

    Counter.objects.update_or_create(id='PR', defaults={'number': idx})
    LOGGER.debug('WS2 information added')


def cron_delerr():

    Vec.objects.filter(druhStavRizeni=DruhStavRizeni.objects.get(desc='MYLNÝ ZÁP.')).delete()
    LOGGER.debug('Erroneous proceedings deleted')


def cron_update():

    cron_getws2()
    cron_gettr()
    cron_proctr()
    cron_deltr()
    cron_delerr()
    LOGGER.info('Batch processed')


def sir_notice(uid):

    text = ''
    res = Tracked.objects.filter(uid=uid, vec__link__isnull=False).order_by('desc', 'id').distinct()
    if res:
        text = 'Došlo ke změně v těchto insolvenčních řízeních, která sledujete:\n\n'
        for ins in res:
            text += (
                ' - {0}sp. zn. {1} {2.senat:d} INS {2.bc:d}/{2.rocnik:d}\n'
                .format('{}, '.format(ins.desc) if ins.desc else '', L2S[ins.vec.idOsobyPuvodce], ins.vec))
            text += '   {}\n\n'.format(ins.vec.link)
        Tracked.objects.filter(uid=uid, vec__link__isnull=False).delete()
        LOGGER.info('Non-empty notice prepared for user "{}" ({:d})'.format(User.objects.get(pk=uid).username, uid))
    return text
