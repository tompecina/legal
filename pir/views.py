# -*- coding: utf-8 -*-
#
# pir/views.py
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

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404
from datetime import datetime
from locale import strxfrm
from csv import writer as csvwriter
from json import dump
from common.utils import between, Pager, newXML, xmldecorate
from common.glob import (
    inerr, text_opts, text_opts_keys, localsubdomain, localurl, DTF)
from sir.glob import l2n, l2s, l2r, s2d, r2i, r2d, a2d
from sir.models import Vec, Osoba, DruhRoleVRizeni, Counter
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

EXLIM = 1000

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    err_message = ''
    messages = []
    page_title = apps.get_app_config(APP).verbose_name

    courts = sorted([{'id': x, 'name': l2n[x]} for x in \
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()], \
        key=(lambda x: strxfrm(x['name'])))
    if request.method == 'GET':
        f = MainForm()
        return render(
            request,
            'pir_mainpage.html',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'courts': courts,
             'f': f})
    else:
        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            for n in ['name', 'first_name', 'city']:
                if not cd[n]:
                    del cd[n + '_opt']
            q = QueryDict(mutable=True)
            for p in cd:
                if cd[p]:
                    q[p] = cd[p]
            for p in \
                ['role_debtor',
                 'role_trustee',
                 'role_creditor',
                 'deleted',
                 'creditors']:
                if cd[p]:
                    q[p] = 'on'
            q['start'] = 0
            del q['format']
            return redirect(reverse('pir:' + cd['format'] + 'list') + \
                '?' + q.urlencode())
        else:
            err_message = inerr
            return render(
                request,
                'pir_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'courts': courts,
                 'f': f})

def g2p(rd):
    p = {'id__lte': Counter.objects.get(id='PR').number}
    if 'court' in rd:
        p['idOsobyPuvodce'] = rd['court']
    for f, d, l in \
        [['senate', 'senat', 0], ['number', 'bc', 1], ['year', 'rocnik', 1990]]:
        if f in rd:
            p[d] = int(rd[f])
            assert p[d] >= l
    if 'date_first_from' in rd:
        p['firstAction__gte'] = \
            datetime.strptime(rd['date_first_from'], DTF).date()
    if 'date_first_to' in rd:
        p['firstAction__lte'] = \
            datetime.strptime(rd['date_first_from'], DTF).date()
    if 'date_last_from' in rd:
        p['lastAction__gte'] = \
            datetime.strptime(rd['date_last_from'], DTF).date()
    if 'date_last_to' in rd:
        p['lastAction__lte'] = \
            datetime.strptime(rd['date_last_from'], DTF).date()
    if 'name_opt' in rd:
        assert rd['name_opt'] in text_opts_keys
    if 'name' in rd:
        assert 'name_opt' in rd
        p['osoby__nazevOsoby__' + rd['name_opt']] = rd['name']
    if 'first_name_opt' in rd:
        assert rd['first_name_opt'] in text_opts_keys
    if 'first_name' in rd:
        assert 'first_name_opt' in rd
        p['osoby__jmeno__' + rd['first_name_opt']] = rd['first_name']
    if 'city_opt' in rd:
        assert rd['city_opt'] in text_opts_keys
    if 'city' in rd:
        assert 'city_opt' in rd
        p['osoby__adresy__mesto__' + rd['city_opt']] = rd['city']
    for f, m in [['genid', 'ic'], ['taxid', 'dic'], ['birthid', 'rc']]:
        if f in rd:
            p['osoby__' + m] = rd[f]
    if 'date_birth' in rd:
        p['osoby__datumNarozeni'] = \
            datetime.strptime(rd['date_birth'], DTF).date()
    if 'year_birth_from' in rd:
        p['osoby__datumNarozeni__year__gte'] = rd['year_birth_from']
    if 'year_birth_to' in rd:
        p['osoby__datumNarozeni__year__lte'] = rd['year_birth_to']
    if ('name' in rd) or \
       ('first_name' in rd) or \
       ('city' in rd) or \
       ('genid' in rd) or \
       ('taxid' in rd) or \
       ('birthid' in rd) or \
       ('date_birth' in rd) or \
       ('year_birth_from' in rd) or ('year_birth_to' in rd):
        role = [DruhRoleVRizeni.objects.get(desc=r2i[f]).id \
                for f in ['debtor', 'trustee', 'creditor'] \
                if ('role_' + f) in rd]
        if 'role_creditor' in rd:
            role.append(DruhRoleVRizeni.objects.get(desc=r2i['motioner']))
        if role:
            p['osoby__druhRoleVRizeni__in'] = role
    if 'deleted' not in rd:
        p['datumVyskrtnuti__isnull'] = True
    return p

def join(delim, *args):
    return delim.join([x for x in args if x])
    
def o2s(o, detailed=False):
    r = join(' ', o.titulPred, o.jmeno, o.nazevOsoby)
    r = join(', ', r, o.titulZa, o.nazevOsobyObchodni)
    if detailed:
        if o.datumNarozeni:
            r += ', nar.&nbsp;' + o.datumNarozeni.strftime('%d.%m.%Y')
        elif o.ic:
            r += ', IČO:&nbsp;' + o.ic
    return r
        
@require_http_methods(['GET'])
def htmllist(request):
    page_title = apps.get_app_config(APP).verbose_name
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        start = int(rd['start']) if ('start' in rd) else 0
        assert start >= 0
    except:
        raise Http404
    v = Vec.objects.filter(**p) \
        .order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    total = v.count()
    if (start >= total) and (total > 0):
        start = total - 1
    creditors = ('creditors' in rd)
    BATCH = (10 if creditors else 20)
    rows = v[start:(start + BATCH)]
    for row in rows:
        row.court = l2n[row.idOsobyPuvodce]
        row.court_short = l2s[row.idOsobyPuvodce]
        row.court_reg = l2r[row.idOsobyPuvodce]
        if row.druhStavRizeni:
            row.state = s2d[row.druhStavRizeni.desc]
        else:
            row.state = '(není známo)'
        row.debtors = []
        for osoba in row.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
            .objects.get(desc=r2i['debtor'])) \
            .order_by('nazevOsoby', 'jmeno', 'id'):
            row.debtors.append({
                'text': o2s(osoba, detailed=True),
                'id': osoba.id})
        row.trustees = []
        for osoba in row.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
            .objects.get(desc=r2i['trustee'])) \
            .order_by('nazevOsoby', 'jmeno', 'id'):
            row.trustees.append({
                'text': o2s(osoba),
                'id': osoba.id})
        if creditors:
            row.creditors = []
            for osoba in row.osoby.filter(druhRoleVRizeni__in=[DruhRoleVRizeni \
                .objects.get(desc=r2i['motioner']), \
                DruhRoleVRizeni.objects.get(desc=r2i['creditor'])]) \
                .order_by('nazevOsoby', 'jmeno', 'id'):
                row.creditors.append({'text': o2s(osoba), 'id': osoba.id})
    return render(
        request,
        'pir_list.html',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': rows,
         'creditors': creditors,
         'pager': Pager(start, total, reverse('pir:htmllist'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
def party(request, id=0):
    osoba = get_object_or_404(Osoba, id=id)
    adresy = osoba.adresy.order_by('-id')
    i = 0
    for adresa in adresy:
        adresa.type = a2d[adresa.druhAdresy.desc]
        adresa.psc = ((adresa.psc[:3] + ' ' + adresa.psc[3:]) \
            if adresa.psc else '')
        adresa.cl = ['odd', 'even'][i % 2]
        i += 1
    return render(
        request,
        'pir_party.html',
        {'app': APP,
         'page_title': 'Informace o osobě',
         'subtitle': o2s(osoba),
         'osoba': osoba,
         'role': r2d[osoba.druhRoleVRizeni.desc],
         'birthid': ((osoba.rc[:6] + '/' + osoba.rc[6:]) if osoba.rc else ''),
         'adresy': adresy})

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
            tag_birth_id.append(osoba.rc[:6] + '/' + osoba.rc[6:])
            subtag.append(tag_birth_id)
        tag_addresses = xml.new_tag('addresses')
        for adresa in osoba.adresy.all():
            tag_address = xml.new_tag('address')
            tag_addresses.append(tag_address)
            tag_address['type'] = a2d[adresa.druhAdresy.desc]
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
                tag_zip.append(adresa.psc[:3] + ' ' + adresa.psc[3:])
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

@require_http_methods(['GET'])
def xmllist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    vv = Vec.objects.filter(**p) \
        .order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    total = vv.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    xd = {
        'insolvencies': {
            'xmlns': 'http://' + localsubdomain,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': ('http://' + localsubdomain + ' ' + \
            localurl + '/static/%s-%s.xsd') % (APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = newXML('')
    tag_insolvencies = xmldecorate(xml.new_tag('insolvencies'), xd)
    xml.append(tag_insolvencies)
    for v in vv:
        tag_insolvency = xml.new_tag('insolvency')
        tag_insolvencies.append(tag_insolvency)
        tag_court = xml.new_tag('court')
        tag_insolvency.append(tag_court)
        tag_court['id'] = v.idOsobyPuvodce
        tag_court.append(l2n[v.idOsobyPuvodce])
        tag_ref = xml.new_tag('ref')
        tag_insolvency.append(tag_ref)
        tag_court = xml.new_tag('court')
        tag_court.append(l2s[v.idOsobyPuvodce])
        tag_ref.append(tag_court)
        tag_senate = xml.new_tag('senate')
        tag_senate.append(str(v.senat))
        tag_ref.append(tag_senate)
        tag_register = xml.new_tag('register')
        tag_register.append('INS')
        tag_ref.append(tag_register)
        tag_number = xml.new_tag('number')
        tag_number.append(str(v.bc))
        tag_ref.append(tag_number)
        tag_year = xml.new_tag('year')
        tag_year.append(str(v.rocnik))
        tag_ref.append(tag_year)
        if v.druhStavRizeni:
            tag_state = xml.new_tag('state')
            tag_state.append(s2d[v.druhStavRizeni.desc])
            tag_insolvency.append(tag_state)
        tag_debtors = xml.new_tag('debtors')
        tag_insolvency.append(tag_debtors)
        xml_addparties(
            v.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
                .objects.get(desc=r2i['debtor'])) \
                .order_by('nazevOsoby', 'jmeno', 'id'),
            xml,
            tag_debtors,
            'debtor')
        tag_trustees = xml.new_tag('trustees')
        tag_insolvency.append(tag_trustees)
        xml_addparties(
            v.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
                .objects.get(desc=r2i['trustee'])) \
                .order_by('nazevOsoby', 'jmeno', 'id'),
            xml,
            tag_trustees,
            'trustee')
        if 'creditors' in rd:
            tag_creditors = xml.new_tag('creditors')
            tag_insolvency.append(tag_creditors)
            xml_addparties(
                v.osoby.filter(druhRoleVRizeni__in=[DruhRoleVRizeni \
                    .objects.get(desc=r2i['motioner']), \
                    DruhRoleVRizeni.objects.get(desc=r2i['creditor'])]) \
                    .order_by('nazevOsoby', 'jmeno', 'id'),
                xml,
                tag_creditors,
                'creditor')
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = \
                'attachment; filename=Insolvence.xml'
    return response

@require_http_methods(['GET'])
def csvlist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    vv = Vec.objects.filter(**p) \
        .order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    total = vv.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Insolvence.csv'
    writer = csvwriter(response)
    hdr = [
        'Soud',
        'Spisová značka',
        'Stav řízení',
    ]
    writer.writerow(hdr)
    for v in vv:
        dat = [
            l2n[v.idOsobyPuvodce],
            '%s%s INS %d/%d' % (
                l2s[v.idOsobyPuvodce],
                ((' %d' % v.senat) if v.senat else ''), v.bc, v.rocnik),
            (s2d[v.druhStavRizeni.desc] if v.druhStavRizeni else ''),
        ]
        writer.writerow(dat)
    return response

def json_addparties(osoby):
    r = []
    for osoba in osoby:
        o = {'name': osoba.nazevOsoby}
        if osoba.nazevOsobyObchodni:
            o['business_name'] = osoba.nazevOsobyObchodni
        if osoba.jmeno:
            o['first_name'] = osoba.jmeno
        if osoba.titulPred:
            o['honorifics_prepended'] = osoba.titulPred
        if osoba.titulZa:
            o['honorifics_appended'] = osoba.titulZa
        if osoba.ic:
            o['gen_id'] = osoba.ic
        if osoba.dic:
            o['tax_id'] = osoba.dic
        if osoba.datumNarozeni:
            o['birth_date'] = osoba.datumNarozeni.isoformat()
        if osoba.rc:
            o['birth_id'] = (osoba.rc[:6] + '/' + osoba.rc[6:])
        aa = []
        for adresa in osoba.adresy.all():
            a = {'type': a2d[adresa.druhAdresy.desc]}
            if adresa.mesto:
                a['city'] = adresa.mesto
            if adresa.ulice:
                a['street'] = adresa.ulice
            if adresa.cisloPopisne:
                a['street_number'] = adresa.cisloPopisne
            if adresa.okres:
                a['district'] = adresa.okres
            if adresa.zeme:
                a['country'] = adresa.zeme
            if adresa.psc:
                a['zip'] = (adresa.psc[:3] + ' ' + adresa.psc[3:])
            if adresa.telefon:
                a['phone'] = adresa.telefon
            if adresa.fax:
                a['fax'] = adresa.fax
            if adresa.textAdresy:
                a['email'] = adresa.textAdresy
            aa.append(a)
        o['addresses'] = aa
        r.append(o)
    return r

@require_http_methods(['GET'])
def jsonlist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    vv = Vec.objects.filter(**p) \
        .order_by('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce').distinct()
    total = vv.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('pir:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Insolvence.json'
    r = []
    for v in vv:
        p = {
            'court': l2n[v.idOsobyPuvodce],
            'ref': {
                'court': l2s[v.idOsobyPuvodce],
                'senate': v.senat,
                'register': 'INS',
                'number': v.bc,
                'year': v.rocnik,
                },
            'state': (s2d[v.druhStavRizeni.desc] if v.druhStavRizeni else ''),
            'debtors': json_addparties(
                v.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
                    .objects.get(desc=r2i['debtor'])) \
                    .order_by('nazevOsoby', 'jmeno', 'id')),
            'trustees': json_addparties(
                v.osoby.filter(druhRoleVRizeni=DruhRoleVRizeni \
                    .objects.get(desc=r2i['trustee'])) \
                    .order_by('nazevOsoby', 'jmeno', 'id')),
        }
        if 'creditors' in rd:
            p['creditors'] = json_addparties(
                v.osoby.filter(druhRoleVRizeni__in=[DruhRoleVRizeni \
                    .objects.get(desc=r2i['motioner']), \
                    DruhRoleVRizeni.objects.get(desc=r2i['creditor'])]) \
                    .order_by('nazevOsoby', 'jmeno', 'id'))
        r.append(p)
    dump(r, response)
    return response
