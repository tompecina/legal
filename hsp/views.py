# -*- coding: utf-8 -*-
#
# hsp/views.py
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
from common import fields
from common.settings import FONT_DIR
from common.utils import (
    getbutton, yfactor, mfactor, formam, xmldecorate, xmlescape, xmlunescape,
    Lf, rmdsl, getXML, newXML, iso2date, CanvasXML, logger)
from common.glob import (
    ydconvs, odp, mdconvs, LIM, inerr, localsubdomain, localurl)
from common.views import error
from cache.main import getasset, setasset
from cnb.main import getMPIrate, getFXrate
from hsp.forms import MainForm, DebitForm, CreditForm, BalanceForm, FXform


APP = __package__

APPVERSION = apps.get_app_config(APP).version


class Debt(object):

    def __init__(self):
        self.title = ''
        self.note = ''
        self.internal_note = ''
        self.rounding = 0
        self.debits = []
        self.credits = []
        self.balances = []
        self.fxrates = []


class Debit(object):

    def __init__(self):
        self.description = ''
        self.model = 'fixed'
        self.fixed_amount = 0.0
        self.fixed_currency = 'CZK'
        self.fixed_date = None
        self.rate = 0.0
        self.day_count_convention = ''
        self.principal_debit = 0
        self.principal_amount = 0.0
        self.principal_currency = 'CZK'
        self.date_from = None
        self.date_to = None


class Credit(object):

    def __init__(self):
        self.description = ''
        self.date = None
        self.amount = 0.0
        self.currency = 'CZK'
        self.debits = []


class Balance(object):

    def __init__(self):
        self.description = ''
        self.date = None


class FXrate(object):

    def __init__(self):
        self.currency_from = None
        self.currency_to = None
        self.rate_from = 1.0
        self.rate_to = 1.0
        self.date_from = None
        self.date_to = None


class Result(object):

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


def n2l(n):

    return chr(ord('A') + n) if (n <= (ord('Z') - ord('A'))) else '?'


DR, CR, BAL = tuple(range(3))


def calcint(interest, pastdate, presdate, debt, res):

    if not pastdate or pastdate < (interest.default_date - odp):
        pastdate = (interest.default_date - odp)

    if interest.date_to and interest.date_to < presdate:
        presdate = interest.date_to

    if pastdate >= presdate:
        return 0.0, None

    principal = debt.debits[interest.principal_debit - 1].balance \
        if interest.principal_debit else interest.principal_amount

    if interest.model == 'per_annum':
        return (principal * yfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100.0), None

    if interest.model == 'per_mensem':
        return (principal * mfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100.0), None

    if interest.model == 'per_diem':
        return (principal * (presdate - pastdate).days
            * interest.rate / 1000.0), None

    if interest.model == 'cust1':
        r = getMPIrate('DISC', interest.default_date, log=res.mpi)
        if r[1]:
            return None, r[1]
        return (principal * yfactor(pastdate, presdate, 'ACT/ACT')
            * r[0] / 50.0), None

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
            r = getMPIrate('REPO', date(y1, m1, d1), log=res.mpi)
            if r[1]:
                return None, r[1]
            y2 = y1
            if y1 < presdate.year or (m1 == 1 and presdate.month > 6):
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
                return (principal * (s + yfactor((t - odp), date(y2, m2, d2),
                    'ACT/ACT') * (r[0] + 7.0)) / 100.0), None

    if interest.model == 'cust3':
        y = interest.default_date.year
        m = interest.default_date.month
        d = interest.default_date.day
        if m > 6:
            m = 6
            d = 30
        else:
            m = 12
            d = 31
            y -= 1
        r = getMPIrate('REPO', date(y, m, d), log=res.mpi)
        if r[1]:
            return None, r[1]
        return (principal * yfactor(pastdate, presdate, 'ACT/ACT')
            * (r[0] + 7.0) / 100.0), None

    if interest.model == 'cust5':
        y = interest.default_date.year
        m = interest.default_date.month
        d = interest.default_date.day
        if m > 6:
            m = 6
            d = 30
        else:
            m = 12
            d = 31
            y -= 1
        r = getMPIrate('REPO', date(y, m, d), log=res.mpi)
        if r[1]:
            return None, r[1]
        return (principal * yfactor(pastdate, presdate, 'ACT/ACT')
            * (r[0] + 8.0) / 100.0), None

    if interest.model == 'cust6':
        y = interest.default_date.year
        m = interest.default_date.month
        if m > 6:
            m = 7
        else:
            m = 1
        r = getMPIrate('REPO', date(y, m, 1), log=res.mpi)
        if r[1]:
            return None, r[1]
        return (principal * yfactor(pastdate, presdate, 'ACT/ACT')
            * (r[0] + 8.0) / 100.0), None

    if interest.model == 'cust4':
        return (principal * (presdate - pastdate).days * .0025), None

    return None, 'Neznámý model'


def distr(debt, dt, credit, amount, disarr, res):

    if amount < LIM:
        return 0.0, None
    for i in credit.debits:
        debit = debt.debits[i]
        if debit.nb >= LIM:
            if credit.currency == debit.currency:
                rt = 1.0
            else:
                for fxrate in debt.fxrates:
                    if fxrate.currency_from == credit.currency \
                        and fxrate.currency_to == debit.currency \
                        and (not fxrate.date_from or fxrate.date_from <= dt) \
                        and (not fxrate.date_to or dt <= fxrate.date_to):
                        rt = fxrate.rate_to / fxrate.rate_from
                        break
                else:
                    if credit.currency == 'CZK':
                        rcl = 1.0
                    else:
                        r, q, dr, msg = getFXrate(
                            credit.currency,
                            dt,
                            log=res.fx,
                            use_fixed=True,
                            log_fixed=res.fix)
                        if msg:
                            return 0.0, msg
                        rcl = (r / q)
                    if debit.currency == 'CZK':
                        rld = 1.0
                    else:
                        r, q, dr, msg = getFXrate(
                            debit.currency,
                            dt,
                            log=res.fx,
                            use_fixed=True,
                            log_fixed=res.fix)
                        if msg:
                            return 0.0, msg
                        rld = (r / q)
                    rt = (rcl / rld)
            camount = (amount * rt)
            if camount < debit.nb:
                debit.nb -= camount
                debit.nb = round(debit.nb, debt.rounding)
                disarr[i] += camount
                return 0.0, None
            disarr[i] += debit.nb
            amount -= (debit.nb / rt)
            debit.nb = 0.0
    return amount, None


def calc(debt, pram=(lambda x: x)):

    res = Result()

    res.msg = None
    res.rows = []
    res.fx = []
    res.fix = []
    res.mpi = []

    res.nd = len(debt.debits)
    res.nc = len(debt.credits)
    res.nb = len(debt.balances)
    res.nf = len(debt.fxrates)

    res.ids = []
    for i, debit in enumerate(debt.debits):
        debit.id = n2l(i)
        res.ids.append(debit.id)

    res.currencies = []
    for debit in debt.debits:
        if debit.model == 'fixed':
            c = debit.fixed_currency
        elif debit.principal_debit:
            c = debt.debits[debit.principal_debit - 1].fixed_currency
        else:
            c = debit.principal_currency
        debit.currency = c
        debit.disp_currency = c
        if c not in res.currencies:
            res.currencies.append(c)
    res.multicurrency_debit = (len(res.currencies) > 1)
    if res.currencies and not res.multicurrency_debit:
        res.currency_debits = res.currencies[0]
    for credit in debt.credits:
        if credit.currency not in res.currencies:
            res.currencies.append(credit.currency)
    res.currencies.sort()
    res.multicurrency = (len(res.currencies) > 1)
    if res.currencies and not res.multicurrency:
        res.currency = res.currencies[0]

    dr = {}
    cust4 = []
    ncust4 = []
    for i, debit in enumerate(debt.debits):
        debit.balance = 0.0
        if debit.model == 'fixed':
            dt = debit.fixed_date
            if dt not in dr:
                dr[dt] = []
            dr[dt].append(i)
        else:
            debit.default_date = (debit.date_from + odp) if debit.date_from \
                else (debt.debits[debit.principal_debit - 1].fixed_date + odp)
            if debit.model == 'cust4':
                cust4.append(debit)
                debit.mb = debit.default_date
                debit.mm = (25.0 if (debit.currency == 'CZK') else 0.0)
                debit.ui = debit.li = 0.0
            else:
                ncust4.append(debit)
    ir = (cust4 + ncust4)

    cr = {}
    for i, credit in enumerate(debt.credits):
        credit.sp = 0.0
        dt = credit.date
        if dt not in cr:
            cr[dt] = []
        cr[dt].append(i)
    bal = {}
    for i, balance in enumerate(debt.balances):
        dt = balance.date
        if dt not in bal:
            bal[dt] = []
        bal[dt].append(i)

    ta = []
    for dt, l in dr.items():
        for i in l:
            ta.append({'tp': DR, 'dt': dt, 'id': i, 'o': debt.debits[i]})
    for dt, l in cr.items():
        for i in l:
            ta.append({'tp': CR, 'dt': dt, 'id': i, 'o': debt.credits[i]})
    for dt, l in bal.items():
        for i in l:
            ta.append({'tp': BAL, 'dt': dt, 'id': i, 'o': debt.balances[i]})
    ta.sort(key=(lambda x: x['tp']))
    ta.sort(key=(lambda x: x['dt']))

    res.nd3 = (res.nd * 3)
    if res.nd:
        res.hrow = True
        res.crow = res.ccol = res.multicurrency
        res.scol = not res.multicurrency_debit and res.nd > 1
        res.c1 = 3 if res.crow else 2
        res.c2 = res.nd
        res.c3 = res.nd + (1 if res.scol else 0)
        res.c4 = (res.nd * 3) + 3 + (1 if res.scol else 0) \
            + (1 if res.ccol else 0)
    else:
        res.hrow = res.crow = res.ccol = res.scol = False
        res.c1 = res.c2 = res.c3 = 1
        res.c4 = 7
    res.r3 = list(range(3))

    if not ta:
        return res

    dt = ta[0]['dt']
    for i in ir:
        dt = min(dt, i.default_date)
    dt -= odp
    e = 0
    cud = None
    while dt <= ta[-1]['dt']:
        for i in cust4:
            if dt >= i.default_date and (not i.date_to or dt <= i.date_to):
                if dt == i.mb:
                    i.li = 0.0
                    i.ui = i.mm
                if i.principal_debit:
                    ii = debt.debits[i.principal_debit - 1].balance
                else:
                    ii = i.principal_amount
                ii *= 0.0025
                ii = max(ii, 0.0)
                i.li += ii
                if i.li > i.ui:
                    di = (i.li - i.ui)
                    i.ui = i.li
                else:
                    di = 0.0
                if dt == i.mb:
                    di += i.mm
                    d = i.default_date.day
                    m = (dt.month + 1)
                    y = dt.year
                    if m > 12:
                        m = 1
                        y += 1
                    d = min(d, monthrange(y, m)[1])
                    i.mb = date(y, m, d)
                i.balance += di

        while e < len(ta) and ta[e]['dt'] == dt:
            tt = ta[e]
            for debit in debt.debits:
                debit.nb = debit.balance
            for i in ncust4:
                ai, res.msg = calcint(i, cud, dt, debt, res)
                if res.msg:  # pragma: no cover
                    return res
                i.nb += ai
            o = tt['o']
            row = {'object': o,
                   'date': dt,
                   'description': o.description,
                   'amount': pram(0.0),
                   'pre': [],
                   'change': [],
                   'post': [],
                   'pre_total': 0.0,
                   'post_total': 0.0,
                   'cr_distr': ([0.0] * res.nd),
                   'sp_distr': ([0.0] * res.nd),
                   'sps': [],
                   'currency': '',
                   'disp_currency': ''}
            tp = row['type'] = tt['tp']
            for debit in debt.debits:
                debit.ob = debit.nb = round(debit.nb, debt.rounding)
                if tp == BAL:
                    row['pre'].append(pram(0.0))
                else:
                    row['pre'].append(pram(debit.nb))
                    row['pre_total'] += debit.nb
            if tp == DR:
                row['id'] = o.id
                row['amount'] = pram(o.fixed_amount)
                o.nb += o.fixed_amount
                o.nb = round(o.nb, debt.rounding)
            for credit in debt.credits:
                credit.nsp, res.msg = \
                    distr(debt, dt, credit, credit.sp, row['sp_distr'], res)
                if res.msg:
                    return res
            if tp == CR:
                row['amount'] = pram(-o.amount)
                row['debits'] = o.debits
                sp, res.msg = \
                    distr(debt, dt, o, o.amount, row['cr_distr'], res)
                if res.msg:
                    return res
                o.nsp += sp
            for debit in debt.debits:
                row['post'].append(pram(debit.nb))
                if not res.multicurrency_debit:
                    row['post_total'] += debit.nb
                if tp == BAL:
                    row['change'].append(pram(0.0))
                else:
                    row['change'].append(pram(debit.nb - debit.ob))
            if tp == DR and o.model == 'fixed':
                row['disp_currency'] = o.fixed_currency
            elif tp == CR:
                row['disp_currency'] = o.currency
            if not res.multicurrency_debit:
                row['post_total'] = pram(round(row['post_total'],
                                               debt.rounding))

            for credit in debt.credits:
                if credit.nsp > LIM:
                    for sp in row['sps']:
                        if sp['curr'] == credit.currency:
                            sp['total'] += credit.nsp
                            break
                    else:
                        row['sps'].append({'curr': credit.currency,
                                           'total': credit.nsp})
            row['sps'].sort(key=(lambda x: x['curr']))

            r = []
            for sp in row['sps']:
                r.append('{}&nbsp;{}'.format(
                    pram(sp['total']),
                    sp['curr'] if (res.multicurrency or sp['curr'] != 'CZK')
                    else 'Kč'))
            row['sps_text'] = ', '.join(r)

            if tp != BAL:
                for debit in debt.debits:
                    debit.balance = debit.nb
                for credit in debt.credits:
                    credit.sp = credit.nsp
                cud = dt

            res.rows.append(row)
            e += 1

        dt += odp

    return res


def toxml(debt):

    xd = {
        'debt': {
            'xmlns': 'http://' + localsubdomain,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'
                .format(localsubdomain, localurl, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()},
        'currency': {'standard': 'ISO 4217'},
        'fixed_currency': {'standard': 'ISO 4217'},
        'principal_currency': {'standard': 'ISO 4217'},
        'currency_from': {'standard': 'ISO 4217'},
        'currency_to': {'standard': 'ISO 4217'},
        'pa_rate': {'unit': 'percent per annum'},
        'pm_rate': {'unit': 'percent per month'},
        'pd_rate': {'unit': 'per mil per day'}}
    xml = newXML('')
    d = xmldecorate(xml.new_tag('debt'), xd)
    xml.append(d)
    for tt in ['title', 'note', 'internal_note']:
        tag = xml.new_tag(tt)
        tag.append(xmlescape(debt.__getattribute__(tt)))
        d.append(tag)
    tag = xml.new_tag('rounding')
    tag.append(str(debt.rounding))
    d.append(tag)

    ts = xml.new_tag('debits')
    for debit in debt.debits:
        t = xml.new_tag('debit')
        t['model'] = m = debit.model
        tag = xml.new_tag('description')
        tag.append(xmlescape(debit.description))
        t.append(tag)
        if m == 'fixed':
            tag = xml.new_tag('fixed_date')
            tag.append(debit.fixed_date.isoformat())
            t.append(tag)
            tag = xml.new_tag('fixed_amount')
            tag.append('{:.2f}'.format(debit.fixed_amount))
            t.append(tag)
            tag = xmldecorate(xml.new_tag('fixed_currency'), xd)
            tag.append(debit.fixed_currency)
            t.append(tag)
        else:
            if m == 'per_annum':
                tag = xmldecorate(xml.new_tag('pa_rate'), xd)
                tag.append('{:.6f}'.format(debit.rate))
                t.append(tag)
                tag = xml.new_tag('day_count_convention')
                tag.append(debit.day_count_convention)
                t.append(tag)
            elif m == 'per_mensem':
                tag = xmldecorate(xml.new_tag('pm_rate'), xd)
                tag.append('{:.6f}'.format(debit.rate))
                t.append(tag)
                tag = xml.new_tag('day_count_convention')
                tag.append(debit.day_count_convention)
                t.append(tag)
            elif m == 'per_diem':
                tag = xmldecorate(xml.new_tag('pd_rate'), xd)
                tag.append('{:.6f}'.format(debit.rate))
                t.append(tag)
            if debit.principal_debit:
                tag = xml.new_tag('principal_debit')
                tag['id'] = '{:d}'.format(debit.principal_debit - 1)
                t.append(tag)
            else:
                tag = xml.new_tag('principal_amount')
                tag.append('{:.2f}'.format(debit.principal_amount))
                t.append(tag)
                tag = xmldecorate(xml.new_tag('principal_currency'), xd)
                tag.append(debit.principal_currency)
                t.append(tag)
            if hasattr(debit, 'date_from') and debit.date_from:
                tag = xml.new_tag('date_from')
                tag.append(debit.date_from.isoformat())
                t.append(tag)
            if hasattr(debit, 'date_to') and debit.date_to:
                tag = xml.new_tag('date_to')
                tag.append(debit.date_to.isoformat())
                t.append(tag)
        ts.append(t)
    d.append(ts)

    ts = xml.new_tag('credits')
    for credit in debt.credits:
        t = xml.new_tag('credit')
        tag = xml.new_tag('description')
        tag.append(xmlescape(credit.description))
        t.append(tag)
        tag = xml.new_tag('date')
        tag.append(credit.date.isoformat())
        t.append(tag)
        tag = xml.new_tag('amount')
        tag.append('{:.2f}'.format(credit.amount))
        t.append(tag)
        tag = xmldecorate(xml.new_tag('currency'), xd)
        tag.append(credit.currency)
        t.append(tag)
        tag = xml.new_tag('debits')
        t.append(tag)
        for db in credit.debits:
            st = xml.new_tag('debit')
            st['id'] = db
            tag.append(st)
        ts.append(t)
    d.append(ts)

    ts = xml.new_tag('balances')
    for balance in debt.balances:
        t = xml.new_tag('balance')
        tag = xml.new_tag('description')
        tag.append(xmlescape(balance.description))
        t.append(tag)
        tag = xml.new_tag('date')
        tag.append(balance.date.isoformat())
        t.append(tag)
        ts.append(t)
    d.append(ts)

    ts = xml.new_tag('fxrates')
    for fxrate in debt.fxrates:
        t = xml.new_tag('fxrate')
        tag = xmldecorate(xml.new_tag('currency_from'), xd)
        tag.append(fxrate.currency_from)
        t.append(tag)
        tag = xmldecorate(xml.new_tag('currency_to'), xd)
        tag.append(fxrate.currency_to)
        t.append(tag)
        tag = xml.new_tag('rate_from')
        tag.append('{:.3f}'.format(fxrate.rate_from))
        t.append(tag)
        tag = xml.new_tag('rate_to')
        tag.append('{:.3f}'.format(fxrate.rate_to))
        t.append(tag)
        if hasattr(fxrate, 'date_from') and fxrate.date_from:
            tag = xml.new_tag('date_from')
            tag.append(fxrate.date_from.isoformat())
            t.append(tag)
        if hasattr(fxrate, 'date_to') and fxrate.date_to:
            tag = xml.new_tag('date_to')
            tag.append(fxrate.date_to.isoformat())
            t.append(tag)
        ts.append(t)

    d.append(ts)
    return str(xml).encode('utf-8') + b'\n'


def fromxml(d):

    s = getXML(d)
    if not s:
        return None, 'Chybný formát souboru (1)'
    h = s.debt
    if not (h and h['application'] in [APP, 'hjp']):
        return None, 'Chybný formát souboru (2)'

    if h['application'] == APP:
        debt = Debt()
        debt.title = xmlunescape(h.title.text.strip())
        debt.note = xmlunescape(h.note.text.strip())
        debt.internal_note = xmlunescape(h.internal_note.text.strip())
        debt.rounding = int(h.rounding.text.strip())

        for tt in h.debits.findAll('debit'):
            debit = Debit()
            debt.debits.append(debit)
            debit.description = xmlunescape(tt.description.text.strip())
            debit.model = m = tt['model']
            if tt.fixed_amount:
                debit.fixed_amount = float(tt.fixed_amount.text.strip())
            if tt.fixed_currency:
                debit.fixed_currency = tt.fixed_currency.text.strip()
            if tt.fixed_date:
                debit.fixed_date = iso2date(tt.fixed_date)
            if tt.pa_rate:
                debit.rate = float(tt.pa_rate.text.strip())
            if tt.pm_rate:
                debit.rate = float(tt.pm_rate.text.strip())
            if tt.pd_rate:
                debit.rate = float(tt.pd_rate.text.strip())
            if tt.day_count_convention:
                debit.day_count_convention = \
                    tt.day_count_convention.text.strip()
            if tt.principal_debit:
                debit.principal_debit = (int(tt.principal_debit['id']) + 1)
            if tt.principal_amount:
                debit.principal_amount = float(tt.principal_amount.text.strip())
            if tt.principal_currency:
                debit.principal_currency = tt.principal_currency.text.strip()
            if tt.date_from:
                debit.date_from = iso2date(tt.date_from)
            if tt.date_to:
                debit.date_to = iso2date(tt.date_to)

        for tt in h.credits.findAll('credit'):
            credit = Credit()
            debt.credits.append(credit)
            credit.description = xmlunescape(tt.description.text.strip())
            credit.date = iso2date(tt.date)
            credit.amount = float(tt.amount.text.strip())
            credit.currency = tt.currency.text.strip()
            for td in tt.debits.findAll('debit'):
                credit.debits.append(int(td['id']))

        for tt in h.balances.findAll('balance'):
            balance = Balance()
            debt.balances.append(balance)
            balance.description = xmlunescape(tt.description.text.strip())
            balance.date = iso2date(tt.date)

        for tt in h.fxrates.findAll('fxrate'):
            fxrate = FXrate()
            debt.fxrates.append(fxrate)
            fxrate.currency_from = tt.currency_from.text.strip()
            fxrate.currency_to = tt.currency_to.text.strip()
            fxrate.rate_from = float(tt.rate_from.text.strip())
            fxrate.rate_to = float(tt.rate_to.text.strip())
            if tt.date_from:
                fxrate.date_from = iso2date(tt.date_from)
            if tt.date_to:
                fxrate.date_to = iso2date(tt.date_to)

    else:
        debt = Debt()
        debt.title = xmlunescape(h.title.text.strip())
        debt.note = xmlunescape(h.note.text.strip())
        debt.internal_note = xmlunescape(h.internal_note.text.strip())
        debt.rounding = int(h.rounding.text.strip())
        currency = h.currency.text.strip()
        interest = h.interest
        tr = list(h.transactions.children)
        firstfix = True
        principals = []
        interests = []
        for tt in tr:
            if not tt.name:
                continue
            if (tt.has_attr('type') and tt['type'] == 'debit') \
               or str(tt.name) == 'debit':
                d = Debit()
                i = len(debt.debits)
                principals.append(i)
                debt.debits.append(d)
                d.model = 'fixed'
                d.description = xmlunescape(tt.description.text.strip())
                d.fixed_amount = float(tt.amount.text.strip())
                d.fixed_currency = currency
                d.fixed_date = iso2date(tt.date)
                m = interest['model']
                if m != 'none' and (m != 'fixed' or firstfix):
                    firstfix = False
                    d = Debit()
                    interests.append(len(debt.debits))
                    debt.debits.append(d)
                    d.description = 'Úrok'
                    d.model = m
                    d.principal_debit = (i + 1)
                    if m == 'fixed':
                        d.fixed_amount = float(interest.amount.text.strip())
                        d.fixed_currency = currency
                        d.fixed_date = iso2date(tt.date)
                    elif m == 'per_annum':
                        d.rate = float(interest.pa_rate.text.strip())
                        d.day_count_convention = \
                            interest.day_count_convention.text.strip()
                    elif m == 'per_mensem':
                        d.rate = float(interest.pm_rate.text.strip())
                        d.day_count_convention = \
                            interest.day_count_convention.text.strip()
                    elif m == 'per_diem':
                        d.rate = float(interest.pd_rate.text.strip())
        orderi = (interests + principals)
        orderp = (principals + interests)
        for tt in tr:
            if not tt.name:
                continue
            tt_type = str(tt.name)
            if tt_type == 'credit':
                c = Credit()
                debt.credits.append(c)
                c.description = xmlunescape(tt.description.text.strip())
                c.amount = float(tt.amount.text.strip())
                c.currency = currency
                c.date = iso2date(tt.date)
                c.debits = orderp[:] if (tt.repayment_preference.text.strip()
                    == 'principal') else orderi[:]
            elif tt_type == 'balance':
                b = Balance()
                debt.balances.append(b)
                b.description = xmlunescape(tt.description.text.strip())
                b.date = iso2date(tt.date)
    return debt, None


@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    def ft(a):
        a = (round(a, debt.rounding) if debt.rounding else int(round(a)))
        if abs(a) < LIM:
            return '<span class="dr"></span>'
        elif a > 0:
            return '<span class="dr">{}</span>'.format(formam(a))
        elif a:
            return '<span class="cr">{}</span>'.format(formam(-a))

    def fa(a, c):
        if not a or abs(a) < LIM:
            return ''
        r = formam(round(a, debt.rounding)
            if debt.rounding else int(round(a))).replace('-', '−')
        if res.multicurrency or c != 'CZK':
            return '{}&nbsp;{}'.format(r, c)
        return '{}&nbsp;Kč'.format(r)

    err_message = ''

    if request.method == 'GET':
        debt = getdebt(request)
        if not debt:  # pragma: no cover
            return error(request)

        var = {
            'title': debt.title,
            'note': debt.note,
            'internal_note': debt.internal_note,
            'rounding': str(debt.rounding)
        }
        f = MainForm(initial=var)

    else:
        btn = getbutton(request)

        if btn == 'empty':
            debt = Debt()
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

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
                    return redirect('hsp:mainpage')
                except:
                    err_message = 'Chyba při načtení souboru'

        debt = getdebt(request)
        if not debt:  # pragma: no cover
            return error(request)

        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            debt.title = cd['title'].strip()
            debt.note = cd['note'].strip()
            debt.internal_note = cd['internal_note'].strip()
            debt.rounding = int(cd['rounding'])
            setdebt(request, debt)

            if not btn and cd['next']:
                return redirect(cd['next'])

            if btn == 'xml':
                response = HttpResponse(
                    toxml(debt),
                    content_type='text/xml; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.xml'
                return response

            if btn == 'csv':
                res = calc(debt)
                response = \
                    HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.csv'
                writer = csv.writer(response)
                hdr = ['Datum', 'Popis', 'Částka', 'Měna']
                for debit in debt.debits:
                    hdr.append('Předchozí zůstatek {0.id} ({0.currency})'
                                   .format(debit))
                for debit in debt.debits:
                    hdr.append('Změna {0.id} ({0.currency})'.format(debit))
                for debit in debt.debits:
                    hdr.append('Nový zůstatek {0.id} ({0.currency})'
                                   .format(debit))
                writer.writerow(hdr)
                for row in res.rows:
                    dat = [
                        row['date'].isoformat(),
                        row['description'],
                        '{:.2f}'.format(row['amount']),
                        row['disp_currency']
                    ]
                    dat.extend(['{:.2f}'.format(t) for t in row['pre']])
                    dat.extend(['{:.2f}'.format(t) for t in row['change']])
                    dat.extend(['{:.2f}'.format(t) for t in row['post']])
                    writer.writerow(dat)
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
                        'Vytvořeno: {0.day:02d}.{0.month:02d}.{0.year:02d}'
                            .format(today))
                    c.restoreState()

                def page2(c, d):
                    page1(c, d)
                    c.saveState()
                    c.setFont('Bookman', 8)
                    c.drawCentredString(
                        (A4[0] / 2),
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

                s17 = ParagraphStyle(
                    name='S17',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                s18 = ParagraphStyle(
                    name='S18',
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
                    spaceBefore=4,
                    allowWidows=False,
                    allowOrphans=False,
                    bulletFontName='Bookman',
                    bulletFontSize=8,
                    bulletIndent=8,
                    leftIndent=16)

                s22 = ParagraphStyle(
                    name='S22',
                    fontName='BookmanI',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                s23 = ParagraphStyle(
                    name='S23',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    spaceBefore=15,
                    spaceAfter=4,
                    allowWidows=False,
                    allowOrphans=False,
                    keepWithNext=True)

                s24 = ParagraphStyle(
                    name='S24',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    spaceBefore=4,
                    allowWidows=False,
                    allowOrphans=False,
                    bulletFontName='BookmanB',
                    bulletFontSize=8,
                    bulletIndent=8,
                    leftIndent=24,
                    keepWithNext=True)

                s25 = ParagraphStyle(
                    name='S25',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    leftIndent=24,
                    allowWidows=False,
                    allowOrphans=False)

                s26 = ParagraphStyle(
                    name='S26',
                    fontName='Bookman',
                    fontSize=6,
                    leading=9,
                    spaceBefore=-2,
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

                bst = [('SPAN', (0, 0), (4, 0)),
                       ('SPAN', (5, 0), (33, 0)),
                       ('SPAN', (1, 1), (10, 1)),
                       ('SPAN', (12, 1), (21, 1)),
                       ('SPAN', (23, 1), (32, 1)),
                       ('LINEABOVE', (0, 0), (-1, 0), 1, black),
                       ('LINEBELOW', (0, 0), (-1, 0), 1, black),
                       ('LINEBEFORE', (0, 0), (0, -1), 1, black),
                       ('LINEAFTER', (-1, 0), (-1, -1), 1, black),
                       ('LINEBELOW', (0, -1), (-1, -1), 1, black),
                       ('BACKGROUND', (0, 0), (-1, 0), '#e8e8e8'),
                       ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                       ('LEFTPADDING', (0, 0), (-1, 0), 0),
                       ('LEFTPADDING', (0, 1), (-1, -1), 3),
                       ('LEFTPADDING', (2, 2), (2, -1), 5),
                       ('LEFTPADDING', (13, 2), (13, -1), 5),
                       ('LEFTPADDING', (24, 2), (24, -1), 5),
                       ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                       ('TOPPADDING', (0, 0), (-1, 0), 2.5),
                       ('TOPPADDING', (0, 1), (-1, 1), 10),
                       ('TOPPADDING', (0, 2), (-1, -1), 0),
                       ('BOTTOMPADDING', (0, 0), (-1, 0), 0.5),
                       ('BOTTOMPADDING', (0, 1), (-1, 1), 1.5),
                       ('BOTTOMPADDING', (0, -1), (-1, -1), 18),
                      ]

                cust2eff = {
                    'cust1': 'do 27.04.2005',
                    'cust2': 'od 28.04.2005 do 30.06.2010',
                    'cust3': 'od 01.07.2010',
                    'cust5': 'od 01.07.2013 do 31.12.2013'}
                mpitypes = {
                    'DISC': 'diskontní sazba',
                    'REPO': '2T repo sazba'}

                w = 483.30
                wl = 8.0
                wr = 8.0
                wg = 12.0
                wf = wc = ((w - wl - wr - (wg * 2.0)) / 6.0)
                cw = [wl] + ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wg] \
                    + ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wg] \
                    + ([wc / 5.0] * 5) + ([wf / 5.0] * 5) + [wr]

                res = calc(debt)
                tl = 0.5

                r = []

                if debt.debits:
                    r.append(Paragraph('Závazky:', s23))
                    for debit in debt.debits:
                        r.append(Paragraph(
                            ('<b>{}</b>'.format(debit.description)
                             if debit.description else
                             '<i>(bez názvu)</i>'),
                            s24,
                            bulletText=(debit.id + '.')))
                        m = debit.model
                        if m == 'fixed':
                            t = 'pevná částka {}, splatná {:%d.%m.%Y}' \
                                    .format(
                                        fa(debit.fixed_amount,
                                           debit.fixed_currency),
                                        debit.fixed_date)
                        else:
                            if m == 'per_annum':
                                t = 'roční úrok {0.rate:n} % <i>p. a.</i> ' \
                                    '(konvence pro počítání dnů: ' \
                                    '{0.day_count_convention})'.format(debit)
                            elif m == 'per_mensem':
                                t = 'měsíční úrok {0.rate:n} % <i>p. m.</i> ' \
                                    '(konvence pro počítání dnů: ' \
                                    '{0.day_count_convention})' \
                                        .format(debit)
                            elif m == 'per_diem':
                                t = 'denní úrok {:n} ‰ <i>p. d.</i>' \
                                         .format(debit.rate)
                            elif m in ['cust1', 'cust2', 'cust3', 'cust5']:
                                t = 'zákonný úrok z prodlení podle nařízení ' \
                                    'vlády č. 142/1994 Sb. ve znění účinném ' \
                                    '{}'.format(cust2eff[m])
                            elif m == 'cust6':
                                t = 'zákonný úrok z prodlení podle nařízení ' \
                                    'vlády č. 351/2013 Sb.'
                            else:
                                t = 'zákonný poplatek z prodlení podle ' \
                                    'nařízení vlády č. 142/1994 Sb.'
                            if debit.principal_debit:
                                t += ' ze závazku {}'.format(
                                    n2l(debit.principal_debit - 1))
                            else:
                                t += ' z&nbsp;částky {}'.format(
                                    fa(debit.principal_amount,
                                       debit.principal_currency))
                            if debit.date_from:
                                t += ' od {:%d.%m.%Y}'.format(debit.date_from)
                            elif debit.principal_debit:
                                t += ' od splatnosti'
                            if debit.date_to:
                                t += ' do {:%d.%m.%Y}'.format(debit.date_to)
                            elif debit.principal_debit:
                                t += ' do zaplacení'
                        r.append(Paragraph(t, s25))

                if debt.fxrates:
                    r.append(Paragraph(('Pevně zadané směnné kursy:'), s23))
                    for fxrate in debt.fxrates:
                        t = ''
                        if fxrate.date_from:
                            t += ' od {:%d.%m.%Y}'.format(fxrate.date_from)
                        if fxrate.date_to:
                            t += ' do {:%d.%m.%Y}'.format(fxrate.date_to)
                        if t:
                            t = ' ({})'.format(t.strip())
                        r.append(Paragraph(
                            '{0.rate_from:n} {0.currency_from} = {0.rate_to:n} '
                            '{0.currency_to}{1}'.format(fxrate, t),
                            s20,
                            bulletText='–'))

                if res.fx:
                    res.fx.sort(key=(lambda x: x['date_required']))
                    res.fx.sort(key=(lambda x: x['currency']))
                    rmdsl(res.fx)
                    r.append(Paragraph(('Použité směnné kursy ČNB:'), s23))
                    for fx in res.fx:
                        r.append(Paragraph(
                            '{0[quantity]:d} {0[currency]} = {1:.3f} CZK, '
                            'platný ke dni {0[date_required]:%d.%m.%Y}'
                                .format(fx, Lf(fx['rate'])),
                            s20,
                            bulletText='–'))

                if res.fix:
                    res.fix.sort(key=(lambda x: x['currency_to']))
                    res.fix.sort(key=(lambda x: x['currency_from']))
                    rmdsl(res.fix)
                    r.append(Paragraph(('Použité fixní směnné poměry:'), s23))
                    for fix in res.fix:
                        r.append(Paragraph(
                            '{0} {1[currency_from]} = 1 {1[currency_to]}, '
                            'platný od {1[date_from]:%d.%m.%Y}'
                                .format(formam(fix['rate']), fix),
                            s20,
                            bulletText='–'))

                if res.mpi:
                    res.mpi.sort(key=(lambda x: x['date']))
                    res.mpi.sort(key=(lambda x: x['type']))
                    rmdsl(res.mpi)
                    r += [Paragraph(('Použité úrokové sazby ČNB:'), s23)]
                    for mpi in res.mpi:
                        r.append(Paragraph(
                            '{} ke dni {:%d.%m.%Y}: {:.2f} % <i>p. a.</i>'
                                .format(
                                    mpitypes[mpi['type']],
                                    mpi['date'],
                                    Lf(mpi['rate'])),
                            s20,
                            bulletText='–'))

                r.append(Spacer(0, 50))
                flow.extend(r)

                for row in res.rows:

                    tp = row['type']
                    spf = bool(row['sps'])

                    hdr = ([''] * 3)
                    ln = ([0] * 3)
                    cl = [[], [], []]
                    cr = [[], [], []]

                    if tp == DR:
                        hdr[0] = 'Závazek'
                        ln[0] = 1
                        cl[0].append(row['id'])
                        cr[0].append((row['amount'], row['disp_currency']))

                    if tp == CR:
                        hdr[0] = 'Splátka'
                        ln[0] = 1
                        cl[0].append('∑')
                        cr[0].append((-row['amount'], row['disp_currency']))
                        for debit, amount in zip(debt.debits, row['cr_distr']):
                            if abs(amount) > LIM:
                                ln[0] += 1
                                cl[0].append(debit.id)
                                cr[0].append((amount, debit.currency))

                    if tp in [DR, CR]:
                        for i in row['pre']:
                            if abs(i) > LIM:
                                hdr[1] = 'Předchozí zůstatek'
                                for debit, amount in \
                                    zip(debt.debits, row['pre']):
                                    if abs(amount) > LIM:
                                        ln[1] += 1
                                        cl[1].append(debit.id)
                                        cr[1].append((amount, debit.currency))
                                if not res.multicurrency_debit and ln[1] > 1:
                                    ln[1] += 1
                                    cl[1].append('∑')
                                    cr[1].append(
                                        (row['pre_total'],
                                         res.currency_debits))
                                break

                    if spf:
                        hdr[2] = 'Přeplatek'
                        for sp in row['sps']:
                            ln[2] += 1
                            cl[2].append('∑')
                            cr[2].append((sp['total'], sp['curr']))
                    else:
                        hdr[2] = ('Nový zůstatek' if hdr[1] else 'Zůstatek')
                        for debit, amount in zip(debt.debits, row['post']):
                            if abs(amount) > LIM:
                                ln[2] += 1
                                cl[2].append(debit.id)
                                cr[2].append((amount, debit.currency))
                        if not res.multicurrency_debit and ln[2] > 1:
                            ln[2] += 1
                            cl[2].append('∑')
                            cr[2].append((row['post_total'],
                                          res.currency_debits))

                    lm = max(ln)

                    for i in range(3):
                        while len(cl[i]) < lm:
                            cl[i].append('')
                        while len(cr[i]) < lm:
                            cr[i].append((None, None))

                    ast = [('RIGHTPADDING', (2, 2), (10, (1 + lm)), 0),
                           ('RIGHTPADDING', (13, 2), (21, (1 + lm)), 0),
                           ('RIGHTPADDING', (24, 2), (32, (1 + lm)), 0),
                           ('BOTTOMPADDING', (0, 2), (-1, (1 + lm)), 0),
                          ]

                    for i in range(lm):
                        ast.extend([
                            ('SPAN', (2, (2 + i)), (10, (2 + i))),
                            ('SPAN', (13, (2 + i)), (21, (2 + i))),
                            ('SPAN', (24, (2 + i)), (32, (2 + i))),
                        ])

                    for i in range(3):
                        if hdr[i]:
                            ast.append(('LINEBELOW', ((1 + (11 * i)), 1),
                                        ((10 + (11 * i)), 1), tl, black))
                        if ln[i]:
                            ast.append(('LINEAFTER', ((1 + (11 * i)), 2),
                                        ((1 + (11 * i)), (1 + ln[i])),
                                        tl, black))

                    d3 = []
                    r = [Paragraph('{:%d.%m.%Y}'.format(row['date']), s13)] \
                        + ([''] * 4)
                    q = Paragraph((escape(row['description']).upper()
                        if row['description'] else '<i>(bez názvu)</i>'), s14)
                    if tp == CR:
                        if len(row['debits']) > 1:
                            q = [q,
                                 Paragraph('Pořadí závazků: {}'.format(
                                     ' – '.join(map(n2l, row['debits']))), s26)]
                    q = [q] + ([''] * 28)
                    d3.extend([r + q])

                    r = ['', Paragraph(hdr[0], s15)] \
                        + ([''] * 10) \
                        + [Paragraph(hdr[1], s15)] \
                        + ([''] * 10) \
                        + [Paragraph(hdr[2], s15), '']
                    d3.extend([r])

                    for i in range(lm):
                        r = ['', Paragraph(cl[0][i], s17)] \
                            + [Paragraph(fa(*cr[0][i]), s18)] \
                            + ([''] * 9) \
                            + [Paragraph(cl[1][i], s17)] \
                            + [Paragraph(fa(*cr[1][i]), s18)] \
                            + ([''] * 9) \
                            + [Paragraph(cl[2][i], s17)] \
                            + [Paragraph(fa(*cr[2][i]), s18)] \
                            + ([''] * 9)
                        d3.extend([r])

                    r = ([''] * 34)
                    d3.extend([r])

                    t3 = Table(d3, colWidths=cw)
                    t3.setStyle(TableStyle(bst + ast))
                    flow.append(KeepTogether(t3))

                if res.msg:
                    flow.extend(
                        [Spacer(0, 20),
                         Paragraph('(pro další transakce nejsou k disposici '
                                   'data, při výpočtu došlo k chybě)', s22)])

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

    res = calc(debt, ft)

    for n, debit in enumerate(debt.debits):
        debit.id = n2l(n)
        m = debit.model
        if m == 'fixed':
            t = 'pevná částka {}, splatná {:%d.%m.%Y}'.format(
                fa(debit.fixed_amount,
                   debit.fixed_currency),
                debit.fixed_date)
        else:
            if m == 'per_annum':
                t = 'roční úrok {:n} % <i>p. a.</i>'.format(debit.rate)
            elif m == 'per_mensem':
                t = 'měsíční úrok {:n} % <i>p. m.</i>'.format(debit.rate)
            elif m == 'per_diem':
                t = 'denní úrok {:n} ‰ <i>p. d.</i>'.format(debit.rate)
            elif m in ['cust1', 'cust2', 'cust3', 'cust5', 'cust6']:
                t = 'zákonný úrok z prodlení'
            else:
                t = 'zákonný poplatek z prodlení'
            if debit.principal_debit:
                t += ' ze závazku {}'.format(n2l(debit.principal_debit - 1))
            else:
                t += ' z&nbsp;částky {}'.format(
                    fa(debit.principal_amount, debit.principal_currency))
            if debit.date_from:
                t += ' od {:%d.%m.%Y}'.format(debit.date_from)
            elif debit.principal_debit:
                t += ' od splatnosti'
            if debit.date_to:
                t += ' do {:%d.%m.%Y}'.format(debit.date_to)
            elif debit.principal_debit:
                t += ' do zaplacení'
        debit.text = t

    for credit in debt.credits:
        credit.text = 'částka {}'.format(fa(credit.amount, credit.currency))
        if len(debt.debits) > 1:
            credit.text += \
                ', pořadí: {}'.format(' → '.join(map(n2l, credit.debits)))

    sc = debt.credits[:]
    id = 1
    for cc in sc:
        cc.id = id
        id += 1
    sc.sort(key=(lambda x: x.date))

    sb = debt.balances[:]
    id = 1
    for bb in sb:
        bb.id = id
        id += 1
    sb.sort(key=(lambda x: x.date))

    return render(
        request,
        'hsp_mainpage.html',
        {'app': APP,
         'page_title': 'Historie složené peněžité pohledávky',
         'f': f,
         'debt': debt,
         'res': res,
         'sc': sc,
         'sb': sb,
         'err_message': err_message})


@require_http_methods(['GET', 'POST'])
@login_required
def debitform(request, id=0):

    logger.debug(
        'Debit form accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)

    page_title = ('Úprava závazku' if id else 'Nový závazek')
    var = {}
    err_message = ''
    id = int(id)
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    fields.AmountField.rounding = debt.rounding
    nd = len(debt.debits)

    rows = [{'value': 0, 'text': 'pevné částky:', 'sel': False}]
    for n, d in enumerate(debt.debits):
        if d.model == 'fixed' and (not id or n != (id - 1)):
            row = {'value': (n + 1),
                   'text': '{} – {}'.format(n2l(n), (d.description
                        if d.description else '(bez názvu)')),
                   'sel': False}
            rows.append(row)

    if request.method == 'GET':
        if id:
            if id > nd:
                raise Http404
            debit = debt.debits[id - 1]
            var['description'] = debit.description
            var['model'] = m = debit.model
            if m == 'fixed':
                var['fixed_amount'] = debit.fixed_amount
                var['fixed_currency'] = debit.fixed_currency
                var['fixed_date'] = debit.fixed_date
            elif m == 'per_annum':
                var['pa_rate'] = debit.rate
                var['ydconv'] = debit.day_count_convention
            elif m == 'per_mensem':
                var['pm_rate'] = debit.rate
                var['mdconv'] = debit.day_count_convention
            elif m == 'per_diem':
                var['pd_rate'] = debit.rate
            for row in rows:
                if row['value'] == debit.principal_debit:
                    row['sel'] = True
                    break
            else:  # pragma: no cover
                rows[0]['sel'] = True
            if m != 'fixed':
                var['date_from'] = debit.date_from
                var['date_to'] = debit.date_to
                if debit.principal_debit == 0:
                    var['principal_amount'] = debit.principal_amount
                    var['principal_currency'] = debit.principal_currency
            for debit in debt.debits:
                if debit.principal_debit == id:
                    var['lock_fixed'] = True
                    break
            f = DebitForm(initial=var)
        else:
            rows[0]['sel'] = True
            f = DebitForm()
    else:
        f = DebitForm(request.POST)

        btn = getbutton(request)
        if btn == 'back':
            return redirect('hsp:mainpage')
        else:
            if request.POST.get('principal_debit'):
                for row in rows:
                    if row['value'] == int(request.POST['principal_debit']):
                        row['sel'] = True
                        break
            if id and request.POST.get('model') != 'fixed':
                for debit in debt.debits:
                    if debit.principal_debit == id:
                        err_message = \
                            'Na závazek se váže úrok, vyžaduje pevnou částku'
            if not err_message and f.is_valid():
                cd = f.cleaned_data
                debit = Debit()
                debit.description = cd['description'].strip()
                debit.model = m = cd['model']
                if m == 'fixed':
                    debit.fixed_amount = cd['fixed_amount']
                    debit.fixed_currency = cd['fixed_currency'].upper()
                    debit.fixed_date = cd['fixed_date']
                elif m == 'per_annum':
                    debit.rate = cd['pa_rate']
                    debit.day_count_convention = cd['ydconv']
                elif m == 'per_mensem':
                    debit.rate = cd['pm_rate']
                    debit.day_count_convention = cd['mdconv']
                elif m == 'per_diem':
                    debit.rate = cd['pd_rate']
                if m != 'fixed':
                    debit.date_from = cd['date_from']
                    debit.date_to = cd['date_to']
                    debit.principal_debit = cd['principal_debit']
                    if debit.principal_debit == 0:
                        debit.principal_amount = cd['principal_amount']
                        debit.principal_currency = \
                            cd['principal_currency'].upper()
                if id:
                    if id > nd:
                        raise Http404
                    debt.debits[id - 1] = debit
                else:
                    debt.debits.append(debit)
                    for credit in debt.credits:
                        credit.debits.append(nd)
                if not setdebt(request, debt):  # pragma: no cover
                    return error(request)
                return redirect('hsp:mainpage')

            else:
                logger.debug('Invalid form', request)
                if not err_message:
                    err_message = inerr

    return render(
        request,
        'hsp_debitform.html',
        {'app': APP,
         'f': f,
         'rows': rows,
         'page_title': page_title,
         'ydconvs': ydconvs,
         'mdconvs': mdconvs,
         'err_message': err_message})


@require_http_methods(['GET', 'POST'])
@login_required
def debitdel(request, id=0):

    logger.debug(
        'Debit delete page accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)
    id = int(id) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    nd = len(debt.debits)
    if id >= nd:
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_debitdel.html',
            {'app': APP,
             'page_title': 'Smazání závazku'})
    else:
        btn = getbutton(request)
        if btn == 'yes':
            r = list(range(nd))
            for i in range((nd - 1), -1, -1):
                if i == id or (debt.debits[i].principal_debit - 1) == id:
                    r[i] = None
                    del debt.debits[i]
            c = [x for x in r if x != None]
            m = [(None if x is None else c.index(x)) for x in r]
            for credit in debt.credits:
                d = []
                for i in credit.debits:
                    if m[i] != None:
                        d.append(m[i])
                credit.debits = d
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:debitdeleted')
        return redirect('hsp:mainpage')


@require_http_methods(['GET', 'POST'])
@login_required
def creditform(request, id=0):

    logger.debug(
        'Credit form accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)

    page_title = ('Úprava splátky' if id else 'Nová splátka')
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    fields.AmountField.rounding = debt.rounding
    rows = []
    nd = len(debt.debits)
    deb_class = ''
    if nd > 1:
        for n, _ in enumerate(debt.debits):
            row = {'n': n, 'cols': []}
            for m, c in enumerate(debt.debits):
                row['cols'].append(
                    {'n': m,
                     'id': n2l(m),
                     'desc': debt.debits[m].description})
            rows.append(row)
    id = int(id)
    if request.method == 'GET':
        if id:
            if id > len(debt.credits):
                raise Http404
            credit = debt.credits[id - 1]
            var = {'description': credit.description,
                   'date': credit.date,
                   'amount': credit.amount,
                   'currency': credit.currency}
            f = CreditForm(initial=var)
            if nd > 1:
                for n, d in enumerate(debt.debits):
                    rows[n]['sel'] = credit.debits[n]
        else:
            f = CreditForm()
            if nd > 1:
                if hasattr(debt, 'last_debits') and len(debt.last_debits) == nd:
                    for n, d in enumerate(debt.debits):
                        rows[n]['sel'] = debt.last_debits[n]
                else:
                    for n, d in enumerate(debt.debits):
                        rows[n]['sel'] = n
    else:
        f = CreditForm(request.POST)

        btn = getbutton(request)
        if btn == 'back':
            return redirect('hsp:mainpage')
        else:
            if nd > 1:
                r = []
                for n in range(nd):
                    c = request.POST['r{:d}'.format(n)]
                    if c in r:
                        deb_class = 'err'
                        break
                    else:
                        r.append(c)
            if f.is_valid() and not deb_class:
                cd = f.cleaned_data
                credit = Credit()
                credit.description = cd['description'].strip()
                credit.date = cd['date']
                credit.amount = cd['amount']
                credit.currency = cd['currency'].upper()
                if nd > 1:
                    for n in range(nd):
                        credit.debits.append(int(
                            request.POST['r{:d}'.format(n)]))
                elif nd:
                    credit.debits = [0]
                if id:
                    if id > len(debt.credits):
                        raise Http404
                    debt.credits[id - 1] = credit
                else:
                    debt.credits.append(credit)
                debt.last_debits = credit.debits
                if not setdebt(request, debt):  # pragma: no cover
                    return error(request)
                return redirect('hsp:mainpage')

            else:
                logger.debug('Invalid form', request)
                err_message = inerr
                if nd > 1:
                    for n in range(nd):
                        rows[n]['sel'] = \
                            int(request.POST['r{:d}'.format(n)])

    return render(
        request,
        'hsp_creditform.html',
        {'app': APP,
         'f': f,
         'rows': rows,
         'page_title': page_title,
         'err_message': err_message,
         'deb_class': deb_class})


@require_http_methods(['GET', 'POST'])
@login_required
def creditdel(request, id=0):

    logger.debug(
        'Credit delete page accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)
    id = int(id) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if id >= len(debt.credits):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_creditdel.html',
            {'app': APP,
             'page_title': 'Smazání splátky',
             'date': debt.credits[id].date})
    else:
        btn = getbutton(request)
        if btn == 'yes':
            del debt.credits[id]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:creditdeleted')
        return redirect('hsp:mainpage')


@require_http_methods(['GET', 'POST'])
@login_required
def balanceform(request, id=0):

    logger.debug(
        'Balance form accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)

    page_title = ('Úprava kontrolního bodu' if id else 'Nový kontrolní bod')
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    id = int(id)
    if request.method == 'GET':
        if id:
            if id > len(debt.balances):
                raise Http404
            balance = debt.balances[id - 1]
            var = {'description': balance.description, 'date': balance.date}
            f = BalanceForm(initial=var)
        else:
            f = BalanceForm()
    else:
        f = BalanceForm(request.POST)

        btn = getbutton(request)
        if btn == 'back':
            return redirect('hsp:mainpage')
        if btn == 'set_date':
            f.data = f.data.copy()
            f.data['date'] = date.today()
        elif f.is_valid():
            cd = f.cleaned_data
            balance = Balance()
            balance.description = cd['description'].strip()
            balance.date = cd['date']
            if id:
                if id > len(debt.balances):
                    raise Http404
                debt.balances[id - 1] = balance
            else:
                debt.balances.append(balance)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

        else:
            logger.debug('Invalid form', request)
            err_message = inerr

    return render(
        request,
        'hsp_balanceform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(['GET', 'POST'])
@login_required
def balancedel(request, id=0):

    logger.debug(
        'Balance delete page accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)
    id = int(id) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if id >= len(debt.balances):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_balancedel.html',
            {'app': APP,
             'page_title': 'Smazání kontrolního bodu',
             'date': debt.balances[id].date})
    else:
        btn = getbutton(request)
        if btn == 'yes':
            del debt.balances[id]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:balancedeleted')
        return redirect('hsp:mainpage')


@require_http_methods(['GET', 'POST'])
@login_required
def fxrateform(request, id=0):

    logger.debug(
        'FX rate form accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)

    page_title = ('Úprava kursu' if id else 'Nový kurs')
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    id = int(id)
    if request.method == 'GET':
        if id:
            if id > len(debt.fxrates):
                raise Http404
            fxrate = debt.fxrates[id - 1]
            var = {
                'currency_from': fxrate.currency_from,
                'currency_to': fxrate.currency_to,
                'rate_from': fxrate.rate_from,
                'rate_to': fxrate.rate_to,
                'date_from': fxrate.date_from,
                'date_to': fxrate.date_to
            }
            f = FXform(initial=var)
        else:
            f = FXform()
    else:
        f = FXform(request.POST)

        btn = getbutton(request)
        if btn == 'back':
            return redirect('hsp:mainpage')
        if f.is_valid():
            cd = f.cleaned_data
            fxrate = FXrate()
            fxrate.currency_from = cd['currency_from'].upper()
            fxrate.currency_to = cd['currency_to'].upper()
            fxrate.rate_from = cd['rate_from']
            fxrate.rate_to = cd['rate_to']
            fxrate.date_from = cd['date_from']
            fxrate.date_to = cd['date_to']
            if id:
                if id > len(debt.fxrates):
                    raise Http404
                debt.fxrates[id - 1] = fxrate
            else:
                debt.fxrates.append(fxrate)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

        else:
            logger.debug('Invalid form', request)
            err_message = inerr

    return render(
        request,
        'hsp_fxrateform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'display_note': True})


@require_http_methods(['GET', 'POST'])
@login_required
def fxratedel(request, id=0):

    logger.debug(
        'FX rate delete page accessed using method {}, id={}'
            .format(request.method, id),
        request,
        request.POST)
    id = int(id) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if id >= len(debt.fxrates):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_fxratedel.html',
            {'app': APP,
             'page_title':
             'Smazání kursu',
             'fxrate': debt.fxrates[id]})
    else:
        btn = getbutton(request)
        if btn == 'yes':
            del debt.fxrates[id]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:fxratedeleted')
        return redirect('hsp:mainpage')
