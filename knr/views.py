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

from math import ceil
from pickle import dumps, loads
from xml.sax.saxutils import escape, unescape
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.platypus import Paragraph, SimpleDocTemplate, LongTable, TableStyle, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, gray
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.forms.models import model_to_dict
from django.apps import apps
from django.db.models import Q

from common.glob import INERR, LOCAL_SUBDOMAIN, LOCAL_URL
from common.utils import (
    getbutton, unrequire, famt, c2p, get_xml, new_xml, xmlbool, register_fonts, make_pdf, lim, LOGGER, render)
from common.views import error, unauth
from cache.utils import getasset, setasset
from knr.glob import FUELS
from knr.utils import getvat, findloc, finddist, convi, convf
from knr.forms import (
    PlaceForm, CarForm, FormulaForm, CalcForm, GeneralForm, ServiceForm, ServiceSubform, FlatForm, FlatSubform,
    AdministrativeForm, AdministrativeSubform, TimeForm, TimeSubform, TravelForm, TravelSubform)
from knr.models import Place, Car, Formula, Rate


APP = __package__

APPVERSION = apps.get_app_config(APP).version

CTRIP = ('cons1', 'cons2', 'cons3')


B = 'B'
S = 'S'
I = 'I'
F1 = 'F1'
F2 = 'F2'
F3 = 'F3'
F7 = 'F7'

TYPES = {
    'title': S,
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
    'fuel_price': F2,
}

XML_DEC = {
    'vat_rate': {'unit': 'percentage'},
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
    'fuel_price': {'currency': 'CZK', 'unit': 'per l'},
}

FORM_FIELDS = {
    'general': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
    ),
    'service': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'major_number',
        'rate',
        'minor_number',
        'multiple_number',
        'off10_flag',
        'off30_flag',
        'off30limit5000_flag',
        'off20limit5000_flag',
    ),
    'flat': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'rate',
        'multiple_flag',
        'multiple50_flag',
        'item_note',
        'single_flag',
        'halved_flag',
        'halved_appeal_flag',
        'collection_flag',
    ),
    'administrative': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'number',
        'rate',
    ),
    'time': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'time_number',
        'time_rate',
    ),
    'travel': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'from_name',
        'from_address',
        'from_lat',
        'from_lon',
        'to_name',
        'to_address',
        'to_lat',
        'to_lon',
        'trip_number',
        'trip_distance',
        'time_rate',
        'time_number',
        'car_name',
        'fuel_name',
        'cons1',
        'cons2',
        'cons3',
        'formula_name',
        'flat_rate',
        'fuel_price',
    ),
}

SUBFORM_FIELDS = {
    'general': (
        'description',
        'amount',
        'vat',
        'numerator',
        'denominator',
        'item_note',
    ),
    'service': (
        'description',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'major_number',
        'rate',
        'minor_number',
        'multiple_number',
        'off10_flag',
        'off30_flag',
        'off30limit5000_flag',
        'off20limit5000_flag',
        'basis',
    ),
    'flat': (
        'description',
        'vat',
        'numerator',
        'denominator',
        'rate',
        'multiple_flag',
        'multiple50_flag',
        'basis',
        'item_note',
        'single_flag',
        'halved_flag',
        'halved_appeal_flag',
        'collection_flag',
    ),
    'administrative': (
        'description',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'number',
        'rate',
    ),
    'time': (
        'description',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'time_number',
        'time_rate',
    ),
    'travel': (
        'description',
        'vat',
        'numerator',
        'denominator',
        'item_note',
        'from_name',
        'from_address',
        'from_lat',
        'from_lon',
        'to_name',
        'to_address',
        'to_lat',
        'to_lon',
        'trip_number',
        'trip_distance',
        'time_rate',
        'time_number',
        'car_name',
        'fuel_name',
        'cons1',
        'cons2',
        'cons3',
        'formula_name',
        'flat_rate',
        'fuel_price',
    ),
}

TEXT = 'text'
TYPE = 'type'
PRESEL = 'presel'

SEP = '-' * 95

PRESELS = (
    {
        TEXT: 'Vyberte předvolbu:',
        TYPE: None,
    },
    {
        TEXT: SEP,
        TYPE: None,
    },
    {
        TEXT: 'Soudní poplatek',
        TYPE: 'general',
        PRESEL: {
            'description': 'Zaplacený soudní poplatek',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Záloha na znalecký posudek',
        TYPE: 'general',
        PRESEL: {
            'description': 'Zaplacená záloha na znalecký posudek',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Záloha na svědečné',
        TYPE: 'general',
        PRESEL: {
            'description': 'Zaplacená záloha na svědečné',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Použití motorového vozidla klient',
        TYPE: 'travel',
        PRESEL: {
            'description': 'Náhrada za použití motorového vozidla (klient)',
            'trip_number': 2,
            'time_rate': 0,
            'fuel_name': 'BA95',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Další hotové výdaje klient',
        TYPE: 'general',
        PRESEL: {
            'description': 'Další hotové výdaje (klient)',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: SEP,
        TYPE: None,
    },
    {
        TEXT: 'Odměna za úkony podle AdvT (neplátce DPH)',
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
            'denominator': 1},
    },
    {
        TEXT: 'Paušální odměna podle vyhlášky (neplátce DPH)',
        TYPE: 'flat',
        PRESEL: {
            'description':
            'Paušální odměna za zastupování účastníka podle vyhlášky č. 484/2000 Sb.',
            'multiple_flag': False,
            'multiple50_flag': False,
            'vat': False,
            'numerator': 1,
            'denominator': 1},
    },
    {
        TEXT: 'Paušální odměna stanovená pevnou částkou (neplátce DPH)',
        TYPE: 'general',
        PRESEL: {
            'description':
            'Paušální odměna za zastupování účastníka stanovená pevnou částkou',
            'vat': False,
            'numerator': 1,
            'denominator': 1},
    },
    {
        TEXT: 'Použití motorového vozidla advokát (neplátce DPH)',
        TYPE: 'travel',
        PRESEL: {
            'description': 'Náhrada za použití motorového vozidla (advokát)',
            'trip_number': 2,
            'time_rate': 100,
            'fuel_name': 'BA95',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Další promeškaný čas (neplátce DPH)',
        TYPE: 'time',
        PRESEL: {
            'description': 'Náhrada za promeškaný čas podle advokátního tarifu',
            'time_rate': 100,
            'vat': False,
            'numerator': 1,
            'denominator': 1},
    },
    {
        TEXT: 'Režijní paušál za úkony podle AdvT (neplátce DPH)',
        TYPE: 'administrative',
        PRESEL: {
            'description':
            'Paušální náhrada za úkony právní služby podle advokátního tarifu',
            'rate': 300,
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Další hotové výdaje advokát (neplátce DPH)',
        TYPE: 'general',
        PRESEL: {
            'description': 'Další hotové výdaje (advokát)',
            'vat': False,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: SEP,
        TYPE: None,
    },
    {
        TEXT: 'Odměna za úkony podle AdvT (plátce DPH)',
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
            'denominator': 1,
        },
    },
    {
        TEXT: 'Paušální odměna podle vyhlášky (plátce DPH)',
        TYPE: 'flat',
        PRESEL: {
            'description':
            'Paušální odměna za zastupování účastníka podle vyhlášky č. 484/2000 Sb.',
            'multiple_flag': False,
            'multiple50_flag': False,
            'vat': True,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Paušální odměna stanovená pevnou částkou (plátce DPH)',
        TYPE: 'general',
        PRESEL: {
            'description':
            'Paušální odměna za zastupování účastníka stanovená pevnou částkou',
            'vat': True,
            'numerator': 1,
            'denominator': 1},
    },
    {
        TEXT: 'Použití motorového vozidla advokát (plátce DPH)',
        TYPE: 'travel',
        PRESEL: {
            'description': 'Náhrada za použití motorového vozidla (advokát)',
            'trip_number': 2,
            'time_rate': 100,
            'fuel_name': 'BA95',
            'vat': True,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Další promeškaný čas (plátce DPH)',
        TYPE: 'time',
        PRESEL: {
            'description': 'Náhrada za promeškaný čas podle advokátního tarifu',
            'time_rate': 100,
            'vat': True,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Režijní paušál za úkony podle AdvT (plátce DPH)',
        TYPE: 'administrative',
        PRESEL: {
            'description':
            'Paušální náhrada za úkony právní služby podle advokátního tarifu',
            'rate': 300,
            'vat': True,
            'numerator': 1,
            'denominator': 1,
        },
    },
    {
        TEXT: 'Další hotové výdaje advokát (plátce DPH)',
        TYPE: 'general',
        PRESEL: {
            'description': 'Další hotové výdaje (advokát)',
            'vat': True,
            'numerator': 1,
            'denominator': 1,
        },
    }
)

FIELDS = ('title', 'calculation_note', 'internal_note', 'vat_rate')

IFIELDS = [x for x in TYPES if x not in FIELDS + ('type',)]


class Calculation:

    def __init__(self):
        self.title = ''
        self.calculation_note = ''
        self.internal_note = ''
        self.vat_rate = getvat()
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
        self.from_lat = .0
        self.from_lon = .0
        self.to_name = ''
        self.to_address = ''
        self.to_lat = .0
        self.to_lon = .0
        self.trip_number = 0
        self.trip_distance = 0
        self.time_rate = 0
        self.time_number = 0
        self.car_name = ''
        self.fuel_name = ''
        self.cons1 = .0
        self.cons2 = .0
        self.cons3 = .0
        self.formula_name = ''
        self.flat_rate = .0
        self.fuel_price = .0


def i2d(keys, inp, out):

    for key in keys:
        val = inp.__getattribute__(key)
        typ = TYPES[key]
        if typ == B:
            res = bool(val)
        elif typ == S:
            res = str(val)
        elif typ == I:
            res = int(round(float(c2p(str(val)))))
        else:
            res = float(c2p(str(val)))
        out[key] = res


def d2d(keys, inp, out):

    for key in keys:
        if key in inp:
            val = inp[key]
            typ = TYPES[key]
            try:
                if typ == B:
                    res = bool(val)
                elif typ == S:
                    res = str(val)
                elif typ == I:
                    res = int(round(float(c2p(str(val)))))
                else:
                    res = float(c2p(str(val)))
            except:
                res = str(val)
            out[key] = res


def s2i(keys, inp, out):

    for key in keys:
        ind = inp.find(key)
        if ind:
            typ = TYPES[key]
            if ind.contents:
                val = ind.contents[0].strip()
                try:
                    if typ == B:
                        res = (val == 'true')
                    elif typ == S:
                        res = str(unescape(val))
                    elif typ == I:
                        res = int(round(float(c2p(str(val)))))
                    else:
                        res = float(c2p(str(val)))
                    out.__setattr__(key, res)
                except:
                    pass


def d2i(keys, inp, out):

    for key in keys:
        if key in inp:
            val = inp[key]
            typ = TYPES[key]
            if typ == B:
                res = bool(val)
            elif typ == S:
                res = str(val)
            elif typ == I:
                res = int(round(float(c2p(str(val)))))
            else:
                res = float(c2p(str(val)))
            out.__setattr__(key, res)


AID = '{} {}'.format(APP.upper(), APPVERSION)


def getcalc(request):

    asset = getasset(request, AID)
    if asset:
        try:
            return loads(asset)
        except:  # pragma: no cover
            pass
    setcalc(request, Calculation())
    asset = getasset(request, AID)
    return loads(asset) if asset else None


def setcalc(request, data):

    return setasset(request, AID, dumps(data), timedelta(weeks=10))


def to_xml(calc):

    xml = new_xml('')
    calculation = xml.new_tag('calculation')
    xml.insert(0, calculation)
    calculation['xmlns'] = 'http://' + LOCAL_SUBDOMAIN
    calculation['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    calculation['xsi:schemaLocation'] = (
        'http://{} {}/static/{}-{}.xsd'.format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION))
    calculation['application'] = APP
    calculation['version'] = APPVERSION
    calculation['created'] = datetime.now().replace(microsecond=0).isoformat()
    for key in ('title', 'calculation_note', 'internal_note'):
        tag = xml.new_tag(key)
        tag.insert(0, escape(calc.__getattribute__(key)).strip())
        calculation.insert(len(calculation), tag)
        if tag.name in XML_DEC:  # pragma: no cover
            for key2, val in XML_DEC[tag.name].items():
                tag[key2] = val
    vat_rate = xml.new_tag('vat_rate')
    vat_rate.insert(0, '{:.2f}'.format(calc.vat_rate))
    for key, val in XML_DEC['vat_rate'].items():
        vat_rate[key] = val
    calculation.insert(len(calculation), vat_rate)
    items = xml.new_tag('items')
    calculation.insert(len(calculation), items)
    for itm in calc.items:
        item = xml.new_tag(itm.type)
        items.insert(len(items), item)
        for key in FORM_FIELDS[itm.type]:
            tag = xml.new_tag(key)
            item.insert(len(item), tag)
            if tag.name in XML_DEC:
                for attr, string in XML_DEC[tag.name].items():
                    tag[attr] = string
            val = itm.__getattribute__(key)
            typ = TYPES[key]
            if typ == S:
                res = str(escape(val))
            elif typ == B:
                res = xmlbool(val)
            elif typ == I:
                res = '{:d}'.format(val)
            elif typ[0] == 'F':
                res = '{:.{prec}f}'.format(val, prec=int(typ[1]))
            tag.insert(0, res.strip())
    return str(xml).encode('utf-8') + b'\n'


def from_xml(dat):

    string = get_xml(dat)
    if not string:
        return None, 'Chybný formát souboru'
    tcalc = string.findChild('calculation')
    if not tcalc or (tcalc.has_attr('application')
        and tcalc['application'] != APP):
        return None, 'Soubor nebyl vytvořen touto aplikací'
    calc = Calculation()
    s2i(FIELDS, string, calc)
    items = string.items.children
    for itm in items:
        if not itm.name:  # pragma: no cover
            continue
        item = Item()
        s2i(IFIELDS, itm, item)
        try:  # pragma: no cover
            item.type = str(itm['type'] if itm.has_attr('type') else itm.name)
        except:  # pragma: no cover
            return None, 'Chybný formát souboru'
        calc.items.append(item)
    return calc, None


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    LOGGER.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    calc = getcalc(request)
    if not calc:  # pragma: no cover
        return error(request)
    var = {
        'app': APP,
        'page_title': 'Kalkulace nákladů řízení',
        'errors': False, 'rows': [],
    }
    if request.method == 'GET':
        i2d(FIELDS, calc, var)
        for key in FIELDS:
            var['{}_error'.format(key)] = 'ok'
    else:
        form = CalcForm(request.POST)
        for key in FIELDS:
            var['{}_error'.format(key)] = 'ok'
        d2d(FIELDS, form.data, var)
        button = getbutton(request)
        if button == 'empty':
            calc = Calculation()
            if not setcalc(request, calc):  # pragma: no cover
                return error(request)
            return redirect('knr:mainpage')
        if button == 'load':
            infile = request.FILES.get('load')
            if not infile:
                var['errors'] = True
                var['err_message'] = 'Nejprve zvolte soubor k načtení'
                return render(request, 'knr_mainpage.html', var)
            try:
                dat = infile.read()
                infile.close()
            except:  # pragma: no cover
                raise Exception('Error reading file')
            calc, msg = from_xml(dat)
            if msg:
                var['errors'] = True
                var['err_message'] = msg
                return render(request, 'knr_mainpage.html', var)
            if not setcalc(request, calc):  # pragma: no cover
                return error(request)
            return redirect('knr:mainpage')
        elif button:
            form = CalcForm(request.POST)
            if form.is_valid():
                cld = form.cleaned_data
                d2i(FIELDS, cld, calc)
                if not setcalc(request, calc):  # pragma: no cover
                    return error(request)
                var.update(cld)
                for key in FIELDS:
                    var['{}_error'.format(key)] = 'ok'
                if button == 'edit':
                    return redirect('knr:itemlist')
                if button == 'xml':
                    response = HttpResponse(
                        to_xml(calc),
                        content_type='text/xml; charset=utf-8')
                    response['Content-Disposition'] = 'attachment; filename=Naklady.xml'
                    return response
                if button == 'pdf':

                    register_fonts()

                    style1 = ParagraphStyle(
                        name='STYLE1',
                        fontName='Bookman',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style2 = ParagraphStyle(
                        name='STYLE2',
                        fontName='BookmanB',
                        fontSize=10,
                        leading=11,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style3 = ParagraphStyle(
                        name='STYLE3',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style4 = ParagraphStyle(
                        name='STYLE4',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=10,
                        allowWidows=False,
                        allowOrphans=False)

                    style5 = ParagraphStyle(
                        name='STYLE5',
                        fontName='Bookman',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style6 = ParagraphStyle(
                        name='STYLE6',
                        fontName='Bookman',
                        fontSize=7,
                        leading=9,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)

                    style7 = ParagraphStyle(
                        name='STYLE7',
                        fontName='BookmanI',
                        fontSize=7,
                        leading=9,
                        spaceBefore=1,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)

                    style8 = ParagraphStyle(
                        name='STYLE8',
                        fontName='Bookman',
                        fontSize=8,
                        leading=10,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style9 = ParagraphStyle(
                        name='STYLE9',
                        fontName='BookmanB',
                        fontSize=8, leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style10 = ParagraphStyle(
                        name='STYLE10',
                        fontName='BookmanB',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style11 = ParagraphStyle(
                        name='STYLE11',
                        fontName='Bookman',
                        fontSize=8,
                        leading=9,
                        alignment=TA_RIGHT,
                        allowWidows=False,
                        allowOrphans=False)

                    style12 = ParagraphStyle(
                        name='STYLE12',
                        fontName='BookmanI',
                        fontSize=8,
                        leading=9,
                        spaceBefore=4,
                        spaceAfter=5,
                        leftIndent=8,
                        allowWidows=False,
                        allowOrphans=False)

                    doc1 = (([Paragraph('Kalkulace nákladů řízení'.upper(), style1)],),)
                    if calc.title:
                        doc1[0][0].append(Paragraph(escape(calc.title), style2))
                    tbl1 = LongTable(doc1, colWidths=(483.3,))
                    tbl1.setStyle(
                        TableStyle((
                            ('LINEABOVE', (0, 0), (0, -1), 1, black),
                            ('TOPPADDING', (0, 0), (0, -1), 2),
                            ('LINEBELOW', (-1, 0), (-1, -1), 1, black),
                            ('BOTTOMPADDING', (-1, 0), (-1, -1), 3),
                            ('LEFTPADDING', (0, 0), (-1, -1), 2),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        )))
                    flow = [tbl1, Spacer(0, 36)]
                    if calc.items:
                        doc2 = []
                        for idx in range(len(calc.items)):
                            item = calc.items[idx]
                            temp = [Paragraph('{:d}.'.format(idx + 1), style3)]
                            temp2 = [Paragraph(
                                escape(item.description.upper().replace(' Č. ', ' č. ').replace(' SB.', ' Sb.')),
                                style4)]
                            if item.type == 'service':
                                if item.multiple_number < 2:
                                    temp2.append(Paragraph(
                                        '<b>Hlavních úkonů:</b> {0.major_number:d} &nbsp; <b>Vedlejších úkonů:</b> '
                                        '{0.minor_number:d}'.format(item),
                                        style6))
                                else:
                                    temp2.append(Paragraph(
                                        '<b>Hlavních úkonů:</b> {0.major_number:d} &nbsp; <b>Vedlejších úkonů:</b> '
                                        '{0.minor_number:d} &nbsp; <b>Zastupovaných účastníků:</b> '
                                        '{0.multiple_number:d}'.format(item),
                                        style6))
                            if item.type == 'administrative':
                                temp2.append(Paragraph(
                                    '<b>Počet úkonů:</b> {:d} &nbsp; <b>Sazba:</b> {} Kč'
                                    .format(item.number, convi(item.rate)),
                                    style6))
                            if item.type == 'time':
                                temp2.append(Paragraph(
                                    '<b>Počet započatých půlhodin:</b> {:d} &nbsp; <b>Sazba:</b> {} Kč/půlhodinu'
                                        .format(item.time_number, convi(item.time_rate)),
                                    style6))
                            if item.type == 'travel':
                                temp2.append(Paragraph(
                                    '<b>Z:</b> {} ({})'.format(
                                        escape(item.from_name),
                                        escape(
                                            item.from_address.replace(', Česká republika', '').replace(', Česko', ''))),
                                    style6))
                                temp2.append(Paragraph(
                                    '<b>Do:</b> {} ({})'.format(
                                        escape(item.to_name),
                                        escape(
                                            item.to_address.replace(', Česká republika', '').replace(', Česko', ''))),
                                    style6))
                                temp2.append(Paragraph(
                                    '<b>Vzdálenost:</b> {} km &nbsp; <b>Počet cest:</b> {:d}'
                                    .format(convi(item.trip_distance), item.trip_number),
                                    style6))
                                if item.time_number and item.time_rate:
                                    temp2.append(Paragraph(
                                        '<b>Počet započatých půlhodin:</b> {:d} &nbsp; <b>Sazba:</b> {} Kč/půlhodinu'
                                        .format((item.time_number * item.trip_number), convi(item.time_rate)),
                                        style6))
                                temp2.append(Paragraph('<b>Vozidlo</b> {}'.format(escape(item.car_name)), style6))
                                temp2.append(Paragraph(
                                    '<b>Palivo:</b> {} &nbsp; <b>Průměrná spotřeba:</b> {} l/100 km'
                                    .format(item.fuel_name, convf(((item.cons1 + item.cons2 + item.cons3) / 3), 3)),
                                    style6))
                                temp2.append(Paragraph('<b>Předpis:</b> {}'.format(escape(item.formula_name)), style6))
                                temp2.append(Paragraph(
                                    '<b>Paušál:</b> {} Kč/km &nbsp; <b>Cena paliva:</b> {} Kč/l'
                                    .format(convf(item.flat_rate, 2), convf(item.fuel_price, 2)),
                                    style6))
                            if item.numerator > 1 or item.denominator > 1:
                                temp2.append(Paragraph(
                                    '<b>Zlomek:</b> {0.numerator:d}/{0.denominator:d}'.format(item),
                                    style6))
                            if item.item_note:
                                for temp3 in filter(bool, item.item_note.strip().split('\n')):
                                    temp2.append(Paragraph(escape(temp3), style7))
                            temp.append(temp2)
                            temp.append(Paragraph('{} Kč'.format(convi(item.amount)), style5))
                            doc2.append(temp)
                        tbl2 = LongTable(doc2, colWidths=(16.15, 400.45, 66.7))
                        tbl2.setStyle(
                            TableStyle((
                                ('LINEABOVE', (0, 0), (-1, 0), .25, gray),
                                ('LINEBELOW', (0, 0), (-1, -1), .25, gray),
                                ('VALIGN', (0, 0), (1, -1), 'TOP'),
                                ('VALIGN', (-1, 0), (-1, -1), 'MIDDLE'),
                                ('RIGHTPADDING', (0, 0), (1, -1), 0),
                                ('RIGHTPADDING', (-1, 0), (-1, -1), 2),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('LEFTPADDING', (1, 0), (1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 4),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            )))
                        flow.extend([tbl2, Spacer(0, 24)])
                    total_net = total_ex = 0
                    for itm in calc.items:
                        if itm.vat:
                            total_net += int(itm.amount)
                        else:
                            total_ex += int(itm.amount)
                    total_vat = int(round(float(total_net * calc.vat_rate) / 100))
                    total = int(total_net + total_ex + total_vat)
                    doc3 = []
                    if total_vat:
                        doc3.append(
                            [None,
                             Paragraph('Základ bez DPH', style8),
                             Paragraph('{} Kč'.format(convi(total_ex)), style11)
                            ])
                        doc3.append(
                            [None,
                             Paragraph('Základ s DPH', style8),
                             Paragraph('{} Kč'.format(convi(total_net)), style11)
                            ])
                        doc3.append(
                            [None,
                             Paragraph('DPH {} %'.format(convf(calc.vat_rate, 0)), style8),
                             Paragraph('{} Kč'.format(convi(total_vat)), style11)
                            ])
                    doc3.append(
                        [None,
                         Paragraph('Celkem'.upper(), style9),
                         Paragraph('{} Kč'.format(convi(total)), style10)])
                    tbl3 = LongTable(doc3, colWidths=(346.6, 70, 66.7) if total_vat else (366.6, 50, 66.7))
                    lst3 = [
                        ('LINEABOVE', (1, 0), (-1, 0), 1, black),
                        ('LINEABOVE', (1, -1), (-1, -1), 1, black),
                        ('LINEBELOW', (1, -1), (-1, -1), 1, black),
                        ('RIGHTPADDING', (0, 0), (1, -1), 0),
                        ('RIGHTPADDING', (-1, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (1, 0), (1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), -1),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ]
                    if total_vat:
                        lst3.append(('TOPPADDING', (0, 1), (-1, 2), -3))
                    tbl3.setStyle(TableStyle(lst3))
                    flow.append(KeepTogether([tbl3]))
                    if calc.calculation_note:
                        flow.append(Spacer(0, 24))
                        temp2 = [Paragraph('Poznámka:'.upper(), style4)]
                        for string in filter(bool, calc.calculation_note.strip().split('\n')):
                            temp2.append(Paragraph(escape(string), style12))
                        flow.append(KeepTogether(temp2[:2]))
                        if len(temp2) > 2:
                            flow.extend(temp2[2:])
                    temp = BytesIO()
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename=Naklady.pdf'
                    auth = '{} V{}'.format(APP.upper(), APPVERSION)
                    doc = SimpleDocTemplate(
                        temp,
                        pagesize=A4,
                        title='Kalkulace nákladů řízení',
                        author=auth,
                        leftMargin=64,
                        rightMargin=48,
                        topMargin=48,
                        bottomMargin=96,
                        )
                    make_pdf(
                        doc,
                        flow,
                        string=auth,
                        xml=to_xml(calc))
                    response.write(temp.getvalue())
                    return response
                if button == "place":
                    return redirect('knr:placelist')
                if button == "car":
                    return redirect('knr:carlist')
                if button == "formula":
                    return redirect('knr:formulalist')
            else:
                var.update({'errors': True})
                d2d(FIELDS, form.data, var)
                for key in FIELDS:
                    var['{}_error'.format(key)] = 'err' if form[key].errors else 'ok'
        else:  # pragma: no cover
            i2d(FIELDS, calc, var)
    var['total_net'] = var['total_ex'] = var['num_items'] = 0
    for itm in calc.items:
        var['total_net' if itm.vat else 'total_ex'] += int(itm.amount)
        var['num_items'] += 1
    var['total_vat'] = int(round(float(var['total_net'] * calc.vat_rate) / 100))
    var['total'] = int(var['total_net'] + var['total_ex'] + var['total_vat'])
    for key in ('total_net', 'total_ex', 'total_vat', 'total'):
        var[key] = famt(var[key])
    return render(request, 'knr_mainpage.html', var)


@require_http_methods(('GET', 'POST'))
@login_required
def placeform(request, idx=0):

    LOGGER.debug(
        'Place form accessed using method {}, id={}'
        .format(request.method, idx),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava místa' if idx else 'Nové místo'
    button = getbutton(request)
    if request.method == 'GET':
        form = PlaceForm(initial=model_to_dict(get_object_or_404(Place, pk=idx, uid=uid))) if idx else PlaceForm()
    elif button == 'back':
        return redirect('knr:placelist')
    elif button == 'search':
        form = PlaceForm(request.POST)
        unrequire(form, ('abbr', 'name', 'addr', 'lat', 'lon'))
        loc = findloc(request.POST.get('addr'))
        form.data = form.data.copy()
        if loc:
            form.data['addr'], form.data['lat'], form.data['lon'] = loc
        else:
            form.data['lat'] = form.data['lon'] = ''
            err_message = 'Hledání neúspěšné, prosím, upřesněte adresu'
    else:
        form = PlaceForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                get_object_or_404(Place, pk=idx, uid=uid)
                cld['pk'] = idx
            Place(uid_id=uid, **cld).save()
            LOGGER.info(
                'User "{}" ({:d}) {} place "{}"'.format(uname, uid, 'updated' if idx else 'added', cld['name']),
                request)
            return redirect('knr:placelist')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'knr_placeform.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET',))
@login_required
def placelist(request):

    LOGGER.debug('Place list accessed', request)
    rows = Place.objects.filter(Q(uid=None) | Q(uid=request.user.id)).order_by('uid', 'abbr', 'name')
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


@require_http_methods(('GET', 'POST'))
@login_required
def placedel(request, idx=0):

    LOGGER.debug(
        'Place delete page accessed using method {}, id={}'
        .format(request.method, idx),
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
             'name': get_object_or_404(Place, pk=idx, uid=uid).name})
    else:
        place = get_object_or_404(Place, pk=idx, uid=uid)
        if getbutton(request) == 'yes':
            LOGGER.info('User "{}" ({:d}) deleted place "{}"'.format(uname, uid, place.name), request)
            place.delete()
            return redirect('knr:placedeleted')
        return redirect('knr:placelist')


@require_http_methods(('GET', 'POST'))
@login_required
def carform(request, idx=0):

    LOGGER.debug(
        'Car form accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava vozidla' if idx else 'Nové vozidlo'
    button = getbutton(request)
    if request.method == 'GET':
        form = CarForm(initial=model_to_dict(get_object_or_404(Car, pk=idx, uid=uid))) if idx else CarForm()
    elif button == 'back':
        return redirect('knr:carlist')
    else:
        form = CarForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                get_object_or_404(Car, pk=idx, uid=uid)
                cld['pk'] = idx
            Car(uid_id=uid, **cld).save()
            LOGGER.info(
                'User "{}" ({:d}) {} car "{}"'.format(uname, uid, 'updated' if idx else 'added', cld['name']),
                request)
            return redirect('knr:carlist')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'knr_carform.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'fuels': FUELS})


@require_http_methods(('GET',))
@login_required
def carlist(request):

    LOGGER.debug('Car list accessed', request)
    rows = Car.objects.filter(uid=request.user.id).order_by('abbr', 'name')
    return render(
        request,
        'knr_carlist.html',
        {'app': APP,
         'page_title': 'Přehled vozidel',
         'rows': rows})


@require_http_methods(('GET', 'POST'))
@login_required
def cardel(request, idx=0):

    LOGGER.debug(
        'Car delete page accessed using method {}, id={}'.format(request.method, idx),
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
             'name': get_object_or_404(Car, pk=idx, uid=uid).name})
    else:
        car = get_object_or_404(Car, pk=idx, uid=uid)
        if getbutton(request) == 'yes':
            LOGGER.info('User "{}" ({:d}) deleted car "{}"'.format(uname, uid, car.name), request)
            car.delete()
            return redirect('knr:cardeleted')
        return redirect('knr:carlist')


@require_http_methods(('GET', 'POST'))
@login_required
def formulaform(request, idx=0):

    LOGGER.debug(
        'Formula form accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava předpisu' if idx else 'Nový předpis'
    button = getbutton(request)
    if request.method == 'GET':
        if idx:
            res = model_to_dict(get_object_or_404(Formula, pk=idx, uid=uid))
            for fuel in FUELS:
                rat = Rate.objects.filter(formula=idx, fuel=fuel)
                if rat and rat[0].rate:
                    res['rate_{}'.format(fuel)] = rat[0].rate
            form = FormulaForm(initial=res)
        else:
            form = FormulaForm()
    elif button == 'back':
        return redirect('knr:formulalist')
    else:
        form = FormulaForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                res = get_object_or_404(Formula, pk=idx, uid=uid)
                cld['pk'] = idx
            dct = {}
            for key, val in cld.items():
                if not key.startswith('rate_'):
                    dct[key] = val
            res = Formula(uid_id=uid, **dct)
            res.save()
            LOGGER.info(
                'User "{}" ({:d}) {} formula {}'.format(uname, uid, 'updated' if idx else 'added', res.name),
                request)
            for fuel in FUELS:
                rat = Rate.objects.filter(formula=res, fuel=fuel)
                rat = rat[0] if rat else Rate(formula=res, fuel=fuel)
                rat.rate = cld['rate_{}'.format(fuel)]
                if not rat.rate:
                    rat.rate = 0
                rat.save()
            return redirect('knr:formulalist')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    rates = []
    for fuel in FUELS:
        rates.append(form['rate_{}'.format(fuel)])
    return render(
        request,
        'knr_formulaform.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'rates': rates})


@require_http_methods(('GET',))
@login_required
def formulalist(request):

    LOGGER.debug('Formula list accessed', request)
    rows = Formula.objects.filter(Q(uid=None) | Q(uid=request.user.id)).order_by('uid', 'abbr', 'name')
    for row in rows:
        rates = []
        for fuel in FUELS:
            rat = Rate.objects.filter(formula=row.id, fuel=fuel)
            rates.append(rat[0].rate if rat else 0)
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
         'fuels': FUELS,
         'colspan': len(FUELS) + 4,
         'rows': rows})


@require_http_methods(('GET', 'POST'))
@login_required
def formuladel(request, idx=0):

    LOGGER.debug(
        'Formula delete page accessed using method {}, id={}'.format(request.method, idx),
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
             'name': get_object_or_404(Formula, pk=idx, uid=uid).name})
    else:
        formula = get_object_or_404(Formula, pk=idx, uid=uid)
        if getbutton(request) == 'yes':
            LOGGER.info('User "{}" ({:d}) deleted formula "{}"'.format(uname, uid, formula.name), request)
            formula.delete()
            return redirect('knr:formuladeleted')
        return redirect('knr:formulalist')


@require_http_methods(('GET', 'POST'))
@login_required
def itemform(request, idx=0):

    def addtravellists(var):
        res = Place.objects.filter(Q(uid=None) | Q(uid=uid)).order_by('abbr', 'name')
        lst1 = []
        for obj in res:
            if obj.uid or not res.filter(abbr=obj.abbr, uid=uid):
                lst1.append(
                    {'idx': obj.id,
                     'text': '{0.abbr} – {0.name}'.format(obj)})
        res = Car.objects.filter(uid=uid).order_by('abbr', 'name')
        lst2 = []
        for obj in res:
            lst2.append(
                {'idx': obj.id,
                 'text': '{0.abbr} – {0.name}'.format(obj)})
        res = Formula.objects.filter(Q(uid=None) | Q(uid=uid)).order_by('abbr', 'name')
        lst3 = []
        for obj in res:
            if obj.uid or not res.filter(abbr=obj.abbr, uid=uid):
                lst3.append(
                    {'idx': obj.id,
                     'text': '{0.abbr} – {0.name}'.format(obj)})
        var.update(
            {'sep': '-' * 110,
             'from_sels': lst1,
             'to_sels': lst1,
             'car_sels': lst2,
             'formula_sels': lst3,
             'fuel_names': FUELS})

    def proc_from(sel, cld):
        res = Place.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if res:
            cld['from_name'] = res[0].name
            cld['from_address'] = res[0].addr
            cld['from_lat'] = res[0].lat
            cld['from_lon'] = res[0].lon
            cld['trip_distance'] = cld['time_number'] = ''

    def proc_to(sel, cld):
        res = Place.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if res:
            cld['to_name'] = res[0].name
            cld['to_address'] = res[0].addr
            cld['to_lat'] = res[0].lat
            cld['to_lon'] = res[0].lon
            cld['trip_distance'] = cld['time_number'] = ''

    def proc_car(sel, cld):
        res = Car.objects.filter(pk=sel, uid=uid)
        if res:
            cld['car_name'] = res[0].name
            cld['fuel_name'] = res[0].fuel
            cld['cons1'] = float(res[0].cons1)
            cld['cons2'] = float(res[0].cons2)
            cld['cons3'] = float(res[0].cons3)

    def proc_formula(sel, cld):
        res = Formula.objects.filter(Q(pk=sel) & (Q(uid=None) | Q(uid=uid)))
        if res:
            cld['formula_name'] = res[0].name
            cld['flat_rate'] = float(res[0].flat)
            rat = Rate.objects.filter(formula=sel, fuel=cld['fuel_name'])
            cld['fuel_price'] = float(rat[0].rate) if rat else ''

    def proc_dist(cld):
        cld['trip_distance'] = cld['time_number'] = ''
        res = {}
        d2d(('from_lat', 'from_lon', 'to_lat', 'to_lon'), cld, res)
        if res['from_lat'] and res['from_lon'] and res['to_lat'] and res['to_lon']:
            dist, dur = finddist(res['from_lat'], res['from_lon'], res['to_lat'], res['to_lon'])
            if dist:
                cld['trip_distance'] = int(ceil(dist / 1000))
            if dur:
                cld['time_number'] = int(ceil(dur / 1800))

    LOGGER.debug(
        'Item form accessed using method {}, idx={}'.format(request.method, idx),
        request,
        request.POST)
    uid = request.user.id
    calc = getcalc(request)
    if not calc:  # pragma: no cover
        return error(request)
    var = {'app': APP, 'errors': False}
    if request.method == 'GET':
        if idx:
            idx = int(idx)
            var.update({'idx': idx, 'page_title': 'Úprava položky'})
            if idx > len(calc.items):
                raise Http404
            calc = calc.items[idx - 1]
            i2d(FORM_FIELDS[calc.type], calc, var)
            var['type'] = calc.type
            for key in SUBFORM_FIELDS[calc.type]:
                var['{}_error'.format(key)] = 'ok'
            if var['type'] == 'travel':
                addtravellists(var)
                var['cons_error'] = 'ok'
        else:
            return redirect('knr:itemlist')
    else:
        button = getbutton(request)
        if button == 'back':
            return redirect('knr:itemlist')
        if button == 'new':
            presel = request.POST.get('presel')
            if (presel and presel.isdigit() and int(presel) and int(presel) < len(PRESELS)
                and PRESELS[int(presel)][TYPE]):
                var.update({'idx': 0, 'page_title': 'Nová položka'})
                var.update(PRESELS[int(presel)][PRESEL])
                var['type'] = PRESELS[int(presel)][TYPE]
                for key in SUBFORM_FIELDS[var['type']]:
                    var['{}_error'.format(key)] = 'ok'
                if var['type'] == 'travel':
                    addtravellists(var)
                    var['cons_error'] = 'ok'
            else:
                return redirect('knr:itemlist')
        else:
            typ = str(request.POST.get('type'))
            if typ not in SUBFORM_FIELDS:
                raise Http404
            if typ == 'travel':
                addtravellists(var)
            if request.POST.get('submit'):
                if typ == 'travel':
                    form = TravelSubform(request.POST)
                    if form.is_valid():
                        cld = form.cleaned_data
                        sel = False
                        if request.POST.get('from_sel'):
                            proc_from(int(request.POST.get('from_sel')), cld)
                            sel = True
                        if request.POST.get('to_sel'):
                            proc_to(int(request.POST.get('to_sel')), cld)
                            sel = True
                        if request.POST.get('car_sel'):
                            proc_car(int(request.POST.get('car_sel')), cld)
                            sel = True
                        if request.POST.get('formula_sel'):
                            proc_formula(
                                int(request.POST.get('formula_sel')),
                                cld)
                            sel = True
                        if not (cld['trip_distance'] and cld['time_number']):
                            proc_dist(cld)
                            if cld['trip_distance'] and cld['time_number']:
                                sel = True
                        if sel:
                            idx = cld['idx']
                            var.update({'idx': idx, 'type': typ})
                            var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                            d2d(SUBFORM_FIELDS[typ], cld, var)
                            for key in SUBFORM_FIELDS[typ]:
                                var['{}_error'.format(key)] = 'ok'
                            var['cons_error'] = 'ok'
                        else:
                            form = TravelForm(request.POST)
                            if form.is_valid():
                                cld = form.cleaned_data
                                item = Item()
                                cld['amount'] = int(round(
                                    (cld['trip_distance'] * ((float((cld['cons1'] + cld['cons2'] + cld['cons3'])
                                    * cld['fuel_price']) / 300) + float(cld['flat_rate'])) + (cld['time_number']
                                    * cld['time_rate'])) * cld['trip_number']))
                                if cld['numerator'] > 1 or cld['denominator'] > 1:
                                    cld['amount'] = cld['amount'] * cld['numerator'] / cld['denominator']
                                d2i(FORM_FIELDS[typ], cld, item)
                                item.type = typ
                                idx = cld['idx']
                                if idx:
                                    if idx > len(calc.items):
                                        raise Http404
                                    calc.items[idx - 1] = item
                                else:
                                    calc.items.append(item)
                                if not setcalc(request, calc):
                                    return error(request)  # pragma: no cover
                                return redirect('knr:itemlist')
                            else:
                                idx = int(request.POST.get('idx') or 0)
                                var.update({
                                    'errors': True,
                                    'idx': idx,
                                    'type': typ})
                                var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                                d2d(SUBFORM_FIELDS[typ], form.data, var)
                                for key in SUBFORM_FIELDS[typ]:
                                    var['{}_error'.format(key)] = 'err' if form[key].errors else 'ok'
                                var['cons_error'] = 'ok'
                                for key in CTRIP:
                                    if form[key].errors:
                                        var['cons_error'] = 'err'
                                        break
                    else:
                        raise Http404
                else:
                    form = globals()[typ.title() + 'Form'](request.POST)
                    if form.is_valid():
                        cld = form.cleaned_data
                        item = Item()
                        if typ == 'service':
                            cld['amount'] = (
                                int(round(cld['major_number'] * cld['rate'] + cld['minor_number'] * .5 * cld['rate'])))
                            if cld['off10_flag']:
                                cld['amount'] = int(round(.9 * cld['amount']))
                            if cld['off30_flag']:
                                cld['amount'] = int(round(.7 * cld['amount']))
                            if cld['off30limit5000_flag']:
                                cld['amount'] = min(int(round(.7 * cld['amount'])), 5000)
                            if cld['off20limit5000_flag']:
                                cld['amount'] = min(int(round(.8 * cld['amount'])), 5000)
                            if cld['multiple_number'] > 1:
                                cld['amount'] = int(round(.8 * cld['multiple_number'] * cld['amount']))
                        elif typ == 'flat':
                            cld['amount'] = cld['rate']
                            if cld['collection_flag']:
                                cld['amount'] = max(int(round(.5 * cld['amount'])), 750)
                            if cld['halved_flag']:
                                cld['amount'] = lim(750, int(round(.5
                                    * cld['amount'])), 15000)
                            if cld['halved_appeal_flag']:
                                cld['amount'] = lim(750, int(round(.5
                                    * cld['amount'])), 20000)
                            if cld['single_flag']:
                                cld['amount'] = max(int(round(.5 * cld['amount'])), 400)
                            if cld['multiple_flag']:
                                cld['amount'] = int(round(1.3 * cld['amount']))
                            if cld['multiple50_flag']:
                                cld['amount'] = int(round(1.5 * cld['amount']))
                            cld['amount'] = int(ceil(cld['amount'] / 10) * 10)
                        elif typ == 'administrative':
                            cld['amount'] = cld['number'] * cld['rate']
                        elif typ == 'time':
                            cld['amount'] = cld['time_number'] * cld['time_rate']
                        if cld['numerator'] > 1 or cld['denominator'] > 1:
                            cld['amount'] = (cld['amount'] * cld['numerator']) / cld['denominator']
                        d2i(FORM_FIELDS[typ], cld, item)
                        item.type = typ
                        idx = cld['idx']
                        if idx:
                            if idx > len(calc.items):
                                raise Http404
                            calc.items[idx - 1] = item
                        else:
                            calc.items.append(item)
                        if not setcalc(request, calc):  # pragma: no cover
                            return error(request)
                        return redirect('knr:itemlist')
                    else:
                        idx = int(request.POST.get('idx') or 0)
                        var.update({'errors': True, 'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], form.data, var)
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'err' if form[key].errors else 'ok'
                        var['fraction_error'] = (
                            'err' if form['numerator'].errors or form['denominator'].errors else 'ok')
            else:
                form = globals()[typ.title() + 'Subform'](request.POST)
                if form.is_valid():
                    cld = form.cleaned_data
                    if typ == 'service':
                        bas = cld['basis']
                        if button == 'calc1':
                            if bas <= 500:
                                rat = 250
                            elif bas <= 1000:
                                rat = 500
                            elif bas <= 5000:
                                rat = 750
                            elif bas <= 10000:
                                rat = 1000
                            elif bas <= 200000:
                                rat = 1000 + 25 * int(ceil((bas - 10000) / 1000))
                            elif bas <= 10000000:
                                rat = 5750 + 25 * int(ceil((bas - 200000) / 10000))
                            else:
                                rat = 30250 + 25 * int(ceil((bas - 10000000) / 100000))
                        else:
                            if bas <= 500:
                                rat = 300
                            elif bas <= 1000:
                                rat = 500
                            elif bas <= 5000:
                                rat = 1000
                            elif bas <= 10000:
                                rat = 1500
                            elif bas <= 200000:
                                rat = 1500 + 40 * int(ceil((bas - 10000) / 1000))
                            elif bas <= 10000000:
                                rat = 9100 + 40 * int(ceil((bas - 200000) / 10000))
                            else:
                                rat = 48300 + 40 * int(ceil((bas - 10000000) / 100000))
                        idx = cld['idx']
                        var.update({'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], cld, var)
                        var['rate'] = rat
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'ok'
                    elif typ == 'flat':
                        bas = cld['basis']
                        if button == 'calc1':
                            if bas <= 500:
                                rat = 1500
                            elif bas <= 1000:
                                rat = 3000
                            elif bas <= 5000:
                                rat = 4500
                            elif bas <= 10000:
                                rat = 6000
                            elif bas <= 200000:
                                rat = 6000 + .15 * (bas - 10000)
                            elif bas <= 10000000:
                                rat = 34500 + .015 * (bas - 200000)
                            else:
                                rat = 181500 + .00015 * (bas - 10000000)
                        elif button == 'calc2':
                            if bas <= 1000:
                                rat = 4500
                            elif bas <= 5000:
                                rat = 6000
                            elif bas <= 10000:
                                rat = 9000
                            elif bas <= 200000:
                                rat = 9000 + .17 * (bas - 10000)
                            elif bas <= 10000000:
                                rat = 41300 + .02 * (bas - 200000)
                            else:
                                rat = 237300 + .0015 * (bas - 10000000)
                        else:
                            if bas <= 100:
                                rat = 1000
                            elif bas <= 500:
                                rat = 1500
                            elif bas <= 1000:
                                rat = 2500
                            elif bas <= 2000:
                                rat = 3750
                            elif bas <= 5000:
                                rat = 4800
                            elif bas <= 10000:
                                rat = 7500
                            elif bas <= 200000:
                                rat = 7500 + .17 * (bas - 10000)
                            elif bas <= 10000000:
                                rat = 39800 + .02 * (bas - 200000)
                            else:
                                rat = 235800 + .0015 * (bas - 10000000)
                        rat = int(ceil(rat / 10) * 10)
                        idx = cld['idx']
                        var.update({'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], cld, var)
                        var['rate'] = rat
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'ok'
                    elif typ == 'administrative':
                        rat = 75 if button == 'calc1' else 300
                        idx = cld['idx']
                        var.update({'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], cld, var)
                        var['rate'] = rat
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'ok'
                    elif typ == 'time':
                        rat = 50 if button == 'calc1' else 100
                        idx = cld['idx']
                        var.update({'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], cld, var)
                        var['time_rate'] = rat
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'ok'
                    elif typ == 'travel':
                        if button == 'from_apply' and request.POST.get('from_sel'):
                            proc_from(int(request.POST.get('from_sel')), cld)
                            proc_dist(cld)
                        elif button == 'from_search' and request.POST.get('from_address'):
                            loc = findloc(request.POST.get('from_address'))
                            if loc:
                                cld['from_address'], cld['from_lat'], cld['from_lon'] = loc
                            else:
                                var.update(
                                    {'errors': True,
                                     'err_message': 'Hledání neúspěšné, '
                                     'prosím, upřesněte adresu.'})
                                cld.update({'from_lat': '', 'from_lon': ''})
                            proc_dist(cld)
                        elif button == 'to_apply' and request.POST.get('to_sel'):
                            proc_to(int(request.POST.get('to_sel')), cld)
                            proc_dist(cld)
                        elif button == 'to_search' and request.POST.get('to_address'):
                            loc = findloc(request.POST.get('to_address'))
                            if loc:
                                cld['to_address'], cld['to_lat'], cld['to_lon'] = loc
                            else:
                                var.update(
                                    {'errors': True,
                                     'err_message': 'Hledání neúspěšné, prosím, upřesněte adresu.'})
                                cld.update({'to_lat': '', 'to_lon': ''})
                            proc_dist(cld)
                        elif button == 'calc':
                            proc_dist(cld)
                        elif button == 'calc1':
                            cld['time_rate'] = 50
                        elif button == 'calc2':
                            cld['time_rate'] = 100
                        elif button == 'car_apply' and request.POST.get('car_sel'):
                            proc_car(int(request.POST.get('car_sel')), cld)
                        elif button == 'formula_apply' and request.POST.get('formula_sel'):
                            proc_formula(int(request.POST.get('formula_sel')), cld)
                        idx = cld['idx']
                        var.update({'idx': idx, 'type': typ})
                        var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                        d2d(SUBFORM_FIELDS[typ], cld, var)
                        if not var['fuel_price']:
                            var['fuel_price'] = ''
                        for key in SUBFORM_FIELDS[typ]:
                            var['{}_error'.format(key)] = 'ok'
                        var['cons_error'] = 'ok'
                else:
                    idx = int(request.POST.get('idx') or 0)
                    var.update({'errors': True, 'idx': idx, 'type': typ})
                    var['page_title'] = 'Úprava položky' if idx else 'Nová položka'
                    d2d(SUBFORM_FIELDS[typ], form.data, var)
                    for key in SUBFORM_FIELDS[typ]:
                        var['{}_error'.format(key)] = 'err' if form[key].errors else 'ok'
    return render(request, 'knr_itemform.html', var)


@require_http_methods(('GET', 'POST'))
@login_required
def itemlist(request):

    LOGGER.debug(
        'Item list accessed using method {}'.format(request.method),
        request,
        request.POST)
    calc = getcalc(request)
    if not calc:  # pragma: no cover
        return error(request)
    var = {
        'app': APP,
        'page_title': 'Položky kalkulace',
        'rows': [],
        'presel': [],
    }
    num = 0
    for row in calc.items:
        dct = {
            'idx': num + 1,
            'up': num > 0,
            'down': num < (len(calc.items) - 1),
        }
        i2d(('description', 'amount'), row, dct)
        dct['amount'] = famt(dct['amount'])
        num += 1
        var['rows'].append(dct)
    num = 0
    for presel in PRESELS:
        prn = num if presel[TYPE] else ''
        var['presel'].append({'idx': prn, 'text': presel[TEXT]})
        num += 1
    return render(request, 'knr_itemlist.html', var)


@require_http_methods(('GET', 'POST'))
@login_required
def itemdel(request, idx=0):

    LOGGER.debug(
        'Item delete page accessed using method {}, idx={}'.format(request.method, idx),
        request,
        request.POST)
    idx = int(idx) - 1
    var = {'app': APP, 'page_title': 'Smazání položky'}
    calc = getcalc(request)
    if not calc:  # pragma: no cover
        return error(request)
    if idx >= len(calc.items):
        raise Http404
    if request.method == 'GET':
        var['idx'] = idx
        var['desc'] = calc.items[idx].description
        return render(request, 'knr_itemdel.html', var)
    else:
        button = getbutton(request)
        if button == 'yes':
            del calc.items[idx]
            LOGGER.debug('Item deleted', request)
            if not setcalc(request, calc):  # pragma: no cover
                return error(request)
            return redirect('knr:itemdeleted')
        return redirect('knr:itemlist')


@require_http_methods(('GET',))
@login_required
def itemmove(request, drc, idx):

    LOGGER.debug('Item move requested', request)
    idx = int(idx)
    calc = getcalc(request)
    if not calc:  # pragma: no cover
        return error(request)
    if drc == 'u':
        idx -= 1
    if idx >= len(calc.items) or idx < 1:
        raise Http404
    calc.items[idx - 1], calc.items[idx] = calc.items[idx], calc.items[idx - 1]
    if not setcalc(request, calc):  # pragma: no cover
        return error(request)
    return redirect('knr:itemlist')


@require_http_methods(('GET',))
@login_required
def presets(request):

    LOGGER.debug('Presets requested', request)
    if not request.user.is_superuser:
        return unauth(request)
    from knr.presets import PS_PLACES, PS_FORMULAS
    Place.objects.filter(uid=None).delete()
    Car.objects.filter(uid=None).delete()
    Formula.objects.filter(uid=None).delete()
    lst = []
    for item in PS_PLACES:
        lst.append(Place(
            uid=None,
            abbr=item[0],
            name=item[1],
            addr=item[2],
            lat=item[3],
            lon=item[4]))
    Place.objects.bulk_create(lst)
    for item in PS_FORMULAS:
        formula = Formula(uid=None, abbr=item[0], name=item[1], flat=item[2])
        formula.save()
        fid = formula.id
        for rat in item[3]:
            Rate(formula_id=fid, fuel=rat[0], rate=rat[1]).save()
    LOGGER.info('Presets restored', request)
    return redirect('knr:mainpage')
