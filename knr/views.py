# -*- coding: utf-8 -*-
#
# knr/views.py
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

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import auth
from django.template import Context, Template
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.db.models import Q
from math import floor, ceil
from urllib.parse import quote, unquote
from json import loads as json_loads
from pickle import dumps, loads
from xml.sax.saxutils import escape, unescape
from datetime import datetime, timedelta
import reportlab.rl_config
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, LongTable, TableStyle, Spacer, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, gray
from io import BytesIO
import os.path
from cache.main import getcache, getasset, setasset
from common.utils import (
    getbutton, unrequire, formam, c2p, getXML, newXML, getint, CanvasXML, lim,
    logger)
from common.glob import inerr, localsubdomain, localurl
from common.views import error, unauth
from .glob import fuels
from .utils import getVAT
from .forms import (
    PlaceForm, CarForm, FormulaForm, CalcForm, GeneralForm, ServiceForm,
    ServiceSubform, FlatForm, FlatSubform, AdministrativeForm,
    AdministrativeSubform, TimeForm, TimeSubform, TravelForm, TravelSubform)
from .models import Place, Car, Formula, Rate

APP = __package__

APPVERSION = apps.get_app_config(APP).version

ctrip = ['cons1', 'cons2', 'cons3']

def findloc(s):
    if not s:
        return False
    s = quote(unquote(s).encode('utf-8'))
    u = ('https://maps.googleapis.com/maps/api/geocode/' \
         'json?address=%s&language=cs&sensor=false' % s)
    r = getcache(u, timedelta(weeks=1))[0]
    if not r:
        return False
    c = json_loads(r)
    if c['status'] != 'OK':
        return False
    c = c['results'][0]
    l = c['geometry']['location']
    return (c['formatted_address'], l['lat'], l['lng'])

def finddist(from_lat, from_lon, to_lat, to_lon):
    u = ('https://maps.googleapis.com/maps/api/distancematrix/' \
         'json?origins=%f,%f&destinations=%f,%f&mode=driving&' \
         'units=metric&language=cs&sensor=false' % \
         (from_lat, from_lon, to_lat, to_lon))
    r = getcache(u, timedelta(weeks=1))[0]
    if not r:
        return (False, False)
    c = json_loads(r)
    if c['status'] != 'OK':
        return (False, False)
    c = c['rows'][0]['elements'][0]
    if c['status'] != 'OK':
        return (False, False)
    return (c['distance']['value'], c['duration']['value'])

def convi(n):
    return formam(int(n))

def convf(n, p):
    tpl = Template('{{ v|floatformat:"%d" }}' % p)
    c = Context({'v': n})
    return tpl.render(c)    

@require_http_methods(['GET', 'POST'])
@login_required
def placeform(request, id=0):
    logger.debug(
        'Place form accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava místa' if id else 'Nové místo')
    btn = getbutton(request)
    if request.method == 'GET':
        f = (PlaceForm(initial=model_to_dict(get_object_or_404(
            Place, pk=id, uid=uid))) if id else PlaceForm())
    elif btn == 'back':
        return redirect('knr:placelist')
    elif btn == 'search':
        f = PlaceForm(request.POST)
        unrequire(f, ['abbr', 'name', 'addr', 'lat', 'lon'])
        loc = findloc(request.POST.get('addr'))
        f.data = f.data.copy()
        if loc:
            f.data['addr'], f.data['lat'], f.data['lon'] = loc
        else:
            f.data['lat'] = f.data['lon'] = ''
            err_message = 'Hledání neúspěšné, prosím, upřesněte adresu'
    else:
        f = PlaceForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Place, pk=id, uid=uid)
                cd['pk'] = id
            Place(uid_id=uid, **cd).save()
            if id:
                logger.info(
                    'User "%s" (%d) updated place "%s"' % \
                    (uname, uid, cd['name']),
                    request)
            else:
                logger.info(
                    'User "%s" (%d) added place "%s"' % \
                    (uname, uid, cd['name']),
                    request)
            return redirect('knr:placelist')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    return render(
        request,
        'knr_placeform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message})

@require_http_methods(['GET'])
@login_required
def placelist(request):
    logger.debug('Place list accessed', request)
    rows = Place.objects.filter(Q(uid=None) | Q(uid=request.user.id)) \
                        .order_by('uid', 'abbr', 'name')
    for row in rows:
        if row.uid:
            row.user = True
        elif rows.filter(abbr=row.abbr).exclude(uid=None):
            row.disabled = True
    return render(
        request,
        'knr_placelist.html',
        {'app': APP,
         'page_title': 'Přehled míst',
         'rows': rows})

@require_http_methods(['GET', 'POST'])
@login_required
def placedel(request, id=0):
    logger.debug(
        'Place delete page accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'knr_placedel.html',
            {'app': APP,
             'page_title': 'Smazání místa',
             'name': get_object_or_404(Place, pk=id, uid=uid).name})
    else:
        place = get_object_or_404(Place, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "%s" (%d) deleted place "%s"' % (uname, uid, place.name),
                request)
            place.delete()
            return redirect('knr:placedeleted')
        return redirect('knr:placelist')

@require_http_methods(['GET', 'POST'])
@login_required
def carform(request, id=0):
    logger.debug(
        'Car form accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava vozidla' if id else 'Nové vozidlo')
    btn = getbutton(request)
    if request.method == 'GET':
        f = (CarForm(initial=model_to_dict(
            get_object_or_404(Car, pk=id, uid=uid))) if id else CarForm())
    elif btn == 'back':
        return redirect('knr:carlist')
    else:
        f = CarForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Car, pk=id, uid=uid)
                cd['pk'] = id
            Car(uid_id=uid, **cd).save()
            if id:
                logger.info(
                    'User "%s" (%d) updated car "%s"' % \
                    (uname, uid, cd['name']),
                    request)
            else:
                logger.info(
                    'User "%s" (%d) added car "%s"' % (uname, uid, cd['name']),
                    request)
            return redirect('knr:carlist')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    return render(
        request,
        'knr_carform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'fuels': fuels})

@require_http_methods(['GET'])
@login_required
def carlist(request):
    logger.debug('Car list accessed', request)
    rows = Car.objects.filter(uid=request.user.id).order_by('abbr', 'name')
    return render(
        request,
        'knr_carlist.html',
        {'app': APP,
         'page_title': 'Přehled vozidel',
         'rows': rows})

@require_http_methods(['GET', 'POST'])
@login_required
def cardel(request, id=0):
    logger.debug(
        'Car delete page accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'knr_cardel.html',
            {'app': APP,
             'page_title':
             'Smazání vozidla',
             'name': get_object_or_404(Car, pk=id, uid=uid).name})
    else:
        car = get_object_or_404(Car, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "%s" (%d) deleted car "%s"' % (uname, uid, car.name),
                request)
            car.delete()
            return redirect('knr:cardeleted')
        return redirect('knr:carlist')

@require_http_methods(['GET', 'POST'])
@login_required
def formulaform(request, id=0):
    logger.debug(
        'Formula form accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava předpisu' if id else 'Nový předpis')
    btn = getbutton(request)
    if request.method == 'GET':
        if id:
            p = model_to_dict(get_object_or_404(Formula, pk=id, uid=uid))
            for fuel in fuels:
                r = Rate.objects.filter(formula=id, fuel=fuel)
                if r and r[0].rate:
                    p['rate_' + fuel] = r[0].rate
            f = FormulaForm(initial=p)
        else:
            f = FormulaForm()
    elif btn == 'back':
        return redirect('knr:formulalist')
    else:
        f = FormulaForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Formula, pk=id, uid=uid)
                cd['pk'] = id
            d = {}
            for k, v in cd.items():
                if k[:5] != 'rate_':
                    d[k] = v
            p = Formula(uid_id=uid, **d)
            p.save()
            if id:
                logger.info(
                    'User "%s" (%d) updated formula "%s"' % \
                    (uname, uid, p.name),
                    request)
            else:
                logger.info(
                    'User "%s" (%d) added formula "%s"' % (uname, uid, p.name),
                    request)
            for fuel in fuels:
                r = Rate.objects.filter(formula=p, fuel=fuel)
                if  r:
                    r = r[0]
                else:
                    r = Rate(formula=p, fuel=fuel)
                r.rate = cd['rate_' + fuel]
                if not r.rate:
                    r.rate = 0
                r.save()
            return redirect('knr:formulalist')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    rates = []
    for fuel in fuels:
        rates.append(f['rate_' + fuel])
    q = rates[0].name
    return render(
        request,
        'knr_formulaform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rates': rates})

@require_http_methods(['GET'])
@login_required
def formulalist(request):
    logger.debug('Formula list accessed', request)
    rows = Formula.objects.filter(Q(uid=None) | Q(uid=request.user.id)) \
                          .order_by('uid', 'abbr', 'name')
    for row in rows:
        rates = []
        for fuel in fuels:
            r = Rate.objects.filter(formula=row.id, fuel=fuel)
            rates.append(r[0].rate if r else 0)
        row.rates = rates
        if row.uid:
            row.user = True
        elif rows.filter(abbr=row.abbr).exclude(uid=None):
            row.disabled = True
    return render(
        request,
        'knr_formulalist.html',
        {'app': APP,
         'page_title': 'Přehled předpisů',
         'fuels': fuels,
         'colspan': (len(fuels) + 4),
         'rows': rows})

@require_http_methods(['GET', 'POST'])
@login_required
def formuladel(request, id=0):
    logger.debug(
        'Formula delete page accessed using method %s, id=%s' % \
            (request.method, id),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'knr_formuladel.html',
            {'app': APP,
             'page_title': 'Smazání předpisu',
             'name': get_object_or_404(Formula, pk=id, uid=uid).name})
    else:
        formula = get_object_or_404(Formula, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "%s" (%d) deleted formula "%s"' % \
                (uname, uid, formula.name),
                request)
            formula.delete()
            return redirect('knr:formuladeleted')
        return redirect('knr:formulalist')

B = 'B'
S = 'S'
I = 'I'
F1 = 'F1'
F2 = 'F2'
F3 = 'F3'
F7 = 'F7'

gd = {'title': S,
      'calculation_note': S,
      'internal_note': S,
      'vat_rate': F2,
      'numerator': I,
      'denominator': I,
      'type': S,
      'description': S,
      'amount': I,
      'vat': B,
      'item_note': S,
      'major_number': I,
      'rate': I,
      'minor_number': I,
      'multiple_number': I,
      'multiple_flag': B,
      'multiple50_flag': B,
      'single_flag': B,
      'halved_flag': B,
      'halved_appeal_flag': B,
      'collection_flag': B,
      'off10_flag': B,
      'off30_flag': B,
      'off30limit5000_flag': B,
      'off20limit5000_flag': B,
      'basis': I,
      'number': I,
      'from_name': S,
      'from_address': S,
      'from_lat': F7,
      'from_lon': F7,
      'to_name': S,
      'to_address': S,
      'to_lat': F7,
      'to_lon': F7,
      'trip_number': I,
      'trip_distance': I,
      'time_rate': I,
      'time_number': I,
      'car_name': S,
      'fuel_name': S,
      'cons1': F1,
      'cons2': F1,
      'cons3': F1,
      'formula_name': S,
      'flat_rate': F2,
      'fuel_price': F2}

ga = {'vat_rate': {'unit': 'percentage'},
      'amount': {'currency': 'CZK'},
      'rate': {'currency': 'CZK'},
      'from_lat': {'unit': 'deg', 'datum': 'WGS84'},
      'from_lon': {'unit': 'deg', 'datum': 'WGS84'},
      'to_lat': {'unit': 'deg', 'datum': 'WGS84'},
      'to_lon': {'unit': 'deg', 'datum': 'WGS84'},
      'trip_distance': {'unit': 'km'},
      'time_rate': {'currency': 'CZK', 'unit': 'per half-hour'},
      'time_number': {'unit': 'half-hour'},
      'cons1': {'unit': 'l per 100 km'},
      'cons2': {'unit': 'l per 100 km'},
      'cons3': {'unit': 'l per 100 km'},
      'flat_rate': {'currency': 'CZK', 'unit': 'per km'},
      'fuel_price': {'currency': 'CZK', 'unit': 'per l'}}

gt = {'general' : ['description', 'amount', 'vat', 'numerator',
                   'denominator', 'item_note'],
      'service' : ['description', 'amount', 'vat', 'numerator',
                   'denominator', 'item_note', 'major_number', 'rate',
                   'minor_number', 'multiple_number', 'off10_flag',
                   'off30_flag', 'off30limit5000_flag', 'off20limit5000_flag'],
      'flat' : ['description', 'amount', 'vat', 'numerator',
                'denominator', 'rate',  'multiple_flag',
                'multiple50_flag', 'item_note', 'single_flag', 'halved_flag',
                'halved_appeal_flag', 'collection_flag'],
      'administrative' : ['description', 'amount', 'vat', 'numerator',
                          'denominator', 'item_note', 'number', 'rate'],
      'time' : ['description', 'amount', 'vat', 'numerator',
                'denominator', 'item_note', 'time_number', 'time_rate'],
      'travel' : ['description', 'amount', 'vat', 'numerator',
                   'denominator', 'item_note', 'from_name', 'from_address',
                  'from_lat', 'from_lon', 'to_name', 'to_address',
                  'to_lat', 'to_lon', 'trip_number', 'trip_distance',
                  'time_rate', 'time_number', 'car_name', 'fuel_name',
                  'cons1', 'cons2', 'cons3', 'formula_name', 'flat_rate',
                  'fuel_price']}

gf = {'general' : ['description', 'amount', 'vat', 'numerator',
                   'denominator', 'item_note'],
      'service' : ['description', 'vat', 'numerator', 'denominator',
                   'item_note', 'major_number', 'rate', 'minor_number',
                   'multiple_number', 'off10_flag', 'off30_flag',
                   'off30limit5000_flag', 'off20limit5000_flag', 'basis'],
      'flat' : ['description', 'vat', 'numerator', 'denominator', 'rate',
                'multiple_flag', 'multiple50_flag', 'basis', 'item_note',
                'single_flag', 'halved_flag', 'halved_appeal_flag',
                'collection_flag'],
      'administrative' : ['description', 'vat', 'numerator', 'denominator',
                          'item_note', 'number', 'rate'],
      'time' : ['description', 'vat', 'numerator', 'denominator',
                'item_note', 'time_number', 'time_rate'],
      'travel' : ['description', 'vat', 'numerator', 'denominator',
                  'item_note', 'from_name', 'from_address', 'from_lat',
                  'from_lon', 'to_name', 'to_address', 'to_lat', 'to_lon',
                  'trip_number', 'trip_distance', 'time_rate', 'time_number',
                  'car_name', 'fuel_name', 'cons1', 'cons2', 'cons3',
                  'formula_name', 'flat_rate', 'fuel_price']}

TEXT = 'text'
TYPE = 'type'
PRESEL = 'presel'

SEP = ('-' * 95)

ps = [{TEXT: 'Vyberte předvolbu:', TYPE: None},

      {TEXT: SEP, TYPE: None},

      {TEXT: 'Soudní poplatek',
       TYPE: 'general',
       PRESEL: {'description': 'Zaplacený soudní poplatek',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: 'Záloha na znalecký posudek',
       TYPE: 'general',
       PRESEL: {'description': 'Zaplacená záloha na znalecký posudek',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: 'Záloha na svědečné',
       TYPE: 'general',
       PRESEL: {'description': 'Zaplacená záloha na svědečné',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: 'Použití motorového vozidla klient',
       TYPE: 'travel',
       PRESEL: {'description': 'Náhrada za použití motorového vozidla (klient)',
                'trip_number': 2,
                'time_rate': 0,
                'fuel_name': 'BA95',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: 'Další hotové výdaje klient',
       TYPE: 'general',
       PRESEL: {'description': 'Další hotové výdaje (klient)',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: SEP, TYPE: None},

      {TEXT: 'Odměna za úkony podle AdvT (neplátce DPH)',
       TYPE: 'service',
       PRESEL: {
           'description':
           'Mimosmluvní odměna za úkony právní služby podle advokátního tarifu',
           'major_number': 0,
           'minor_number': 0,
           'multiple_number': 1,
           'off10_flag': False,
           'off30_flag': False,
           'off30limit5000_flag': False,
           'off20limit5000_flag': False,
           'vat': False,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Paušální odměna podle vyhlášky (neplátce DPH)',
       TYPE: 'flat',
       PRESEL: {
           'description':
           'Paušální odměna za zastupování účastníka podle vyhlášky ' \
           'č. 484/2000 Sb.',
           'multiple_flag': False,
           'multiple50_flag': False,
           'vat': False,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Paušální odměna stanovená pevnou částkou (neplátce DPH)',
       TYPE: 'general',
       PRESEL: {
           'description':
           'Paušální odměna za zastupování účastníka stanovená pevnou částkou',
           'vat': False,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Použití motorového vozidla advokát (neplátce DPH)',
       TYPE: 'travel',
       PRESEL: {
           'description': 'Náhrada za použití motorového vozidla (advokát)',
           'trip_number': 2,
           'time_rate': 100,
           'fuel_name': 'BA95',
           'vat': False,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Další promeškaný čas (neplátce DPH)',
       TYPE: 'time',
       PRESEL: {
           'description': 'Náhrada za promeškaný čas podle advokátního tarifu',
           'time_rate': 100,
           'vat': False,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Režijní paušál za úkony podle AdvT (neplátce DPH)',
       TYPE: 'administrative',
       PRESEL: {
           'description':
           'Paušální náhrada za úkony právní služby podle advokátního tarifu',
           'rate': 300,
           'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: 'Další hotové výdaje advokát (neplátce DPH)',
       TYPE: 'general',
       PRESEL: {'description': 'Další hotové výdaje (advokát)',
                'vat': False,
                'numerator': 1,
                'denominator': 1}},

      {TEXT: SEP, TYPE: None},

      {TEXT: 'Odměna za úkony podle AdvT (plátce DPH)',
       TYPE: 'service',
       PRESEL: {
           'description':
           'Mimosmluvní odměna za úkony právní služby podle advokátního tarifu',
           'major_number': 0,
           'minor_number': 0,
           'multiple_number': 1,
           'off10_flag': False,
           'off30_flag': False,
           'off30limit5000_flag': False,
           'off20limit5000_flag': False,
           'vat': True,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Paušální odměna podle vyhlášky (plátce DPH)',
       TYPE: 'flat',
       PRESEL: {
           'description':
           'Paušální odměna za zastupování účastníka podle vyhlášky ' \
           'č. 484/2000 Sb.',
           'multiple_flag': False,
           'multiple50_flag': False,
           'vat': True,
           'numerator': 1,
           'denominator': 1}},
      
      {TEXT: 'Paušální odměna stanovená pevnou částkou (plátce DPH)',
       TYPE: 'general',
       PRESEL: {
           'description':
           'Paušální odměna za zastupování účastníka stanovená pevnou částkou',
           'vat': True,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Použití motorového vozidla advokát (plátce DPH)',
       TYPE: 'travel',
       PRESEL: {
           'description': 'Náhrada za použití motorového vozidla (advokát)',
           'trip_number': 2,
           'time_rate': 100,
           'fuel_name': 'BA95',
           'vat': True,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Další promeškaný čas (plátce DPH)',
       TYPE: 'time',
       PRESEL: {
           'description': 'Náhrada za promeškaný čas podle advokátního tarifu',
           'time_rate': 100,
           'vat': True,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Režijní paušál za úkony podle AdvT (plátce DPH)',
       TYPE: 'administrative',
       PRESEL: {
           'description':
           'Paušální náhrada za úkony právní služby podle advokátního tarifu',
           'rate': 300,
           'vat': True,
           'numerator': 1,
           'denominator': 1}},

      {TEXT: 'Další hotové výdaje advokát (plátce DPH)',
       TYPE: 'general',
       PRESEL: {'description': 'Další hotové výdaje (advokát)',
                'vat': True,
                'numerator': 1,
                'denominator': 1}}
      ]

fields = ['title', 'calculation_note', 'internal_note', 'vat_rate']

ifields = list(gd.keys())
for t in ['title', 'calculation_note', 'internal_note', 'vat_rate', 'type']:
    ifields.remove(t)

class Calculation:
    def __init__(self):
        self.title = ''
        self.calculation_note = ''
        self.internal_note = ''
        self.vat_rate = getVAT()
        self.items = []

class Item:
    def __init__(self):
        self.type = 'general'
        self.description = ''
        self.amount = 0
        self.vat = False
        self.numerator = 1
        self.denominator = 1
        self.item_note = ''
        self.major_number = 0
        self.rate = 0
        self.minor_number = 0
        self.multiple_number = 0
        self.off10_flag = False
        self.off30_flag = False
        self.off30limit5000_flag = False
        self.off20limit5000_flag = False
        self.multiple_flag = False
        self.multiple50_flag = False
        self.single_flag = False
        self.halved_flag = False
        self.halved_appeal_flag = False
        self.collection = False
        self.number = 0
        self.from_name = ''
        self.from_address = ''
        self.from_lat = 0.0
        self.from_lon = 0.0
        self.to_name = ''
        self.to_address = ''
        self.to_lat = 0.0
        self.to_lon = 0.0
        self.trip_number = 0
        self.trip_distance = 0
        self.time_rate = 0
        self.time_number = 0
        self.car_name = ''
        self.fuel_name = ''
        self.cons1 = 0.0
        self.cons2 = 0.0
        self.cons3 = 0.0
        self.formula_name = ''
        self.flat_rate = 0.0
        self.fuel_price = 0.0

def i2d(f, c, d):
    for t in f:
        p = c.__getattribute__(t)
        y = gd[t]
        if y == B:
            r = bool(p)
        elif y == S:
            r = str(p)
        elif y == I:
            r = int(round(float(c2p(str(p)))))
        else:
            r = float(c2p(str(p)))
        d[t] = r

def d2d(f, d, v):
    for t in f:
        if t in d:
            p = d[t]
            y = gd[t]
            try:
                if y == B:
                    r = bool(p)
                elif y == S:
                    r = str(p)
                elif y == I:
                    r = int(round(float(c2p(str(p)))))
                else:
                    r = float(c2p(str(p)))
            except:
                r = str(p)
            v[t] = r

def s2i(f, s, c):
    for t in f:
        q = s.find(t)
        if q:
            d = gd[t]
            if q.contents:
                p = q.contents[0].strip()
                try:
                    if d == B:
                        r = (p == 'true')
                    elif d == S:
                        r = str(unescape(p))
                    elif d == I:
                        r = int(round(float(c2p(str(p)))))
                    else:
                        r = float(c2p(str(p)))
                    c.__setattr__(t, r)
                except:
                    pass

def d2i(f, d, c):
    for t in f:
        if t in d:
            p = d[t]
            y = gd[t]
            if y == B:
                r = bool(p)
            elif y == S:
                r = str(p)
            elif y == I:
                r = int(round(float(c2p(str(p)))))
            else:
                r = float(c2p(str(p)))
            c.__setattr__(t, r)

aid = (APP.upper() + ' ' + APPVERSION)

def getcalc(request):
    a = getasset(request, aid)
    if a:
        try:
            return loads(a)
        except:  # pragma: no cover
            pass
    setcalc(request, Calculation())
    a = getasset(request, aid)
    return (loads(a) if a else None)

def setcalc(request, data):
    return setasset(request, aid, dumps(data), timedelta(weeks=10))

def toxml(c):
    xml = newXML('')
    calculation = xml.new_tag('calculation')
    xml.insert(0, calculation)
    calculation['xmlns'] = 'http://' + localsubdomain
    calculation['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    calculation['xsi:schemaLocation'] = \
        ('http://' + localsubdomain + ' ' + localurl + '/static/%s-%s.xsd') % \
        (APP, APPVERSION)
    calculation['application'] = APP
    calculation['version'] = APPVERSION
    calculation['created'] = datetime.now().replace(microsecond=0).isoformat()
    for t in ['title', 'calculation_note', 'internal_note']:
        tag = xml.new_tag(t)
        tag.insert(0, escape(c.__getattribute__(t)).strip())
        calculation.insert(len(calculation), tag)
        if tag.name in ga:  # pragma: no cover
            for key, val in ga[tag.name].items():
                tag[key] = val
    vat_rate = xml.new_tag('vat_rate')
    vat_rate.insert(0, ('%.2f' % c.vat_rate))
    for key, val in ga['vat_rate'].items():
        vat_rate[key] = val
    calculation.insert(len(calculation), vat_rate)
    items = xml.new_tag('items')
    calculation.insert(len(calculation), items)
    for i in c.items:
        item = xml.new_tag(i.type)
        items.insert(len(items), item)
        for t in gt[i.type]:
            tag = xml.new_tag(t)
            item.insert(len(item), tag)
            if tag.name in ga:
                for key, val in ga[tag.name].items():
                    tag[key] = val
            p = i.__getattribute__(t)
            y = gd[t]
            if y == S:
                r = str(escape(p))
            elif y == B:
                if p:
                    r = 'true'
                else:
                    r = 'false'
            elif y == I:
                r = ('%d' % p)
            elif y[0] == 'F':
                r = (('%%.%uf' % int(y[1])) % p)
            tag.insert(0, r.strip())
    return str(xml).encode('utf-8') + b'\n'

def fromxml(d):
    s = getXML(d)
    if not s:
        return None, 'Chybný formát souboru'
    h = s.findChild('calculation')
    if ((not h) or (h.has_attr('application') and (h['application'] != APP))):
        return None, 'Soubor nebyl vytvořen touto aplikací'
    c = Calculation()
    s2i(fields, s, c)
    l = s.items.children
    for ll in l:
        if not ll.name:  # pragma: no cover
            continue
        item = Item()
        s2i(ifields, ll, item)
        try:
            if ll.has_attr('type'):  # pragma: no cover
                item.type = str(ll['type'])
            else:
                item.type = str(ll.name)
        except:  # pragma: no cover
            return None, 'Chybný formát souboru'
        c.items.append(item)
    return c, None

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    
    logger.debug(
        'Main page accessed using method ' + request.method,
        request,
        request.POST)

    c = getcalc(request)
    if not c:  # pragma: no cover
        return error(request)
    var = {'app': APP,
           'page_title': 'Kalkulace nákladů řízení',
           'errors': False, 'rows': []
    }
    if request.method == 'GET':
        i2d(fields, c, var)
        for t in fields:
            var[t + '_error'] = 'ok'
    else:
        f = CalcForm(request.POST)
        for t in fields:
            var[t + '_error'] = 'ok'
        d2d(fields, f.data, var)
        btn = getbutton(request)
        if btn == 'empty':
            c = Calculation()
            if not setcalc(request, c):  # pragma: no cover
                return error(request)
            return redirect('knr:mainpage')
        if btn == 'load':
            f = request.FILES.get('load')
            if not f:
                var['errors'] = True
                var['err_message'] = 'Nejprve zvolte soubor k načtení'
                return render(request, 'knr_mainpage.html', var)
            try:
                d = f.read()
                f.close()
            except:  # pragma: no cover
                raise Exception('Error reading file')
            c, m = fromxml(d)
            if m:
                var['errors'] = True
                var['err_message'] = m
                return render(request, 'knr_mainpage.html', var)
            if not setcalc(request, c):  # pragma: no cover
                return error(request)
            return redirect('knr:mainpage')
        elif btn:
            f = CalcForm(request.POST)
            if f.is_valid():
                cd = f.cleaned_data
                d2i(fields, cd, c)
                if not setcalc(request, c):  # pragma: no cover
                    return error(request)
                var.update(cd)
                for t in fields:
                    var[t + '_error'] = 'ok'
                if btn == 'edit':
                    return redirect('knr:itemlist')
                if btn == 'xml':
                    response = HttpResponse(
                        toxml(c),
                        content_type='text/xml; charset=utf-8')
                    response['Content-Disposition'] = \
                        'attachment; filename=Naklady.xml'
                    return response
                if btn == 'pdf':

                    def page1(c, d):
                        c.saveState()
                        c.setFont('Bookman', 7)
                        c.drawString(64.0, 48.0, ('KNR V%s' % APPVERSION))
                        c.setFont('BookmanI', 7)
                        nw = datetime.now()
                        c.drawRightString(
                            (A4[0] - 48.0),
                            48.0,
                            ('Vytvořeno: %u. %u. %u' % \
                             (nw.day, nw.month, nw.year)))
                        c.restoreState()

                    fontdir = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        'common/fonts/').replace('\\','/')
                    reportlab.rl_config.warnOnMissingFontGlyphs = 0
                    registerFont(TTFont(
                        'Bookman',
                        (fontdir + 'URWBookman-Regular.ttf')))
                    registerFont(TTFont(
                        'BookmanB',
                        (fontdir + 'URWBookman-Bold.ttf')))
                    registerFont(TTFont(
                        'BookmanI',
                        (fontdir + 'URWBookman-Italic.ttf')))
                    registerFont(
                        TTFont('BookmanBI',
                               (fontdir + 'URWBookman-BoldItalic.ttf')))
                    registerFontFamily(
                        'Bookman',
                        normal='Bookman',
                        bold='BookmanB',
                        italic='BookmanI',
                        boldItalic='BookmanBI')
                    s1 = ParagraphStyle(
                        name='S1',
                        fontName='Bookman',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s2 = ParagraphStyle(
                        name='S2',
                        fontName='BookmanB',
                        fontSize=10,
                        leading=11,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s3 = ParagraphStyle(
                        name='S3',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s4 = ParagraphStyle(
                        name='S4',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=10,
                        allowWidows=False,
                        allowOrphans=False)
                    s5 = ParagraphStyle(
                        name='S5',
                        fontName='Bookman',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s6 = ParagraphStyle(
                        name='S6',
                        fontName='Bookman',
                        fontSize=7,
                        leading=9,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)
                    s7 = ParagraphStyle(
                        name='S7',
                        fontName='BookmanI',
                        fontSize=7,
                        leading=9,
                        spaceBefore=1,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)
                    s8 = ParagraphStyle(
                        name='S8',
                        fontName='Bookman',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s9 = ParagraphStyle(
                        name='S9',
                        fontName='BookmanB',
                        fontSize=8, leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s10 = ParagraphStyle(
                        name='S10',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s11 = ParagraphStyle(
                        name='S11',
                        fontName='Bookman',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)
                    s12 = ParagraphStyle(
                        name='S12',
                        fontName='BookmanI',
                        fontSize=8,
                        leading=9,
                        spaceBefore=4,
                        spaceAfter=5,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)
                    d1 =[[[Paragraph('Kalkulace nákladů řízení'.upper(), s1)]]]
                    if c.title:
                        d1[0][0].append(Paragraph(escape(c.title), s2))
                    t1 = LongTable(d1, colWidths=[483.30])
                    t1.setStyle(
                        TableStyle([
                            ('LINEABOVE', (0, 0), (0, -1), 1.0, black),
                            ('TOPPADDING', (0, 0), (0, -1), 2),
                            ('LINEBELOW', (-1, 0), (-1, -1), 1.0, black),
                            ('BOTTOMPADDING', (-1, 0), (-1, -1), 3),
                            ('LEFTPADDING', (0, 0), (-1, -1), 2),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ]))
                    flow = [t1, Spacer(0, 36)]
                    if c.items:
                        d2 = []
                        for i in range(len(c.items)):
                            item = c.items[i]
                            r = [Paragraph(('%u.' % (i + 1)), s3)]
                            q = [Paragraph(escape(item \
                                                  .description \
                                                  .upper() \
                                                  .replace(' Č. ', ' č. ') \
                                                  .replace(' SB.', ' Sb.')),
                                           s4)]
                            if item.type == 'service':
                                if item.multiple_number < 2:
                                    q.append(Paragraph(
                                        ('<b>Hlavních úkonů:</b> %u ' \
                                         '&nbsp; <b>Vedlejších úkonů:</b> ' \
                                         '%u' % (item.major_number,
                                                 item.minor_number)),
                                        s6))
                                else:
                                    q.append(Paragraph(
                                        ('<b>Hlavních úkonů:</b> %u ' \
                                         '&nbsp; <b>Vedlejších úkonů:</b> ' \
                                         '%u &nbsp; <b>Zastupovaných ' \
                                         'účastníků:</b> %u' \
                                        % (item.major_number,
                                           item.minor_number,
                                           item.multiple_number)),
                                        s6))
                            if item.type == 'administrative':
                                q.append(Paragraph(
                                    ('<b>Počet úkonů:</b> %u &nbsp; ' \
                                     '<b>Sazba:</b> %s Kč' % \
                                     (item.number, convi(item.rate))),
                                    s6))
                            if item.type == 'time':
                                q.append(Paragraph(
                                    ('<b>Počet započatých půlhodin:</b> %u ' \
                                     '&nbsp; <b>Sazba:</b> %s Kč/půlhodinu' % \
                                     (item.time_number, convi(item.time_rate))),
                                    s6))
                            if item.type == 'travel':
                                q.append(Paragraph(
                                    ('<b>Z:</b> %s (%s)' % \
                                     (escape(item.from_name),
                                      escape(item.from_address.replace(
                                          ', Česká republika', '')))),
                                    s6))
                                q.append(Paragraph(
                                    ('<b>Do:</b> %s (%s)' % \
                                     (escape(item.to_name),
                                      escape(item.to_address.replace(
                                          ', Česká republika', '')))),
                                    s6))
                                q.append(Paragraph(
                                    ('<b>Vzdálenost:</b> %s km &nbsp; ' \
                                     '<b>Počet cest:</b> %u' % \
                                     (convi(item.trip_distance),
                                      item.trip_number)),
                                    s6))
                                if (item.time_number and item.time_rate):
                                    q.append(Paragraph(
                                        ('<b>Počet započatých půlhodin:</b> ' \
                                         '%u &nbsp; <b>Sazba:</b> %s ' \
                                         'Kč/půlhodinu' % \
                                         ((item.time_number * item.trip_number),
                                          convi(item.time_rate))),
                                        s6))
                                q.append(Paragraph(
                                    ('<b>Vozidlo</b> %s' % \
                                     escape(item.car_name)),
                                    s6))
                                q.append(Paragraph(
                                    ('<b>Palivo:</b> %s &nbsp; ' \
                                     '<b>Průměrná spotřeba:</b> %s l/100 km' % \
                                     (item.fuel_name,
                                      convf(((item.cons1 + item.cons2 + \
                                              item.cons3) / 3.0), 3))),
                                    s6))
                                q.append(Paragraph(
                                    ('<b>Předpis:</b> %s' % \
                                     escape(item.formula_name)),
                                    s6))
                                q.append(Paragraph(
                                    ('<b>Paušál:</b> %s Kč/km &nbsp; ' \
                                     '<b>Cena paliva:</b> %s Kč/l' % \
                                     (convf(item.flat_rate, 2),
                                      convf(item.fuel_price, 2))),
                                    s6))
                            if (item.numerator > 1) or (item.denominator > 1):
                                q.append(Paragraph(
                                    ('<b>Zlomek:</b> %u/%u' % \
                                     (item.numerator, item.denominator)),
                                    s6))
                            if item.item_note:
                                for s in filter(bool, item.item_note.strip() \
                                                .split('\n')):
                                    q.append(Paragraph(escape(s), s7))
                            r.append(q)
                            r.append(Paragraph(
                                ('%s Kč' % convi(item.amount)), s5))
                            d2.append(r)         
                        t2 = LongTable(d2, colWidths=[16.15, 400.45, 66.70])
                        t2.setStyle(
                            TableStyle([
                                ('LINEABOVE', (0, 0), (-1, 0), 0.25, gray),
                                ('LINEBELOW', (0, 0), (-1, -1), 0.25, gray),
                                ('VALIGN', (0, 0), (1, -1), 'TOP'),
                                ('VALIGN', (-1, 0), (-1, -1), 'MIDDLE'),
                                ('RIGHTPADDING', (0, 0), (1, -1), 0),
                                ('RIGHTPADDING', (-1, 0), (-1, -1), 2),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('LEFTPADDING', (1, 0), (1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 4),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ]))
                        flow.extend([t2, Spacer(0, 24)])
                    total_net = total_ex = 0
                    for i in c.items:
                        if i.vat:
                            total_net += int(i.amount)
                        else:
                            total_ex += int(i.amount)
                    total_vat = \
                        int(round(float(total_net * c.vat_rate) / 100.0))
                    total = int(total_net + total_ex + total_vat)
                    d3 = []
                    if total_vat:
                        d3.append(
                            [None,
                             Paragraph('Základ bez DPH', s8),
                             Paragraph(('%s Kč' % convi(total_ex)), s11)])
                        d3.append(
                            [None,
                             Paragraph('Základ s DPH', s8),
                             Paragraph(('%s Kč' % convi(total_net)), s11)])
                        d3.append(
                            [None,
                             Paragraph(('DPH %s %%' % convf(c.vat_rate, 0)),
                                       s8),
                             Paragraph(('%s Kč' % convi(total_vat)), s11)])
                    d3.append(
                        [None,
                         Paragraph('Celkem'.upper(), s9),
                         Paragraph(('%s Kč' % convi(total)), s10)])
                    if total_vat:
                        t3 = LongTable(d3, colWidths=[346.60, 70.00, 66.70])
                    else:                      
                        t3 = LongTable(d3, colWidths=[366.60, 50.00, 66.70])
                    l3 = [('LINEABOVE', (1, 0), (-1, 0), 1.0, black),
                          ('LINEABOVE', (1, -1), (-1, -1), 1.0, black),
                          ('LINEBELOW', (1, -1), (-1, -1), 1.0, black),
                          ('RIGHTPADDING', (0, 0), (1, -1), 0),
                          ('RIGHTPADDING', (-1, 0), (-1, -1), 2),
                          ('LEFTPADDING', (0, 0), (-1, -1), 0),
                          ('LEFTPADDING', (1, 0), (1, -1), 6),
                          ('TOPPADDING', (0, 0), (-1, -1), -1),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                          ]
                    if total_vat:
                        l3.append(('TOPPADDING', (0, 1), (-1, 2), -3))
                    t3.setStyle(TableStyle(l3))
                    flow.append(KeepTogether([t3]))
                    if c.calculation_note:
                        flow.append(Spacer(0, 24))
                        q = [Paragraph('Poznámka:'.upper(), s4)]
                        for s in filter(bool,
                                        c.calculation_note.strip().split('\n')):
                            q.append(Paragraph(escape(s), s12))
                        flow.append(KeepTogether(q[:2]))
                        if len(q) > 2:
                            flow.extend(q[2:])
                    temp = BytesIO()
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = \
                        'attachment; filename=Naklady.pdf'
                    doc = SimpleDocTemplate(
                        temp,
                        pagesize=A4,
                        title='Kalkulace nákladů řízení',
                        author=('KNR V%s' % APPVERSION),
                        leftMargin=64.0,
                        rightMargin=48.0,
                        topMargin=48.0,
                        bottomMargin=96.0,
                        )
                    CanvasXML.xml = toxml(c)
                    doc.build(
                        flow,
                        onFirstPage=page1,
                        onLaterPages=page1,
                        canvasmaker=CanvasXML)
                    response.write(temp.getvalue())
                    return response
                if btn == "place":
                    return redirect('knr:placelist')
                if btn == "car":
                    return redirect('knr:carlist')
                if btn == "formula":
                    return redirect('knr:formulalist')
            else:
                var.update({'errors': True})
                d2d(fields, f.data, var)
                for t in fields:
                    if f[t].errors:
                        var[t + '_error'] = 'err'
                    else:
                        var[t + '_error'] = 'ok'
        else:  # pragma: no cover
            i2d(fields, c, var)
    var['total_net'] = var['total_ex'] = var['num_items'] = 0
    for i in c.items:
        if i.vat:
            var['total_net'] += int(i.amount)
        else:
            var['total_ex'] += int(i.amount)
        var['num_items'] += 1
    var['total_vat'] = int(round(float(var['total_net'] * c.vat_rate) / 100.0))
    var['total'] = int(var['total_net'] + var['total_ex'] + var['total_vat'])
    for i in ['total_net', 'total_ex',  'total_vat', 'total']:
        var[i] = formam(var[i])
    return render(request, 'knr_mainpage.html', var)

@require_http_methods(['GET', 'POST'])
@login_required
def itemform(request, idx=0):

    def addtravellists(var):
        p = Place.objects.filter(Q(uid=None) | Q(uid=uid)) \
                         .order_by('abbr', 'name')
        l1 = []
        for t in p:
            if t.uid or (not p.filter(abbr=t.abbr, uid=uid)):
                l1.append({'idx': t.id, 'text': t.abbr + ' – ' + t.name})
        p = Car.objects.filter(uid=uid).order_by('abbr', 'name')
        l2 = []
        for t in p:
            l2.append({'idx': t.id, 'text': t.abbr + ' – ' + t.name})
        p = Formula.objects.filter(Q(uid=None) | Q(uid=uid)) \
                           .order_by('abbr', 'name')
        l3 = []
        for t in p:
            if t.uid or (not p.filter(abbr=t.abbr, uid=uid)):
                l3.append({'idx': t.id, 'text': t.abbr + ' – ' + t.name})
        var.update(
            {'sep': ('-' * 110),
             'from_sels': l1,
             'to_sels': l1,
             'car_sels': l2,
             'formula_sels': l3,
             'fuel_names': fuels})

    def proc_from(sel, cd):
        p = Place.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if p:
            cd['from_name'] = p[0].name
            cd['from_address'] = p[0].addr
            cd['from_lat'] = p[0].lat
            cd['from_lon'] = p[0].lon
            cd['trip_distance'] = cd['time_number'] = ''

    def proc_to(sel, cd):
        p = Place.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if p:
            cd['to_name'] = p[0].name
            cd['to_address'] = p[0].addr
            cd['to_lat'] = p[0].lat
            cd['to_lon'] = p[0].lon
            cd['trip_distance'] = cd['time_number'] = ''

    def proc_car(sel, cd):
        p = Car.objects.filter(pk=sel, uid=uid)
        if p:
            cd['car_name'] = p[0].name
            cd['fuel_name'] = p[0].fuel
            cd['cons1'] = float(p[0].cons1)
            cd['cons2'] = float(p[0].cons2)
            cd['cons3'] = float(p[0].cons3)

    def proc_formula(sel, cd):
        p = Formula.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if p:
            cd['formula_name'] = p[0].name
            cd['flat_rate'] = float(p[0].flat)
            q = Rate.objects.filter(formula=sel, fuel=cd['fuel_name'])
            if q:
                cd['fuel_price'] = float(q[0].rate)
            else:
                cd['fuel_price'] = ''

    def proc_dist(cd):
        cd['trip_distance'] = cd['time_number'] = ''
        p = {}
        d2d(['from_lat', 'from_lon', 'to_lat', 'to_lon'], cd, p)
        if (p['from_lat'] and p['from_lon'] and p['to_lat'] and p['to_lon']):
            dist, dur = finddist(
                p['from_lat'],
                p['from_lon'],
                p['to_lat'],
                p['to_lon'])
            if dist:
                cd['trip_distance'] = int(ceil(dist / 1000.0))
            if dur:
                cd['time_number'] = int(ceil(dur / 1800.0))

    logger.debug(
        'Item form accessed using method %s, idx=%s' % \
            (request.method, idx),
        request,
        request.POST)
    uid = request.user.id
    c = getcalc(request)
    if not c:  # pragma: no cover
        return error(request)
    var = {'app': APP, 'errors': False}
    if (request.method == 'GET'):
        if idx:
            idx = int(idx)
            var.update({'idx': idx, 'page_title': 'Úprava položky'})
            if idx > len(c.items):
                raise Http404
            c = c.items[idx - 1]
            i2d(gt[c.type], c, var)
            var['type'] = c.type
            for t in gf[c.type]:
                var[t + '_error'] = 'ok'
            if var['type'] == 'travel':
                addtravellists(var)
                var['cons_error'] = 'ok'
        else:
            return redirect('knr:itemlist')
    else:
        btn = getbutton(request)
        if btn == 'back':
            return redirect('knr:itemlist')
        if btn == 'new':
            presel = request.POST.get('presel')
            if presel and \
               presel.isdigit() and \
               int(presel) and \
               (int(presel) < len(ps)) and \
               ps[int(presel)][TYPE]:
                var.update({'idx': 0, 'page_title': 'Nová položka'})
                var.update(ps[int(presel)][PRESEL])
                var['type'] = ps[int(presel)][TYPE]
                for t in gf[var['type']]:
                    var[t + '_error'] = 'ok'
                if var['type'] == 'travel':
                    addtravellists(var)
                    var['cons_error'] = 'ok'
            else:
                return redirect('knr:itemlist')
        else:
            type = str(request.POST.get('type'))
            if type not in gf:
                raise Http404
            if type == 'travel':
                addtravellists(var)
            if request.POST.get('submit'):
                if type == 'travel':
                    f = TravelSubform(request.POST)
                    if f.is_valid():
                        cd = f.cleaned_data
                        sel = False
                        if request.POST.get('from_sel'):
                            proc_from(int(request.POST.get('from_sel')), cd)
                            sel = True
                        if request.POST.get('to_sel'):
                            proc_to(int(request.POST.get('to_sel')), cd)
                            sel = True
                        if request.POST.get('car_sel'):
                            proc_car(int(request.POST.get('car_sel')), cd)
                            sel = True
                        if request.POST.get('formula_sel'):
                            proc_formula(
                                int(request.POST.get('formula_sel')),
                                cd)
                            sel = True
                        if (not (cd['trip_distance'] and cd['time_number'])):
                            proc_dist(cd)
                            if (cd['trip_distance'] and cd['time_number']):
                                sel = True
                        if sel:
                            idx = cd['idx']
                            var.update({'idx': idx, 'type': type})
                            if idx:
                                var['page_title'] = 'Úprava položky'
                            else:
                                var['page_title'] = 'Nová položka'
                            d2d(gf[type], cd, var)
                            for t in gf[type]:
                                var[t + '_error'] = 'ok'
                            var['cons_error'] = 'ok'
                        else:
                            f = TravelForm(request.POST)
                            if f.is_valid():
                                cd = f.cleaned_data
                                i = Item()
                                cd['amount'] = \
                                    int(round((cd['trip_distance'] * \
                                    ((float((cd['cons1'] + cd['cons2'] + \
                                    cd['cons3']) * cd['fuel_price']) / \
                                    300.0) + float(cd['flat_rate'])) + \
                                    (cd['time_number'] * cd['time_rate'])) * \
                                    cd['trip_number']))
                                if (cd['numerator'] > 1) or \
                                   (cd['denominator'] > 1):
                                    cd['amount'] = \
                                        (cd['amount'] * cd['numerator']) / \
                                        cd['denominator']
                                d2i(gt[type], cd, i)
                                i.type = type
                                idx = cd['idx']
                                if idx:
                                    if idx > len(c.items):
                                        raise Http404
                                    c.items[idx - 1] = i
                                else:
                                    c.items.append(i)
                                if not setcalc(request, c):  # pragma: no cover
                                    return error(request)
                                return redirect('knr:itemlist')
                            else:
                                idx = getint(request.POST.get('idx'))
                                var.update({'errors': True,
                                            'idx': idx,
                                            'type': type})
                                if idx:
                                    var['page_title'] = 'Úprava položky'
                                else:
                                    var['page_title'] = 'Nová položka'
                                d2d(gf[type], f.data, var)
                                for t in gf[type]:
                                    if f[t].errors:
                                        var[t + '_error'] = 'err'
                                    else:
                                        var[t + '_error'] = 'ok'
                                var['cons_error'] = 'ok'
                                for t in ctrip:
                                    if f[t].errors:
                                        var['cons_error'] = 'err'
                                        break
                    else:
                        raise Http404
                else:
                    f = eval(type.title() + 'Form(request.POST)')
                    if f.is_valid():
                        cd = f.cleaned_data
                        i = Item()
                        if type == 'service':
                            cd['amount'] = \
                                int(round(cd['major_number'] * cd['rate'] + \
                                cd['minor_number'] * 0.5 * cd['rate']))
                            if cd['off10_flag']:
                                cd['amount'] = int(round(0.9 * cd['amount']))
                            if cd['off30_flag']:
                                cd['amount'] = int(round(0.7 * cd['amount']))
                            if cd['off30limit5000_flag']:
                                cd['amount'] = \
                                    min(int(round(0.7 * cd['amount'])), 5000)
                            if cd['off20limit5000_flag']:
                                cd['amount'] = \
                                    min(int(round(0.8 * cd['amount'])), 5000)
                            if cd['multiple_number'] > 1:
                                cd['amount'] = int(round(0.8 * \
                                    cd['multiple_number'] * cd['amount']))
                        elif type == 'flat':
                            cd['amount'] = cd['rate']
                            if cd['collection_flag']:
                                cd['amount'] = \
                                    max(int(round(0.5 * cd['amount'])), 750)
                            if cd['halved_flag']:
                                cd['amount'] = lim(750, int(round(0.5 * \
                                    cd['amount'])), 15000)
                            if cd['halved_appeal_flag']:
                                cd['amount'] = lim(750, int(round(0.5 * \
                                    cd['amount'])), 20000)
                            if cd['single_flag']:
                                cd['amount'] = \
                                    max(int(round(0.5 * cd['amount'])), 400)
                            if cd['multiple_flag']:
                                cd['amount'] = int(round(1.3 * cd['amount']))
                            if cd['multiple50_flag']:
                                cd['amount'] = int(round(1.5 * cd['amount']))
                            cd['amount'] = int(ceil(cd['amount'] / 10.0) * 10)
                        elif type == 'administrative':
                            cd['amount'] = (cd['number'] * cd['rate'])
                        elif type == 'time':
                            cd['amount'] = (cd['time_number'] * cd['time_rate'])
                        if (cd['numerator'] > 1) or (cd['denominator'] > 1):
                            cd['amount'] = (cd['amount'] * cd['numerator']) / \
                                cd['denominator']
                        d2i(gt[type], cd, i)
                        i.type = type
                        idx = cd['idx']
                        if idx:
                            if idx > len(c.items):
                                raise Http404
                            c.items[idx - 1] = i
                        else:
                            c.items.append(i)
                        if not setcalc(request, c):  # pragma: no cover
                            return error(request)
                        return redirect('knr:itemlist')
                    else:
                        idx = getint(request.POST.get('idx'))
                        var.update({'errors': True, 'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], f.data, var)
                        for t in gf[type]:
                            if f[t].errors:
                                var[t + '_error'] = 'err'
                            else:
                                var[t + '_error'] = 'ok'
                        var['fraction_error'] = \
                            'err' if ( \
                                f['numerator'].errors or \
                                f['denominator'].errors) \
                            else 'ok'
            else:
                f = eval(type.title() + 'Subform(request.POST)')
                if f.is_valid():
                    cd = f.cleaned_data
                    if type == 'service':
                        b = cd['basis']
                        if btn == 'calc1':
                            if b <= 500:
                                r = 250
                            elif b <= 1000:
                                r = 500
                            elif b <= 5000:
                                r = 750
                            elif b <= 10000:
                                r = 1000
                            elif b <= 200000:
                                r = 1000 + \
                                    25 * int(ceil((b - 10000) / 1000.0))
                            elif b <= 10000000:
                                r = 5750 + \
                                    25 * int(ceil((b - 200000) / 10000.0))
                            else:
                                r = 30250 + \
                                    25 * int(ceil((b - 10000000) / 100000.0))
                        else:
                            if b <= 500:
                                r = 300
                            elif b <= 1000:
                                r = 500
                            elif b <= 5000:
                                r = 1000
                            elif b <= 10000:
                                r = 1500
                            elif b <= 200000:
                                r = 1500 + \
                                    40 * int(ceil((b - 10000) / 1000.0))
                            elif b <= 10000000:
                                r = 9100 + \
                                    40 * int(ceil((b - 200000) / 10000.0))
                            else:
                                r = 48300 + \
                                    40 * int(ceil((b - 10000000) / 100000.0))
                        idx = cd['idx']
                        var.update({'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], cd, var)
                        var['rate'] = r
                        for t in gf[type]:
                            var[t + '_error'] = 'ok'
                    elif type == 'flat':
                        b = cd['basis']
                        if btn == 'calc1':
                            if b <= 500:
                                r = 1500
                            elif b <= 1000:
                                r = 3000
                            elif b <= 5000:
                                r = 4500
                            elif b <= 10000:
                                r = 6000
                            elif b <= 200000:
                                r = 6000 + 0.15 * (b - 10000.0)
                            elif b <= 10000000:
                                r = 34500 + 0.015 * (b - 200000.0)
                            else:
                                r = 181500 + 0.00015 * (b - 10000000.0)
                        elif btn == 'calc2':
                            if b <= 1000:
                                r = 4500
                            elif b <= 5000:
                                r = 6000
                            elif b <= 10000:
                                r = 9000
                            elif b <= 200000:
                                r = 9000 + 0.17 * (b - 10000.0)
                            elif b <= 10000000:
                                r = 41300 + 0.02 * (b - 200000.0)
                            else:
                                r = 237300 + 0.0015 * (b - 10000000.0)
                        else:
                            if b <= 100:
                                r = 1000
                            elif b <= 500:
                                r = 1500
                            elif b <= 1000:
                                r = 2500
                            elif b <= 2000:
                                r = 3750
                            elif b <= 5000:
                                r = 4800
                            elif b <= 10000:
                                r = 7500
                            elif b <= 200000:
                                r = 7500 + 0.17 * (b - 10000.0)
                            elif b <= 10000000:
                                r = 39800 + 0.02 * (b - 200000.0)
                            else:
                                r = 235800 + 0.0015 * (b - 10000000.0)
                        r = int(ceil(r / 10.0) * 10)
                        idx = cd['idx']
                        var.update({'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], cd, var)
                        var['rate'] = r
                        for t in gf[type]:
                            var[t + '_error'] = 'ok'
                    elif type == 'administrative':
                        if btn == 'calc1':
                            r = 75
                        else:
                            r = 300
                        idx = cd['idx']
                        var.update({'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], cd, var)
                        var['rate'] = r
                        for t in gf[type]:
                            var[t + '_error'] = 'ok'
                    elif type == 'time':
                        if btn == 'calc1':
                            r = 50
                        else:
                            r = 100
                        idx = cd['idx']
                        var.update({'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], cd, var)
                        var['time_rate'] = r
                        for t in gf[type]:
                            var[t + '_error'] = 'ok'
                    elif type == 'travel':
                        if ((btn == 'from_apply') and \
                            request.POST.get('from_sel')):
                            proc_from(int(request.POST.get('from_sel')), cd)
                            proc_dist(cd)
                        elif ((btn == 'from_search') and \
                              request.POST.get('from_address')):
                            loc = findloc(request.POST.get('from_address'))
                            if loc:
                                cd['from_address'], \
                                cd['from_lat'], \
                                cd['from_lon'] = loc
                            else:
                                var.update(
                                    {'errors': True,
                                     'err_message': 'Hledání neúspěšné, ' \
                                     'prosím, upřesněte adresu.'})
                                cd.update({'from_lat': '', 'from_lon': ''})
                            proc_dist(cd)
                        elif ((btn == 'to_apply') and \
                              request.POST.get('to_sel')):
                            proc_to(int(request.POST.get('to_sel')), cd)
                            proc_dist(cd)
                        elif ((btn == 'to_search') and \
                              request.POST.get('to_address')):
                            loc = findloc(request.POST.get('to_address'))
                            if loc:
                                cd['to_address'], \
                                cd['to_lat'], \
                                cd['to_lon'] = loc
                            else:
                                var.update(
                                    {'errors': True,
                                     'err_message': 'Hledání neúspěšné, ' \
                                     'prosím, upřesněte adresu.'})
                                cd.update({'to_lat': '', 'to_lon': ''})
                            proc_dist(cd)
                        elif btn == 'calc':
                            proc_dist(cd)
                        elif btn == 'calc1':
                            cd['time_rate'] = 50
                        elif btn == 'calc2':
                            cd['time_rate'] = 100
                        elif ((btn == 'car_apply') and \
                              request.POST.get('car_sel')):
                            proc_car(int(request.POST.get('car_sel')), cd)
                        elif ((btn == 'formula_apply') and \
                              request.POST.get('formula_sel')):
                            proc_formula(int(request.POST.get('formula_sel')),
                                         cd)
                        idx = cd['idx']
                        var.update({'idx': idx, 'type': type})
                        if idx:
                            var['page_title'] = 'Úprava položky'
                        else:
                            var['page_title'] = 'Nová položka'
                        d2d(gf[type], cd, var)
                        if not var['fuel_price']:
                            var['fuel_price'] = ''
                        for t in gf[type]:
                            var[t + '_error'] = 'ok'
                        var['cons_error'] = 'ok'
                else:
                    idx = getint(request.POST.get('idx'))
                    var.update({'errors': True, 'idx': idx, 'type': type})
                    if idx:
                        var['page_title'] = 'Úprava položky'
                    else:
                        var['page_title'] = 'Nová položka'
                    d2d(gf[type], f.data, var)
                    for t in gf[type]:
                        if f[t].errors:
                            var[t + '_error'] = 'err'
                        else:
                            var[t + '_error'] = 'ok'
    return render(request, 'knr_itemform.html', var)

@require_http_methods(['GET', 'POST'])
@login_required
def itemlist(request):
    logger.debug(
        'Item list accessed using method ' + request.method,
        request,
        request.POST)
    c = getcalc(request)
    if not c:  # pragma: no cover
        return error(request)
    var = {'app': APP,
           'page_title': 'Položky kalkulace',
           'rows': [],
           'presel': []}
    n = 0
    for row in c.items:
        r = {'idx': (n + 1), 'up': (n > 0), 'down': (n < (len(c.items) - 1))}
        i2d(['description', 'amount'], row, r)
        r['amount'] = formam(r['amount'])
        n += 1
        var['rows'].append(r)
    n = 0
    for presel in ps:
        if presel[TYPE]:
            p = n
        else:
            p = ''
        var['presel'].append({'idx': p, 'text': presel[TEXT]})
        n += 1
    return render(request, 'knr_itemlist.html', var)

@require_http_methods(['GET', 'POST'])
@login_required
def itemdel(request, idx=0):
    logger.debug(
        'Item delete page accessed using method %s, idx=%s' % \
            (request.method, idx),
        request,
        request.POST)
    idx = (int(idx) - 1)
    var = {'app': APP, 'page_title': 'Smazání položky'}
    c = getcalc(request)
    if not c:  # pragma: no cover
        return error(request)
    if idx >= len(c.items):
        raise Http404
    if request.method == 'GET':
        var['idx'] = idx
        var['desc'] = c.items[idx].description
        return render(request, 'knr_itemdel.html', var)
    else:
        btn = getbutton(request)
        if btn == 'yes':
            del c.items[idx]
            logger.debug('Item deleted', request)
            if not setcalc(request, c):  # pragma: no cover
                return error(request)
            return redirect('knr:itemdeleted')
        return redirect('knr:itemlist')

@require_http_methods(['GET'])
@login_required
def itemmove(request, dir, idx):
    logger.debug('Item move requested', request)
    idx = int(idx)
    c = getcalc(request)
    if not c:  # pragma: no cover
        return error(request)
    if dir == 'u':
        idx -= 1
    if (idx >= len(c.items)) or (idx < 1):
        raise Http404
    c.items[idx - 1], c.items[idx] = c.items[idx], c.items[idx - 1]
    if not setcalc(request,  c):  # pragma: no cover
        return error(request)
    return redirect('knr:itemlist')

@require_http_methods(['GET'])
@login_required
def presets(request):
    logger.debug('Presets requested', request)
    if not request.user.is_superuser:
        return unauth(request)
    from .presets import pl, fo
    Place.objects.filter(uid=None).delete()
    Car.objects.filter(uid=None).delete()
    Formula.objects.filter(uid=None).delete()
    pp = []
    for p in pl:
        pp.append(Place(
            uid=None,
            abbr=p[0],
            name=p[1],
            addr=p[2],
            lat=p[3],
            lon=p[4]))
    Place.objects.bulk_create(pp)
    for f in fo:
        ff = Formula(uid=None, abbr=f[0], name=f[1], flat=f[2])
        ff.save()
        fid = ff.id
        for r in f[3]:
            Rate(formula_id=fid, fuel=r[0], rate=r[1]).save()
    logger.info('Presets restored', request)
    return redirect('knr:mainpage')
