# -*- coding: utf-8 -*-
#
# pir/views.py
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

from datetime import datetime
from csv import writer as csvwriter
from json import dump

from django.shortcuts import get_object_or_404, redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.gzip import gzip_page
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404

from legal.common.glob import NULL_REGISTERS, INERR, TEXT_OPTS_KEYS, EXLIM_TITLE, LOCAL_SUBDOMAIN, LOCAL_URL, DTF
from legal.common.utils import Pager, new_xml, xml_decorate, LOGGER, render
from legal.sir.glob import L2N, L2S, L2R, S2D, R2I, A2D
from legal.sir.models import Vec, Osoba, DruhRoleVRizeni, Counter
from legal.pir.forms import MainForm


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

EXLIM = 1000


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    page_title = apps.get_app_config(APP).verbose_name

    if request.method == 'GET':
        form = MainForm()
        return render(
            request,
            'pir_mainpage.xhtml',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'form': form})
    form = MainForm(request.POST)
    if form.is_valid():
        cld = form.cleaned_data
        for key in ('name', 'first_name', 'city'):
            if not cld[key]:
                del cld[key + '_opt']
        cld['birthid'] = cld['birthid'].replace('/', '')
        query = QueryDict(mutable=True)
        for key in cld:
            if cld[key]:
                query[key] = cld[key]
        for key in ('role_debtor', 'role_trustee', 'role_creditor', 'deleted', 'creditors'):
            if cld[key]:
                query[key] = 'on'
        query['start'] = 0
        del query['format']
        return redirect('{}?{}'.format(
            reverse('{}:{}list'.format(APP, cld['format'])),
            query.urlencode()))
    LOGGER.debug('Invalid form', request)
    err_message = INERR
    return render(
        request,
        'pir_mainpage.xhtml',
        {'app': APP,
         'page_title': page_title,
         'err_message': err_message,
         'form': form})


def g2p(reqd):

    par = {'id__lte': Counter.objects.get(id='PR').number}
    if 'court' in reqd:
        par['idOsobyPuvodce'] = reqd['court']

    lims = {
        'senate': ('senat', 0),
        'number': ('bc', 1),
        'year': ('rocnik', 2008),
    }
    for fld in lims:
        if fld in reqd:
            par[lims[fld][0]] = npar = int(reqd[fld])
            assert npar >= lims[fld][1]

    if 'date_first_from' in reqd:
        par['firstAction__gte'] = datetime.strptime(reqd['date_first_from'], DTF).date()
    if 'date_first_to' in reqd:
        par['firstAction__lte'] = datetime.strptime(reqd['date_first_to'], DTF).date()
    if 'date_last_from' in reqd:
        par['lastAction__gte'] = datetime.strptime(reqd['date_last_from'], DTF).date()
    if 'date_last_to' in reqd:
        par['lastAction__lte'] = datetime.strptime(reqd['date_last_to'], DTF).date()
    if 'name_opt' in reqd:
        assert reqd['name_opt'] in TEXT_OPTS_KEYS
    if 'name' in reqd:
        assert 'name_opt' in reqd
        par['roles__osoba__nazevOsoby__' + reqd['name_opt']] = reqd['name']
    if 'first_name_opt' in reqd:
        assert reqd['first_name_opt'] in TEXT_OPTS_KEYS
    if 'first_name' in reqd:
        assert 'first_name_opt' in reqd
        par['roles__osoba__jmeno__' + reqd['first_name_opt']] = reqd['first_name']
    if 'city_opt' in reqd:
        assert reqd['city_opt'] in TEXT_OPTS_KEYS
    if 'city' in reqd:
        assert 'city_opt' in reqd
        par['roles__osoba__adresy__mesto__' + reqd['city_opt']] = reqd['city']
    for fld, key in (('genid', 'ic'), ('taxid', 'dic'), ('birthid', 'rc')):
        if fld in reqd:
            par['roles__osoba__' + key] = reqd[fld]
    if 'date_birth' in reqd:
        par['roles__osoba__datumNarozeni'] = datetime.strptime(reqd['date_birth'], DTF).date()
    if 'year_birth_from' in reqd:
        par['roles__osoba__datumNarozeni__year__gte'] = reqd['year_birth_from']
    if 'year_birth_to' in reqd:
        par['roles__osoba__datumNarozeni__year__lte'] = reqd['year_birth_to']
    if ('name' in reqd or 'first_name' in reqd or 'city' in reqd or 'genid' in reqd or 'taxid' in reqd
        or 'birthid' in reqd or 'date_birth' in reqd or 'year_birth_from' in reqd or 'year_birth_to' in reqd):
        role = [DruhRoleVRizeni.objects.get(desc=R2I[f]).id for f in ('debtor', 'trustee', 'creditor')
            if 'role_' + f in reqd]
        if 'role_creditor' in reqd:
            role.append(DruhRoleVRizeni.objects.get(desc=R2I['motioner']).id)
        par['roles__druhRoleVRizeni__in'] = role
    if 'deleted' not in reqd:
        par['datumVyskrtnuti__isnull'] = True
    return par


def o2s(osoba, detailed=False):

    res = ' '.join(filter(bool, (osoba.titulPred, osoba.jmeno, osoba.nazevOsoby)))
    res = ', '.join(filter(bool, (res, osoba.titulZa, osoba.nazevOsobyObchodni)))
    if detailed:
        if osoba.datumNarozeni:
            res += ', nar.&#160;{:%d.%m.%Y}'.format(osoba.datumNarozeni)
        elif osoba.ic:
            res += ', IČO:&#160;{}'.format(osoba.ic)
    return res


def getosoby(vec, *desc):

    roles = [DruhRoleVRizeni.objects.get(desc=R2I[x]).id for x in desc]
    lst = vec.roles.filter(druhRoleVRizeni__in=roles).values_list('osoba', flat=True)
    return Osoba.objects.filter(id__in=lst).order_by('nazevOsoby', 'jmeno', 'id')


@require_http_methods(('GET',))
def htmllist(request):

    LOGGER.debug('HTML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        start = int(reqd['start']) if 'start' in reqd else 0
        assert start >= 0
        res = Vec.objects.filter(**par).order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    except:
        raise Http404
    total = res.count()
    if total and start >= total:
        start = total - 1
    creditors = 'creditors' in reqd
    batch = 10 if creditors else 20
    rows = res[start:start + batch]
    for row in rows:
        row.court = L2N[row.idOsobyPuvodce]
        row.court_short = L2S[row.idOsobyPuvodce]
        row.court_reg = L2R[row.idOsobyPuvodce]
        row.state = S2D[row.druhStavRizeni.desc] if row.druhStavRizeni else '(není známo)'
        row.debtors = []
        for osoba in getosoby(row, 'debtor'):
            row.debtors.append({
                'text': o2s(osoba, detailed=True),
                'id': osoba.id})
        row.trustees = []
        for osoba in getosoby(row, 'trustee'):
            row.trustees.append({
                'text': o2s(osoba),
                'id': osoba.id})
        if creditors:
            row.creditors = []
            for osoba in getosoby(row, 'motioner', 'creditor'):
                row.creditors.append({'text': o2s(osoba), 'id': osoba.id})
    return render(
        request,
        'pir_list.xhtml',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': rows,
         'creditors': creditors,
         'pager': Pager(start, total, reverse('pir:htmllist'), reqd, batch),
         'total': total,
         'NULL_REGISTERS': NULL_REGISTERS})


def xml_addparties(osoby, xml, tag, tagname):

    for osoba in osoby:
        subtag = xml.new_tag(tagname)
        tag.append(subtag)
        tag_name = xml.new_tag('name')
        tag_name.append(osoba.nazevOsoby)
        subtag.append(tag_name)
        if osoba.nazevOsobyObchodni:
            tag_business_name = xml.new_tag('business_name')
            tag_business_name.append(osoba.nazevOsobyObchodni)
            subtag.append(tag_business_name)
        if osoba.jmeno:
            tag_first_name = xml.new_tag('first_name')
            tag_first_name.append(osoba.jmeno)
            subtag.append(tag_first_name)
        if osoba.titulPred:
            tag_honorifics_prepended = xml.new_tag('honorifics_prepended')
            tag_honorifics_prepended.append(osoba.titulPred)
            subtag.append(tag_honorifics_prepended)
        if osoba.titulZa:
            tag_honorifics_appended = xml.new_tag('honorifics_appended')
            tag_honorifics_appended.append(osoba.titulZa)
            subtag.append(tag_honorifics_appended)
        if osoba.ic:
            tag_gen_id = xml.new_tag('gen_id')
            tag_gen_id.append(osoba.ic)
            subtag.append(tag_gen_id)
        if osoba.dic:
            tag_tax_id = xml.new_tag('tax_id')
            tag_tax_id.append(osoba.dic)
            subtag.append(tag_tax_id)
        if osoba.datumNarozeni:
            tag_birth_date = xml.new_tag('birth_date')
            tag_birth_date.append(osoba.datumNarozeni.isoformat())
            subtag.append(tag_birth_date)
        if osoba.rc:
            tag_birth_id = xml.new_tag('birth_id')
            tag_birth_id.append('{}/{}'.format(osoba.rc[:6], osoba.rc[6:]))
            subtag.append(tag_birth_id)
        tag_addresses = xml.new_tag('addresses')
        for adresa in osoba.adresy.all():
            tag_address = xml.new_tag('address')
            tag_addresses.append(tag_address)
            tag_address['type'] = A2D[adresa.druhAdresy.desc]
            if adresa.mesto:
                tag_city = xml.new_tag('city')
                tag_city.append(adresa.mesto)
                tag_address.append(tag_city)
            if adresa.ulice:
                tag_street = xml.new_tag('street')
                tag_street.append(adresa.ulice)
                tag_address.append(tag_street)
            if adresa.cisloPopisne:
                tag_street_number = xml.new_tag('street_number')
                tag_street_number.append(adresa.cisloPopisne)
                tag_address.append(tag_street_number)
            if adresa.okres:
                tag_district = xml.new_tag('district')
                tag_district.append(adresa.okres)
                tag_address.append(tag_district)
            if adresa.zeme:
                tag_country = xml.new_tag('country')
                tag_country.append(adresa.zeme)
                tag_address.append(tag_country)
            if adresa.psc:
                tag_zip = xml.new_tag('zip')
                tag_zip.append('{} {}'.format(adresa.psc[:3], adresa.psc[3:]))
                tag_address.append(tag_zip)
            if adresa.telefon:
                tag_phone = xml.new_tag('phone')
                tag_phone.append(adresa.telefon)
                tag_address.append(tag_phone)
            if adresa.fax:
                tag_fax = xml.new_tag('fax')
                tag_fax.append(adresa.fax)
                tag_address.append(tag_fax)
            if adresa.textAdresy:
                tag_email = xml.new_tag('email')
                tag_email.append(adresa.textAdresy)
                tag_address.append(tag_email)
        subtag.append(tag_addresses)


@gzip_page
@require_http_methods(('GET',))
def xmllist(request):

    LOGGER.debug('XML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Vec.objects.filter(**par).order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    dec = {
        'insolvencies': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'.format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = new_xml('')
    tag_insolvencies = xml_decorate(xml.new_tag('insolvencies'), dec)
    xml.append(tag_insolvencies)
    for item in res:
        tag_insolvency = xml.new_tag('insolvency')
        tag_insolvencies.append(tag_insolvency)
        tag_court = xml.new_tag('court')
        tag_insolvency.append(tag_court)
        tag_court['id'] = item.idOsobyPuvodce
        tag_court.append(L2N[item.idOsobyPuvodce])
        tag_ref = xml.new_tag('ref')
        tag_insolvency.append(tag_ref)
        tag_court = xml.new_tag('court')
        tag_court.append(L2S[item.idOsobyPuvodce])
        tag_ref.append(tag_court)
        tag_senate = xml.new_tag('senate')
        tag_senate.append(str(item.senat))
        tag_ref.append(tag_senate)
        tag_register = xml.new_tag('register')
        tag_register.append('INS')
        tag_ref.append(tag_register)
        tag_number = xml.new_tag('number')
        tag_number.append(str(item.bc))
        tag_ref.append(tag_number)
        tag_year = xml.new_tag('year')
        tag_year.append(str(item.rocnik))
        tag_ref.append(tag_year)
        if item.druhStavRizeni:
            tag_state = xml.new_tag('state')
            tag_state.append(S2D[item.druhStavRizeni.desc])
            tag_insolvency.append(tag_state)
        tag_debtors = xml.new_tag('debtors')
        tag_insolvency.append(tag_debtors)
        xml_addparties(getosoby(item, 'debtor'), xml, tag_debtors, 'debtor')
        tag_trustees = xml.new_tag('trustees')
        tag_insolvency.append(tag_trustees)
        xml_addparties(getosoby(item, 'trustee'), xml, tag_trustees, 'trustee')
        if 'creditors' in reqd:
            tag_creditors = xml.new_tag('creditors')
            tag_insolvency.append(tag_creditors)
            xml_addparties(getosoby(item, 'motioner', 'creditor'), xml, tag_creditors, 'creditor')
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Insolvence.xml'
    return response


@gzip_page
@require_http_methods(('GET',))
def csvlist(request):

    LOGGER.debug('CSV list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Vec.objects.filter(**par).order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Insolvence.csv'
    writer = csvwriter(response)
    hdr = (
        'Soud',
        'Spisová značka',
        'Stav řízení',
    )
    writer.writerow(hdr)
    for item in res:
        dat = (
            L2N[item.idOsobyPuvodce],
            '{}{} INS {:d}/{:d}'.format(
                L2S[item.idOsobyPuvodce],
                ' {:d}'.format(item.senat) if item.senat else '',
                item.bc,
                item.rocnik),
            (S2D[item.druhStavRizeni.desc]
             if item.druhStavRizeni else '(není známo)'),
        )
        writer.writerow(dat)
    return response


def json_addparties(osoby):

    res = []
    for osoba in osoby:
        item = {'name': osoba.nazevOsoby}
        if osoba.nazevOsobyObchodni:
            item['business_name'] = osoba.nazevOsobyObchodni
        if osoba.jmeno:
            item['first_name'] = osoba.jmeno
        if osoba.titulPred:
            item['honorifics_prepended'] = osoba.titulPred
        if osoba.titulZa:
            item['honorifics_appended'] = osoba.titulZa
        if osoba.ic:
            item['gen_id'] = osoba.ic
        if osoba.dic:
            item['tax_id'] = osoba.dic
        if osoba.datumNarozeni:
            item['birth_date'] = osoba.datumNarozeni.isoformat()
        if osoba.rc:
            item['birth_id'] = '{}/{}'.format(osoba.rc[:6], osoba.rc[6:])
        subres = []
        for adresa in osoba.adresy.all():
            addr = {'type': A2D[adresa.druhAdresy.desc]}
            if adresa.mesto:
                addr['city'] = adresa.mesto
            if adresa.ulice:
                addr['street'] = adresa.ulice
            if adresa.cisloPopisne:
                addr['street_number'] = adresa.cisloPopisne
            if adresa.okres:
                addr['district'] = adresa.okres
            if adresa.zeme:
                addr['country'] = adresa.zeme
            if adresa.psc:
                addr['zip'] = '{} {}'.format(adresa.psc[:3], adresa.psc[3:])
            if adresa.telefon:
                addr['phone'] = adresa.telefon
            if adresa.fax:
                addr['fax'] = adresa.fax
            if adresa.textAdresy:
                addr['email'] = adresa.textAdresy
            subres.append(addr)
        item['addresses'] = subres
        res.append(item)
    return res


@gzip_page
@require_http_methods(('GET',))
def jsonlist(request):

    LOGGER.debug('JSON list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Vec.objects.filter(**par).order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Insolvence.json'
    lst = []
    for item in res:
        par = {
            'court': L2N[item.idOsobyPuvodce],
            'ref': {
                'court': L2S[item.idOsobyPuvodce],
                'senate': item.senat,
                'register': 'INS',
                'number': item.bc,
                'year': item.rocnik,
                },
            'state': S2D[item.druhStavRizeni.desc]
            if item.druhStavRizeni else '',
            'debtors': json_addparties(getosoby(item, 'debtor')),
            'trustees': json_addparties(getosoby(item, 'trustee')),
        }
        if 'creditors' in reqd:
            par['creditors'] = json_addparties(getosoby(item, 'motioner', 'creditor'))
        lst.append(par)
    dump(lst, response)
    return response


@require_http_methods(('GET',))
def party(request, idx=0):

    LOGGER.debug('Party information page accessed, id={}'.format(idx), request)
    osoba = get_object_or_404(Osoba, id=idx)
    adresy = osoba.adresy.order_by('-id')
    num = 0
    for adresa in adresy:
        adresa.type = A2D[adresa.druhAdresy.desc]
        adresa.psc = '{} {}'.format(adresa.psc[:3], adresa.psc[3:]) if adresa.psc else ''
        adresa.cl = 'even' if num % 2 else 'odd'
        num += 1
    return render(
        request,
        'pir_party.xhtml',
        {'app': APP,
         'page_title': 'Informace o osobě',
         'subtitle': o2s(osoba),
         'osoba': osoba,
         'birthid': '{}/{}'.format(osoba.rc[:6], osoba.rc[6:]) if osoba.rc else '',
         'adresy': adresy})
