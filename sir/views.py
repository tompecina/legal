# -*- coding: utf-8 -*-
#
# sir/views.py
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
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse
from locale import strxfrm
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from common.utils import getbutton, grammar, between, Pager
from common.glob import inerr, GR_C, text_opts, text_opts_keys
from szr.forms import EmailForm
from .glob import l2n, l2s
from .models import Vec, Insolvency
from .forms import InsForm, InsBatchForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

@require_http_methods(['GET', 'POST'])
@login_required
def insform(request, id=0):
    err_message = ''
    uid = request.user.id
    page_title = ('Úprava řízení' if id else 'Nové řízení')
    btn = getbutton(request)
    if request.method == 'GET':
        f = (InsForm(initial=model_to_dict(get_object_or_404( \
            Insolvency, pk=id, uid=uid))) if id else InsForm())
    elif btn == 'back':
        return redirect('sir:mainpage')
    else:
        f = InsForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Insolvency, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            p = Insolvency(uid_id=uid, **cd)
            p.save()
            return redirect('sir:mainpage')
        else:
            err_message = inerr
    return render(
        request,
        'sir_insform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def insdel(request, id=0):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'sir_insdel.html',
            {'app': APP,
             'page_title': 'Smazání řízení'})
    else:
        if (getbutton(request) == 'yes'):
            get_object_or_404(Insolvency, pk=id, uid=uid).delete()
            return redirect('sir:insdeleted')
        return redirect('sir:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def insdelall(request, id=0):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'sir_insdelall.html',
            {'app': APP,
             'page_title': 'Smazání všech řízení'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Insolvency.objects.filter(uid=uid).delete()
        return redirect('sir:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def insbatchform(request):

    err_message = ''
    uid = request.user.id

    if (request.method == 'GET'):
        f = InsBatchForm()

    else:
        btn = getbutton(request)

        if btn == 'load':
            f = request.FILES.get('load')
            if not f:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                errors = []
                try:
                    count = 0
                    with f:
                        i = 0
                        for line in csvreader(StringIO(f.read().decode())):
                            i += 1
                            if not line:
                                continue
                            desc = line[0].strip()
                            if not desc:
                                errors.append([i, 'Prázdný popis'])
                                continue
                            try:
                                number = int(line[1])
                                assert number > 0
                            except:
                                errors.append([i, 'Chybný formát běžného čísla'])
                                continue
                            try:
                                year = int(line[2])
                                assert year > 0
                            except:
                                errors.append([i, 'Chybný formát ročníku'])
                                continue
                            detailed = line[3].strip()
                            if detailed == 'ano':
                                detailed = True
                            elif detailed == 'ne':
                                detailed = False
                            else:
                                errors.append([i, 'Chybný formát pro pole Vše'])
                                continue

                            if not errors:
                                try:
                                    Insolvency.objects.update_or_create(
                                        uid_id=uid,
                                        desc=desc,
                                        defaults={
                                            'number': number,
                                            'year': year,
                                            'detailed': detailed}
                                    )
                                except:
                                    errors.append([i, 'Popisu "' + desc + \
                                        '" odpovídá více než jedno řízení'])
                                    continue
                                count += 1
                    return render(
                        request,
                        'sir_insbatchresult.html',
                        {'app': APP,
                         'page_title': 'Import řízení ze souboru',
                         'count': count,
                         'errors': errors})
                except:
                    err_message = 'Chyba při načtení souboru'

        f = InsBatchForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            
            if (not btn) and cd['next']:
                return redirect(cd['next'])

        else:
            err_message = inerr

    return render(
        request,
        'sir_insbatchform.html',
        {'app': APP,
         'page_title': 'Import řízení ze souboru',
         'f': f,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v insolvenčních řízeních'
    rd = request.GET.copy()
    start = int(rd['start']) if ('start' in rd) else 0
    btn = getbutton(request)
    if request.method == 'GET':
        f = EmailForm(initial=model_to_dict(get_object_or_404(User, pk=uid)))
    else:
        f = EmailForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            p = get_object_or_404(User, pk=uid)
            p.email = cd['email']
            p.save()
            return redirect('sir:mainpage')
        else:
            err_message = inerr
    p = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk')
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    return render(
        request,
        'sir_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sir:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
@login_required
def insexport(request):
    uid = request.user.id
    ii = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=sir.csv'
    writer = csvwriter(response)
    for i in ii:
        dat = [
            i.desc,
            str(i.number),
            str(i.year),
            ('ano' if i.detailed else 'ne'),
        ]
        writer.writerow(dat)
    return response

@require_http_methods(['GET'])
def courts(request):
    courts = sorted([{'short': l2s[x], 'name': l2n[x]} for x in \
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()], \
        key=(lambda x: strxfrm(x['name'])))
    return render(
        request,
        'sir_courts.html',
        {'page_title': 'Přehled insolvenčních soudů', 'rows': courts})
