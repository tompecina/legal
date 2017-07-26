# -*- coding: utf-8 -*-
#
# hjp/views.py
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

from datetime import date, datetime, timedelta
from calendar import monthrange
from pickle import dumps, loads
from xml.sax.saxutils import escape
import csv
from io import BytesIO
from os.path import join
import reportlab.rl_config
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Table, TableStyle, Spacer, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from django.shortcuts import render, redirect, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.apps import apps
from common.settings import FONT_DIR
from common.utils import (
    getbutton, yfactor, mfactor, odp, formam, xmldecorate, xmlescape,
    xmlunescape, Lf, getXML, newXML, iso2date, CanvasXML, logger)
from common.glob import ydconvs, mdconvs, LIM, inerr, localsubdomain, localurl
from common.views import error
from cache.main import getasset, setasset
from cnb.main import getMPIrate
from hjp.forms import MainForm, TransForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version


class Debt(object):

    def __init__(self):
        self.title = ''
        self.note = ''
        self.internal_note = ''
        self.currency = 'CZK'
        self.rounding = 0
        self.interest = Interest()
        self.transactions = []
        self.rates = {}


class Interest(object):

    def __init__(self):
        self.model = 'none'


class Transaction(object):

    pass


aid = '{} {}'.format(APP.upper(), APPVERSION)


def getdebt(request):

    a = getasset(request, aid)
    if a:
        try:
            return loads(a)
        except:  # pragma: no cover
            pass
    setdebt(request, Debt())
    a = getasset(request, aid)
    return loads(a) if a else None


def setdebt(request, data):

    return setasset(request, aid, dumps(data), timedelta(weeks=10))


def dispcurr(curr):

    return 'Kč' if (curr == 'CZK') else curr


def calcint(pastdate, presdate, principal, debt, default_date):

    interest = debt.interest

    if interest.model == 'none':
        return (0.0, None)

    if interest.model == 'fixed':
        return ((0.0 if pastdate else interest.fixed_amount), None)

    if (not pastdate) or (pastdate > presdate):
        return (None, 'Chybný interval')

    if pastdate < (default_date - odp):
        pastdate = default_date - odp

    if pastdate >= presdate:
        return (0.0, None)

    if interest.model == 'per_annum':
        return ((principal * yfactor(pastdate, presdate, \
               interest.day_count_convention) * interest.rate / 100.0), None)

    if interest.model == 'per_mensem':
        return ((principal * mfactor(pastdate, presdate, \
               interest.day_count_convention) * interest.rate / 100.0), None)

    if interest.model == 'per_diem':
        return ((principal * (presdate - pastdate).days * \
               interest.rate / 1000.0), None)

    if interest.model == 'cust1':
        r = getMPIrate('DISC', default_date)
        if r[1]:
            return (None, r[1])
        debt.rates[default_date] = r[0]
        return ((principal * yfactor(pastdate, presdate, 'ACT/ACT') * \
                 r[0] / 50.0), None)

    if interest.model == 'cust2':
        s = 0.0
        t = pastdate
        while True:
            t += odp
            y1 = t.year
            m1 = t.month
            d1 = 1
            if m1 > 6:
                m1 = 7
            else:
                m1 = 1
            r = getMPIrate('REPO', date(y1, m1, d1))
            if r[1]:
                return (None, r[1])
            debt.rates[date(y1, m1, d1)] = r[0]
            y2 = y1
            if (y1 < presdate.year) or ((m1 == 1) and (presdate.month > 6)):
                if m1 == 1:
                    m2 = 6
                    d2 = 30
                else:
                    m2 = 12
                    d2 = 31
                nt = date(y2, m2, d2)
                s += yfactor((t - odp), nt, 'ACT/ACT') * (r[0] + 7.0)
                t = nt
            else:
                m2 = presdate.month
                d2 = presdate.day
                return ((principal * (s + yfactor((t - odp), date(y2, m2, d2), \
                       'ACT/ACT') * (r[0] + 7.0)) / 100.0), None)

    if interest.model == 'cust3':
        y = default_date.year
        m = default_date.month
        d = default_date.day
        if m > 6:
            m = 6
            d = 30
        else:
            m = 12
            d = 31
            y -= 1
        r = getMPIrate('REPO', date(y, m, d))
        if r[1]:
            return (None, r[1])
        debt.rates[date(y, m, d)] = r[0]
        return ((principal * yfactor(pastdate, presdate, 'ACT/ACT') * \
               (r[0] + 7.0) / 100.0), None)

    if interest.model == 'cust5':
        y = default_date.year
        m = default_date.month
        d = default_date.day
        if m > 6:
            m = 6
            d = 30
        else:
            m = 12
            d = 31
            y -= 1
        r = getMPIrate('REPO', date(y, m, d))
        if r[1]:
            return (None, r[1])
        debt.rates[date(y, m, d)] = r[0]
        return ((principal * yfactor(pastdate, presdate, 'ACT/ACT') * \
               (r[0] + 8.0) / 100.0), None)

    if interest.model == 'cust6':
        y = default_date.year
        m = default_date.month
        if m > 6:
            m = 7
        else:
            m = 1
        r = getMPIrate('REPO', date(y, m, 1))
        if r[1]:
            return (None, r[1])
        debt.rates[date(y, m, 1)] = r[0]
        return ((principal * yfactor(pastdate, presdate, 'ACT/ACT') * \
               (r[0] + 8.0) / 100.0), None)

    if interest.model == 'cust4':
        return ((principal * (presdate - pastdate).days * .0025), None)

    return (None, 'Neznámý model')


def getrows(debt):

    if not debt.transactions:
        return []

    if debt.interest.model == 'cust4':
        return getrows4(debt)

    st = debt.transactions[:]
    id = 1
    for tt in st:
        tt.id = id
        id += 1
    st.sort(key=(lambda x: x.transaction_type), reverse=True)
    st.sort(key=(lambda x: x.date))

    rows = []
    principal = interest = 0.0
    cud = None
    err = False
    for tt in st:
        if tt.transaction_type == 'debit':
            default_date = (tt.date + odp)
            break
    else:
        default_date = None
    debt.default_date = default_date

    for tt in st:
        row = {}
        am = (round(tt.amount, debt.rounding) if hasattr(tt, 'amount') else 0.0)
        row['id'] = tt.id
        row['date'] = tt.date
        row['description'] = tt.description
        row['trt'] = trt = tt.transaction_type
        if trt == 'credit':
            row['rep'] = \
            ('jistina' if (tt.repayment_preference == 'principal') else 'úrok')
        if trt == 'debit':
            row['change'] = am
        elif trt == 'credit':
            row['change'] = -am
        else:
            row['change'] = 0.0
        if not err:
            op = principal
            oi = interest
            if (cud and (debt.interest.model != 'none') and \
                (principal > 0)) or (debt.interest.model == 'fixed'):
                i = calcint(cud, tt.date, principal, debt, default_date)
                if i[1]:
                    err = True
                    row['msg'] = i[1]
                else:
                    interest += round(i[0], debt.rounding)
            if trt != 'balance':
                row['pre_principal'] = principal
                row['pre_interest'] = interest
                row['pre_total'] = (principal + interest)
            else:
                row['pre_principal'] = \
                row['pre_interest'] = \
                row['pre_total'] = 0.0
            if trt == 'debit':
                cp = -am
                ci = 0
            elif trt == 'credit':
                if tt.repayment_preference == 'principal':
                    cp = (principal if (am > principal) else am)
                    am -= cp
                    ci = (interest if (am > interest) else am)
                    am -= ci
                    if am:
                        principal -= am
                else:
                    ci = (interest if (am > interest) else am)
                    am -= ci
                    cp = am
            else:
                cp = ci = 0.0
            principal -= cp
            interest -= ci
            row['change_principal'] = -cp
            row['change_interest'] = -ci
            row['post_principal'] = principal
            row['post_interest'] = interest
            row['post_total'] = (principal + interest)
            if trt == 'balance':
                principal = op
                interest = oi
            else:
                cud = tt.date

        row['err'] = err
        rows.append(row)

    return rows


def getrows4(debt):

    if not debt.transactions:
        return []

    mm = (25.0 if (debt.currency == 'CZK') else 0.0)

    st = debt.transactions[:]
    id = 1
    for tt in st:
        tt.id = id
        id += 1
    st.sort(key=(lambda x: x.transaction_type), reverse=True)
    st.sort(key=(lambda x: x.date))

    for tt in st:
        if tt.transaction_type == 'debit':
            default_date = (tt.date + odp)
            break
    else:
        default_date = None
    debt.default_date = default_date

    rows = []
    err = ''
    principal = interest = 0.0
    mb = default_date
    ui = li = 0.0
    dt = st[0].date
    e = 0
    while dt <= st[-1].date:
        if dt == mb:
            li = 0.0
            ui = mm
        ii = (principal * 0.0025)
        if ii < 0.0:
            ii = 0.0
        li += ii
        if li > ui:
            di = (li - ui)
            ui = li
        else:
            di = 0
        if dt == mb:
            di += mm
            d = default_date.day
            m = (dt.month + 1)
            y = dt.year
            if m > 12:
                m = 1
                y += 1
            d = min(d, monthrange(y, m)[1])
            mb = date(y, m, d)

        interest += di
        while (e < len(st)) and (st[e].date == dt):
            tt = st[e]
            row = {}
            row['id'] = tt.id
            row['date'] = dt
            row['description'] = tt.description
            am = (round(st[e].amount, debt.rounding) \
                  if hasattr(st[e], 'amount') else 0.0)
            row['change'] = (am if (st[e].transaction_type == 'debit') else -am)
            row['trt'] = tt.transaction_type
            if tt.transaction_type != 'balance':
                row['pre_principal'] = principal
                row['pre_interest'] = interest
                row['pre_total'] = (principal + interest)
            if st[e].transaction_type == 'debit':
                principal += am
                cp = -am
                ci = 0
            elif st[e].transaction_type == 'credit':
                if st[e].repayment_preference == 'principal':
                    cp = (principal if (am > principal) else am)
                    am -= cp
                    ci = (interest if (am > interest) else am)
                    am -= ci
                    if am:
                        principal -= am
                else:
                    ci = (interest if (am > interest) else am)
                    am -= ci
                    cp = am
                principal -= cp
                interest -= ci
            else:
                cp = ci = 0.0

            if tt.transaction_type == 'credit':
                row['rep'] = ('jistina' \
                    if (tt.repayment_preference == 'principal') else 'úrok')
            if tt.transaction_type != 'balance':
                row['change_principal'] = -cp
                row['change_interest'] = -ci
            else:
                row['pre_principal'] = \
                row['pre_interest'] = \
                row['pre_total'] = \
                row['change_principal'] = \
                row['change_interest'] = 0.0
            row['post_principal'] = principal
            row['post_interest'] = interest
            row['post_total'] = principal + interest
            row['err'] = err
            rows.append(row)
            e += 1

        dt += odp

    return rows


def toxml(debt):

    xd = {
        'debt': {
            'xmlns': 'http://' + localsubdomain,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd' \
                .format(localsubdomain, localurl, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        },
        'currency': {'standard': 'ISO 4217'},
        'pa_rate': {'unit': 'percent per annum'},
        'pm_rate': {'unit': 'percent per month'},
        'pd_rate': {'unit': 'per mil per day'}
    }
    xml = newXML('')
    d = xmldecorate(xml.new_tag('debt'), xd)
    xml.append(d)
    for tt in ['title', 'note', 'internal_note']:
        tag = xml.new_tag(tt)
        tag.append(xmlescape(debt.__getattribute__(tt)))
        d.append(tag)
    tag = xmldecorate(xml.new_tag('currency'), xd)
    tag.append(debt.currency)
    d.append(tag)
    tag = xml.new_tag('rounding')
    tag.append(str(debt.rounding))
    d.append(tag)
    i = xml.new_tag('interest')
    interest = debt.interest
    m = interest.model
    i['model'] = m
    if m == 'fixed':
        tag = xml.new_tag('amount')
        tag.append('{:.2f}'.format(interest.fixed_amount))
        i.append(tag)
    elif m == 'per_annum':
        tag = xmldecorate(xml.new_tag('pa_rate'), xd)
        tag.append('{:.6f}'.format(interest.rate))
        i.append(tag)
    elif m == 'per_mensem':
        tag = xmldecorate(xml.new_tag('pm_rate'), xd)
        tag.append('{:.6f}'.format(interest.rate))
        i.append(tag)
    elif m == 'per_diem':
        tag = xmldecorate(xml.new_tag('pd_rate'), xd)
        tag.append('{:.6f}'.format(interest.rate))
        i.append(tag)
    if m in ['per_annum', 'per_mensem']:
        tag = xml.new_tag('day_count_convention')
        tag.append(interest.day_count_convention)
        i.append(tag)
    d.append(i)
    ts = xml.new_tag('transactions')
    for tt in debt.transactions:
        t = xml.new_tag(tt.transaction_type)
        tag = xml.new_tag('description')
        tag.append(xmlescape(tt.description))
        t.append(tag)
        tag = xml.new_tag('date')
        tag.append(tt.date.isoformat())
        t.append(tag)
        if hasattr(tt, 'amount'):
            tag = xml.new_tag('amount')
            tag.append('{:.2f}'.format(tt.amount))
            t.append(tag)
        if hasattr(tt, 'repayment_preference'):
            tag = xml.new_tag('repayment_preference')
            tag.append(tt.repayment_preference)
            t.append(tag)
        ts.append(t)
    d.append(ts)
    return str(xml).encode('utf-8') + b'\n'


def fromxml(d):

    s = getXML(d)
    if not s:
        return None, 'Chybný formát souboru'
    h = s.debt
    assert h and (h['application'] == APP)
    debt = Debt()
    debt.title = xmlunescape(h.title.text.strip())
    debt.note = xmlunescape(h.note.text.strip())
    debt.internal_note = xmlunescape(h.internal_note.text.strip())
    debt.rounding = int(h.rounding.text.strip())
    debt.currency = h.currency.text.strip()
    interest = Interest()
    debt.interest = interest
    i = h.interest
    interest.model = m = i['model']
    if m == 'fixed':
        interest.fixed_amount = float(i.amount.text.strip())
    elif m == 'per_annum':
        interest.rate = float(i.pa_rate.text.strip())
        interest.day_count_convention = i.day_count_convention.text.strip()
    elif m == 'per_mensem':
        interest.rate = float(i.pm_rate.text.strip())
        interest.day_count_convention = i.day_count_convention.text.strip()
    elif m == 'per_diem':
        interest.rate = float(i.pd_rate.text.strip())
    for tt in h.transactions.children:
        if not tt.name:
            continue
        transaction = Transaction()
        debt.transactions.append(transaction)
        transaction.description = xmlunescape(tt.description.text.strip())
        transaction.transaction_type = str(tt.name)
        transaction.date = iso2date(tt.date)
        if transaction.transaction_type != 'balance':
            transaction.amount = float(tt.amount.text.strip())
        if transaction.transaction_type == 'credit':
            transaction.repayment_preference = \
                tt.repayment_preference.text.strip()
    return debt, None


@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    def cellam(a, slb=False):
        a = (float(a) if debt.rounding else int(round(a)))
        s = ('s' if slb else '')
        if abs(a) < LIM:
            return '<td class="cr{}"></td>'.format(s)
        if a > 0.0:
            return '<td class="cr{}">{}</td>'.format(s, formam(a))
        return '<td class="dr{}">{}</td>'.format(s, formam(-a))

    def fa(a):
        return formam(round(a, debt.rounding) if debt.rounding else \
                      int(round(a))).replace('-', '−') + '&nbsp;' + \
                      dispcurr(debt.currency)

    err_message = ''
    rows_err = False

    if request.method == 'GET':
        debt = getdebt(request)
        if not debt:  # pragma: no cover
            return error(request)
        debt.rates = {}

        rows = getrows(debt)
        for row in rows:
            if row['err']:
                rows_err = True
                break

        var = {'title': debt.title,
               'note': debt.note,
               'internal_note': debt.internal_note,
               'currency': debt.currency,
               'rounding': str(debt.rounding)}
        i = debt.interest
        var['model'] = m = i.model
        if m == 'fixed':
            var['fixed_amount'] = ('{:.2f}'.format(Lf(i.fixed_amount)) \
                if debt.rounding else int(round(i.fixed_amount)))
        elif m == 'per_annum':
            var['pa_rate'] = i.rate
            var['ydconv'] = i.day_count_convention
        elif m == 'per_mensem':
            var['pm_rate'] = i.rate
            var['mdconv'] = i.day_count_convention
        elif m == 'per_diem':
            var['pd_rate'] = i.rate

        f = MainForm(initial=var)

    else:
        btn = getbutton(request)

        if btn == 'empty':
            debt = Debt()
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:mainpage')

        if btn == 'load':
            f = request.FILES.get('load')
            if not f:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                try:
                    d = f.read()
                    f.close()
                    debt, m = fromxml(d)
                    if m:
                        raise Exception('Error reading file')
                    setdebt(request, debt)
                    return redirect('hjp:mainpage')
                except:
                    err_message = 'Chyba při načtení souboru'

        debt = getdebt(request)
        if not debt:  # pragma: no cover
            return error(request)
        debt.rates = {}
        rows = getrows(debt)
        for row in rows:
            if row['err']:
                rows_err = True
                break

        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            debt.title = cd['title'].strip()
            debt.note = cd['note'].strip()
            debt.internal_note = cd['internal_note'].strip()
            debt.currency = cd['currency']
            debt.rounding = int(cd['rounding'])
            interest = Interest()
            debt.interest = interest
            interest.model = m = cd['model']
            if m == 'fixed':
                interest.fixed_amount = float(cd['fixed_amount'])
            elif m == 'per_annum':
                interest.rate = float(cd['pa_rate'])
                interest.day_count_convention = cd['ydconv']
            elif m == 'per_mensem':
                interest.rate = float(cd['pm_rate'])
                interest.day_count_convention = cd['mdconv']
            elif m == 'per_diem':
                interest.rate = float(cd['pd_rate'])
            setdebt(request, debt)

            if (not btn) and cd['next']:
                return redirect(cd['next'])

            if btn == 'xml':
                response = HttpResponse(
                    toxml(debt),
                    content_type='text/xml; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.xml'
                return response

            if (btn == 'csv') and not rows_err:
                response = \
                    HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.csv'
                writer = csv.writer(response)
                writer.writerow(
                    ['Datum',
                     'Popis',
                     'Přednost',
                     'Pohyb',
                     'Předchozí zůstatek/jistina',
                     'Předchozí zůstatek/úrok',
                     'Předchozí zůstatek/celkem',
                     'Započteno/jistina',
                     'Započteno/úrok',
                     'Nový zůstatek/jistina',
                     'Nový zůstatek/úrok',
                     'Nový zůstatek/celkem'])
                for row in rows:
                    writer.writerow(
                        [row['date'].isoformat(),
                         row['description'],
                         row.get('rep', ''),
                         '{:.2f}'.format(row['change']),
                         '{:.2f}'.format(row['pre_principal']),
                         '{:.2f}'.format(row['pre_interest']),
                         '{:.2f}'.format(row['pre_total']),
                         '{:.2f}'.format(row['change_principal']),
                         '{:.2f}'.format(row['change_interest']),
                         '{:.2f}'.format(row['post_principal']),
                         '{:.2f}'.format(row['post_interest']),
                         '{:.2f}'.format(row['post_total'])])
                return response

            if btn == 'pdf':

                def page1(c, d):
                    c.saveState()
                    c.setFont('Bookman', 7)
                    c.drawString(
                        64.0,
                        48.0,
                        '{} V{}'.format(APP.upper(), APPVERSION))
                    c.setFont('BookmanI', 7)
                    today = date.today()
                    c.drawRightString(
                        (A4[0] - 48.0),
                        48.0,
                        'Vytvořeno: {:d}. {:d}. {:d}' \
                            .format(today.day, today.month, today.year))
                    c.restoreState()

                def page2(c, d):
                    page1(c, d)
                    c.saveState()
                    c.setFont('Bookman', 8)
                    c.drawCentredString((A4[0] / 2),
                                        (A4[1] - 30),
                                        '– {:d} –'.format(d.page))
                    c.restoreState()

                reportlab.rl_config.warnOnMissingFontGlyphs = 0

                registerFont(TTFont(
                    'Bookman',
                    join(FONT_DIR, 'URWBookman-Regular.ttf')))

                registerFont(TTFont(
                    'BookmanB',
                    join(FONT_DIR, 'URWBookman-Bold.ttf')))

                registerFont(TTFont(
                    'BookmanI',
                    join(FONT_DIR, 'URWBookman-Italic.ttf')))

                registerFont(TTFont(
                    'BookmanBI',
                    join(FONT_DIR, 'URWBookman-BoldItalic.ttf')))

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

                s4 = ParagraphStyle(
                    name='S4',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
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

                s13 = ParagraphStyle(
                    name='S13',
                    fontName='Bookman',
                    fontSize=8,
                    leading=12,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                s14 = ParagraphStyle(
                    name='S14',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=12,
                    allowWidows=False,
                    allowOrphans=False)

                s15 = ParagraphStyle(
                    name='S15',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                s16 = ParagraphStyle(
                    name='S16',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                s17 = ParagraphStyle(
                    name='S17',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    alignment=TA_RIGHT,
                    allowWidows=False,
                    allowOrphans=False)

                s18 = ParagraphStyle(
                    name='S18',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    allowWidows=False,
                    allowOrphans=False)

                s19 = ParagraphStyle(
                    name='S19',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    allowWidows=False,
                    allowOrphans=False)

                s20 = ParagraphStyle(
                    name='S20',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    leftIndent=8,
                    allowWidows=False,
                    allowOrphans=False)

                s21 = ParagraphStyle(
                    name='S21',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    leftIndent=16,
                    allowWidows=False,
                    allowOrphans=False)

                s22 = ParagraphStyle(
                    name='S22',
                    fontName='BookmanI',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                d1 = [[[Paragraph('Historie peněžité pohledávky'.upper(), s1)]]]
                if debt.title:
                    d1[0][0].append(Paragraph(escape(debt.title), s2))
                t1 = Table(d1, colWidths=[483.30])
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

                w = 483.30
                wl = 8.0
                wr = 8.0
                wg = 12.0
                wf = wc = ((w - wl - wr - (wg * 2.0)) / 6.0)
                cw = [wl] + ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wg] + \
                     ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wg] + \
                     ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wr]

                tl = 0.5

                r = [Paragraph(('<b>Měna:</b> {}'.format(debt.currency)), s19)]
                if hasattr(debt, 'default_date') and debt.default_date:
                    r.append(Paragraph(
                        '<b>První den prodlení:</b> {:%d.%m.%Y}' \
                            .format(debt.default_date),
                        s19))
                i2 = None
                i3 = []
                if debt.interest.model == 'none':
                    i1 = 'bez úroku'
                elif debt.interest.model == 'fixed':
                    i1 = 'pevnou částkou {}' \
                             .format(fa(debt.interest.fixed_amount))
                elif debt.interest.model == 'per_annum':
                    i1 = 'pevnou sazbou {:n} % <i>p. a.</i>, ' \
                         'konvence pro počítání dnů: {}' \
                             .format(debt.interest.rate,
                                     debt.interest.day_count_convention)
                elif debt.interest.model == 'per_mensem':
                    i1 = 'pevnou sazbou {:n} % <i>p. m.</i>, ' \
                         'konvence pro počítání dnů: {}' \
                             .format(debt.interest.rate,
                                     debt.interest.day_count_convention)
                elif debt.interest.model == 'per_diem':
                    i1 = 'pevnou sazbou {:n} ‰ <i>p. d.</i>' \
                             .format(debt.interest.rate)
                elif debt.interest.model == 'cust1':
                    i1 = 'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                         '(účinnost do 27.04.2005)'
                    if debt.rates:
                        rt = debt.rates.popitem()
                        i2 = 'Diskontní sazba ČNB ke dni {:%d.%m.%Y}: {:.2f}' \
                             ' % <i>p. a.</i>'.format(rt[0], Lf(rt[1]))
                elif debt.interest.model == 'cust2':
                    i1 = 'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                         '(účinnost od 28.04.2005 do 30.06.2010)'
                    if len(debt.rates) == 1:
                        rt = debt.rates.popitem()
                        i2 = 'Použita 2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                             ' {:.2f} % <i>p. a.</i>'.format(rt[0], Lf(rt[1]))
                    elif len(debt.rates) > 1:
                        i2 = 'Použity následující 2T repo sazby ČNB:'
                        for dt in sorted(debt.rates.keys()):
                            i3.append(
                                '– ke dni {:%d.%m.%Y}: {:.2f} % <i>p. a.</i>' \
                                    .format(dt, Lf(debt.rates[dt])))
                elif debt.interest.model == 'cust3':
                    i1 = 'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                         '(účinnost od 01.07.2010 do 30.06.2013)'
                    if debt.rates:
                        rt = debt.rates.popitem()
                        i2 = '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                             ' {:.2f} % <i>p. a.</i>'.format(rt[0], Lf(rt[1]))
                elif debt.interest.model == 'cust5':
                    i1 = 'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                         '(účinnost od 01.07.2013 do 31.12.2013)'
                    if debt.rates:
                        rt = debt.rates.popitem()
                        i2 = '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                             ' {:.2f} % <i>p. a.</i>'.format(rt[0], Lf(rt[1]))
                elif debt.interest.model == 'cust6':
                    i1 = 'úrok z prodlení podle nařízení č. 351/2013 Sb.'
                    if debt.rates:
                        rt = debt.rates.popitem()
                        i2 = '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                             ' {:.2f} % <i>p. a.</i>'.format(rt[0], Lf(rt[1]))
                else:
                    i1 = 'poplatek z prodlení podle nařízení č. 142/1994 Sb.'
                    if debt.currency != 'CZK':
                        i2 = '<i>(minimální sazba 25 Kč za každý ' \
                             'započatý měsíc prodlení není pro jinou ' \
                             'měnu než CZK podporována)</i>'

                r.append(Paragraph('<b>Úročení:</b> {}'.format(i1), s19))
                if i2:
                    r.append(Paragraph(i2, s20))
                for i in i3:
                    r.append(Paragraph(i, s21))
                r.append(Spacer(0, 50))
                flow.extend(r)


                bst = [('SPAN', (0, 0), (4, 0)),
                       ('SPAN', (5, 0), (33, 0)),
                       ('SPAN', (1, 1), (10, 1)),
                       ('SPAN', (12, 1), (21, 1)),
                       ('SPAN', (23, 1), (32, 1)),
                       ('SPAN', (1, 2), (3, 2)),
                       ('SPAN', (4, 2), (10, 2)),
                       ('SPAN', (12, 2), (14, 2)),
                       ('SPAN', (15, 2), (21, 2)),
                       ('SPAN', (23, 2), (25, 2)),
                       ('SPAN', (26, 2), (32, 2)),
                       ('SPAN', (1, 3), (3, 3)),
                       ('SPAN', (4, 3), (10, 3)),
                       ('SPAN', (12, 3), (14, 3)),
                       ('SPAN', (15, 3), (21, 3)),
                       ('SPAN', (23, 3), (25, 3)),
                       ('SPAN', (26, 3), (32, 3)),
                       ('SPAN', (1, 4), (3, 4)),
                       ('SPAN', (4, 4), (10, 4)),
                       ('SPAN', (12, 4), (14, 4)),
                       ('SPAN', (15, 4), (21, 4)),
                       ('SPAN', (23, 4), (25, 4)),
                       ('SPAN', (26, 4), (32, 4)),
                       ('LINEABOVE', (0, 0), (-1, 0), 1, black),
                       ('LINEBELOW', (0, 0), (-1, 0), 1, black),
                       ('LINEBEFORE', (0, 0), (0, -1), 1, black),
                       ('LINEAFTER', (-1, 0), (-1, -1), 1, black),
                       ('LINEBELOW', (0, -1), (-1, -1), 1, black),
                       ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                       ('VALIGN', (0, 0), (-1, 0), 'TOP'),
                       ('LEFTPADDING', (0, 0), (-1, 0), 0),
                       ('LEFTPADDING', (0, 1), (-1, -1), 3),
                       ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                       ('RIGHTPADDING', (4, 2), (10, 4), 0),
                       ('RIGHTPADDING', (15, 2), (21, 4), 0),
                       ('RIGHTPADDING', (26, 2), (32, 4), 0),
                       ('TOPPADDING', (0, 0), (-1, 0), 2.5),
                       ('TOPPADDING', (0, 1), (-1, 1), 10),
                       ('TOPPADDING', (0, 2), (-1, -1), 0),
                       ('BOTTOMPADDING', (0, 0), (-1, 0), 0.5),
                       ('BOTTOMPADDING', (0, 1), (-1, 1), 1.5),
                       ('BOTTOMPADDING', (0, 2), (-1, 4), 0),
                       ('BOTTOMPADDING', (0, -1), (-1, -1), 18),
                      ]

                ast = {
                    'debit': [
                        ('LINEBELOW', (1, 1), (10, 1), tl, black),
                        ('LINEAFTER', (3, 2), (3, 2), tl, black),
                        ('LINEBELOW', (12, 1), (21, 1), tl, black),
                        ('LINEAFTER', (14, 2), (14, 4), tl, black),
                        ('LINEBELOW', (23, 1), (32, 1), tl, black),
                        ('LINEAFTER', (25, 2), (25, 4), tl, black)],
                    'credit': [
                        ('LINEBELOW', (1, 1), (10, 1), tl, black),
                        ('LINEAFTER', (3, 2), (3, 4), tl, black),
                        ('LINEBELOW', (12, 1), (21, 1), tl, black),
                        ('LINEAFTER', (14, 2), (14, 4), tl, black),
                        ('LINEBELOW', (23, 1), (32, 1), tl, black),
                        ('LINEAFTER', (25, 2), (25, 4), tl, black)],
                    'balance': [
                        ('LINEBELOW', (23, 1), (32, 1), tl, black),
                        ('LINEAFTER', (25, 2), (25, 4), tl, black)]}

                for row in rows:
                    if row['err']:
                        flow.extend(
                            [Spacer(0, 20),
                             Paragraph(
                                 '(pro další transakce nejsou k disposici' \
                                 ' data, při výpočtu došlo k chybě)', s22)])
                        break
                    trt = row['trt']
                    d3 = []
                    r = [Paragraph('{:%d.%m.%Y}'.format(row['date']), s13)] \
                        + ([''] * 4)
                    q = [Paragraph(escape(row['description']).upper(), s14)] + \
                        ([''] * 28)
                    d3.extend([r + q])

                    if trt == 'debit':
                        r = ['', Paragraph('Závazek', s15)] \
                            + ([''] * 10) \
                            + [Paragraph('Předchozí zůstatek', s15)] \
                            + ([''] * 10) \
                            + [Paragraph('Nový zůstatek', s15), '']
                    elif trt == 'credit':
                        r = ['', Paragraph('<b>Splátka</b> (přednost {}' \
                                    .format(row['rep']), s16)] \
                            + ([''] * 10) \
                            + [Paragraph('Předchozí zůstatek', s15)] \
                            + ([''] * 10) \
                            + [Paragraph('Nový zůstatek', s15), '']
                    else:
                        r = ([''] * 23) \
                            + [Paragraph('Zůstatek', s15), '']
                    d3.extend([r])

                    if trt != 'balance':
                        r = ['', Paragraph('Částka', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa((row['change'] if (trt == 'debit') \
                                             else (-row['change']))), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Jistina', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['pre_principal']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Jistina', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_principal']), s18)] \
                            + ([''] * 7)
                    else:
                        r = ([''] * 23) \
                            + [Paragraph('Jistina', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_principal']), s18)] \
                            + ([''] * 7)
                    d3.extend([r])

                    if trt == 'debit':
                        r = ([''] * 12) \
                            + [Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['pre_interest']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_interest']), s18)] \
                            + ([''] * 7)
                    elif trt == 'credit':
                        r = ['', Paragraph('Jistina', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(-row['change_principal']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['pre_interest']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_interest']), s18)] \
                            + ([''] * 7)
                    else:
                        r = ([''] * 23) \
                            + [Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_interest']), s18)] \
                            + ([''] * 7)
                    d3.extend([r])

                    if trt == 'debit':
                        r = ([''] * 12) \
                            + [Paragraph('Celkem', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['pre_total']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_total']), s18)] \
                            + ([''] * 7)
                    elif trt == 'credit':
                        r = ['', Paragraph('Úrok', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(-row['change_interest']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['pre_total']), s18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_total']), s18)] \
                            + ([''] * 7)
                    else:
                        r = ([''] * 23) \
                            + [Paragraph('Celkem', s17)] \
                            + ([''] * 2) \
                            + [Paragraph(fa(row['post_total']), s18)] \
                            + ([''] * 7)
                    d3.extend([r])

                    r = ([''] * 34)
                    d3.extend([r])

                    t3 = Table(d3, colWidths=cw)
                    t3.setStyle(TableStyle(bst + ast[trt]))
                    flow.append(KeepTogether(t3))

                if debt.note:
                    flow.append(Spacer(0, 24))
                    q = [Paragraph('Poznámka:'.upper(), s4)]
                    for s in filter(bool, debt.note.strip().split('\n')):
                        q.append(Paragraph(escape(s), s12))
                    flow.append(KeepTogether(q[:2]))
                    if len(q) > 2:
                        flow.extend(q[2:])
                temp = BytesIO()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.pdf'
                doc = SimpleDocTemplate(
                    temp,
                    pagesize=A4,
                    title='Historie peněžité pohledávky',
                    author='{} V{}'.format(APP.upper(), APPVERSION),
                    leftMargin=64.0,
                    rightMargin=48.0,
                    topMargin=48.0,
                    bottomMargin=96.0,
                    )
                CanvasXML.xml = toxml(debt)
                doc.build(
                    flow,
                    onFirstPage=page1,
                    onLaterPages=page2,
                    canvasmaker=CanvasXML)
                response.write(temp.getvalue())
                return response

        else:
            logger.debug('Invalid form', request)
            err_message = inerr

    for row in rows:
        row['change'] = cellam(row['change'])
        if not row['err']:
            row['pre_principal'] = cellam(row['pre_principal'])
            row['pre_interest'] = cellam(row['pre_interest'], True)
            row['change_principal'] = cellam(row['change_principal'])
            row['change_interest'] = cellam(row['change_interest'], True)
            row['post_principal'] = cellam(row['post_principal'])
            row['post_interest'] = cellam(row['post_interest'], True)
            row['post_total'] = cellam(row['post_total'], True)

    return render(
        request,
        'hjp_mainpage.html',
        {'app': APP,
         'page_title': 'Historie jednoduché peněžité pohledávky',
         'f': f,
         'rows': rows,
         'currency': dispcurr(debt.currency),
         'ydconvs': ydconvs,
         'mdconvs': mdconvs,
         'err_message': err_message,
         'rows_err': rows_err})


@require_http_methods(['GET', 'POST'])
@login_required
def transform(request, id=0):

    logger.debug(
        'Transaction form accessed using method {}, id={}' \
            .format(request.method, id),
        request,
        request.POST)
    page_title = ('Úprava transakce' if id else 'Nová transakce')
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    id = int(id)
    if request.method == 'GET':
        if id:
            if id > len(debt.transactions):
                raise Http404
            transaction = debt.transactions[id - 1]
            var = {'description': transaction.description,
                   'transaction_type': transaction.transaction_type,
                   'date': transaction.date}
            if hasattr(transaction, 'amount'):
                var['amount'] = '{:.2f}'.format(Lf(transaction.amount)) \
                    if debt.rounding else int(round(transaction.amount))
            if hasattr(transaction, 'repayment_preference'):
                var['repayment_preference'] = transaction.repayment_preference
            f = TransForm(initial=var)
        else:
            f = TransForm()
    else:
        f = TransForm(request.POST)

        btn = getbutton(request)
        if btn == 'back':
            return redirect('hjp:mainpage')
        if btn == 'set_date':
            f.data = f.data.copy()
            f.data['date'] = date.today()
        elif f.is_valid():
            cd = f.cleaned_data
            transaction = Transaction()
            transaction.description = cd['description'].strip()
            transaction.transaction_type = cd['transaction_type']
            transaction.date = cd['date']
            if transaction.transaction_type != 'balance':
                transaction.amount = float(cd['amount'])
            if transaction.transaction_type == 'credit':
                transaction.repayment_preference = cd['repayment_preference']
            if id:
                if id > len(debt.transactions):
                    raise Http404
                debt.transactions[id - 1] = transaction
            else:
                debt.transactions.append(transaction)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:mainpage')

        else:
            logger.debug('Invalid form', request)
            err_message = inerr

    return render(request,
                  'hjp_transform.html',
                  {'app': APP,
                   'f': f,
                   'page_title': page_title,
                   'currency': dispcurr(debt.currency),
                   'err_message': err_message})


@require_http_methods(['GET', 'POST'])
@login_required
def transdel(request, id=0):

    logger.debug(
        'Transaction delete page accessed using method {}, id={}' \
            .format(request.method, id),
        request,
        request.POST)
    id = int(id) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if id >= len(debt.transactions):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hjp_transdel.html',
            {'app': APP,
             'page_title': 'Smazání transakce',
             'date': debt.transactions[id].date})
    else:
        btn = getbutton(request)
        if btn == 'yes':
            del debt.transactions[id]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:transdeleted')
        return redirect('hjp:mainpage')
