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

from datetime import date, datetime
from calendar import monthrange
from pickle import dumps, loads
from xml.sax.saxutils import escape
import csv
from io import BytesIO

from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from django.shortcuts import redirect, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.apps import apps

from legal.common.glob import YDCONVS, ODP, MDCONVS, LIM, INERR, LOCAL_SUBDOMAIN, LOCAL_URL, ASSET_EXP
from legal.common.utils import (
    getbutton, yfactor, mfactor, famt, xml_decorate, xml_escape, xml_unescape, LocalFloat, get_xml, new_xml, iso2date,
    register_fonts, make_pdf, LOGGER, render, getasset, setasset)
from legal.common import fields
from legal.common.views import error
from legal.cnb.utils import get_mpi_rate, get_fx_rate
from legal.hsp.forms import MainForm, DebitForm, CreditForm, BalanceForm, FXform


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version


class Debt:

    def __init__(self):
        self.title = ''
        self.note = ''
        self.internal_note = ''
        self.rounding = 0
        self.debits = []
        self.credits = []
        self.balances = []
        self.fxrates = []


class Debit:

    def __init__(self):
        self.description = ''
        self.model = 'fixed'
        self.fixed_amount = 0
        self.fixed_currency = 'CZK'
        self.fixed_date = None
        self.rate = 0
        self.day_count_convention = ''
        self.principal_debit = 0
        self.principal_amount = 0
        self.principal_currency = 'CZK'
        self.date_from = None
        self.date_to = None


class Credit:

    def __init__(self):
        self.description = ''
        self.date = None
        self.amount = 0
        self.currency = 'CZK'
        self.debits = []


class Balance:

    def __init__(self):
        self.description = ''
        self.date = None


class FXrate:

    def __init__(self):
        self.currency_from = None
        self.currency_to = None
        self.rate_from = 1
        self.rate_to = 1
        self.date_from = None
        self.date_to = None


class Result:

    pass


AID = '{} {}'.format(APP.upper(), APPVERSION)


def getdebt(request):

    asset = getasset(request, AID)
    if asset:
        try:
            return loads(asset)
        except:  # pragma: no cover
            pass
    setdebt(request, Debt())
    asset = getasset(request, AID)
    return loads(asset) if asset else None


def setdebt(request, data):

    return setasset(request, AID, dumps(data), ASSET_EXP)


def n2l(num):
    """
    Convert debt number 'num' to letter.
    """

    return chr(ord('A') + num) if num <= (ord('Z') - ord('A')) else '?'


DR, CR, BAL = tuple(range(3))


def rmdsl(lst):
    """
    Remove duplicate elements from list 'lst'.
    """

    if lst:
        elem = lst[-1]
        for idx in range((len(lst) - 2), -1, -1):
            if elem == lst[idx]:
                del lst[idx]
            else:
                elem = lst[idx]
    return lst


def calcint(interest, pastdate, presdate, debt, res):

    if not pastdate or pastdate < (interest.default_date - ODP):
        pastdate = interest.default_date - ODP

    if interest.date_to and interest.date_to < presdate:
        presdate = interest.date_to

    if pastdate >= presdate:
        return .0, None

    principal = (
        debt.debits[interest.principal_debit - 1].balance if interest.principal_debit else interest.principal_amount)

    if interest.model == 'per_annum':
        return principal * yfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100, None

    if interest.model == 'per_mensem':
        return principal * mfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100, None

    if interest.model == 'per_diem':
        return principal * (presdate - pastdate).days * interest.rate / 1000, None

    if interest.model == 'cust1':
        rate = get_mpi_rate('DISC', interest.default_date, log=res.mpi)
        if rate[1]:
            return None, rate[1]
        return (principal * yfactor(pastdate, presdate, 'ACT/ACT') * rate[0] / 50), None

    if interest.model == 'cust2':
        temp = 0
        dat = pastdate
        while True:
            dat += ODP
            year1 = dat.year
            month1 = dat.month
            day1 = 1
            month1 = 7 if month1 > 6 else 1
            rate = get_mpi_rate('REPO', date(year1, month1, day1), log=res.mpi)
            if rate[1]:
                return None, rate[1]
            year2 = year1
            if year1 < presdate.year or (month1 == 1 and presdate.month > 6):
                if month1 == 1:
                    month2 = 6
                    day2 = 30
                else:
                    month2 = 12
                    day2 = 31
                newt = date(year2, month2, day2)
                temp += yfactor(dat - ODP, newt, 'ACT/ACT') * (rate[0] + 7)
                dat = newt
            else:
                month2 = presdate.month
                day2 = presdate.day
                return (
                    principal * (temp + yfactor(dat - ODP, date(year2, month2, day2), 'ACT/ACT') * (rate[0] + 7)) / 100,
                    None)

    if interest.model == 'cust3':
        year = interest.default_date.year
        month = interest.default_date.month
        day = interest.default_date.day
        if month > 6:
            month = 6
            day = 30
        else:
            month = 12
            day = 31
            year -= 1
        rate = get_mpi_rate('REPO', date(year, month, day), log=res.mpi)
        if rate[1]:
            return None, rate[1]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') * (rate[0] + 7) / 100, None

    if interest.model == 'cust5':
        year = interest.default_date.year
        month = interest.default_date.month
        day = interest.default_date.day
        if month > 6:
            month = 6
            day = 30
        else:
            month = 12
            day = 31
            year -= 1
        rate = get_mpi_rate('REPO', date(year, month, day), log=res.mpi)
        if rate[1]:
            return None, rate[1]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') * (rate[0] + 8) / 100, None

    if interest.model == 'cust6':
        year = interest.default_date.year
        month = interest.default_date.month
        month = 7 if month > 6 else 1
        rate = get_mpi_rate('REPO', date(year, month, 1), log=res.mpi)
        if rate[1]:
            return None, rate[1]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') * (rate[0] + 8) / 100, None

    if interest.model == 'cust4':
        return principal * (presdate - pastdate).days / 400, None

    return None, 'Neznámý model'


def distr(debt, dat, credit, amt, disarr, res):

    if amt < LIM:
        return 0, None
    for idx in credit.debits:
        debit = debt.debits[idx]
        if debit.newb >= LIM:
            if credit.currency == debit.currency:
                ratio = 1
            else:
                for fxrate in debt.fxrates:
                    if (fxrate.currency_from == credit.currency and fxrate.currency_to == debit.currency
                        and (not fxrate.date_from or fxrate.date_from <= dat)
                        and (not fxrate.date_to or dat <= fxrate.date_to)):
                        ratio = fxrate.rate_to / fxrate.rate_from
                        break
                else:
                    if credit.currency == 'CZK':
                        rcl = 1
                    else:
                        rate, qty, dummy, msg = get_fx_rate(
                            credit.currency,
                            dat,
                            log=res.fxinfo,
                            use_fixed=True,
                            log_fixed=res.fix)
                        if msg:
                            return .0, msg
                        rcl = rate / qty
                    if debit.currency == 'CZK':
                        rld = 1
                    else:
                        rate, qty, dummy, msg = get_fx_rate(
                            debit.currency,
                            dat,
                            log=res.fxinfo,
                            use_fixed=True,
                            log_fixed=res.fix)
                        if msg:
                            return 0, msg
                        rld = rate / qty
                    ratio = rcl / rld
            camt = amt * ratio
            if camt < debit.newb:
                debit.newb -= camt
                debit.newb = round(debit.newb, debt.rounding)
                disarr[idx] += camt
                return 0, None
            disarr[idx] += debit.newb
            amt -= debit.newb / ratio
            debit.newb = 0
    return amt, None


def calc(debt, pram=lambda x: x):

    res = Result()

    res.msg = None
    res.rows = []
    res.fxinfo = []
    res.fix = []
    res.mpi = []

    res.newd = len(debt.debits)
    res.newc = len(debt.credits)
    res.newb = len(debt.balances)
    res.newfx = len(debt.fxrates)

    res.ids = []
    for idx, debit in enumerate(debt.debits):
        debit.id = n2l(idx)
        res.ids.append(debit.id)

    res.currencies = []
    for debit in debt.debits:
        if debit.model == 'fixed':
            curr = debit.fixed_currency
        elif debit.principal_debit:
            curr = debt.debits[debit.principal_debit - 1].fixed_currency
        else:
            curr = debit.principal_currency
        debit.currency = curr
        debit.disp_currency = curr
        if curr not in res.currencies:
            res.currencies.append(curr)
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

    drat = {}
    cust4 = []
    ncust4 = []
    for idx, debit in enumerate(debt.debits):
        debit.balance = 0.0
        if debit.model == 'fixed':
            dat = debit.fixed_date
            if dat not in drat:
                drat[dat] = []
            drat[dat].append(idx)
        else:
            debit.default_date = (
                debit.date_from + ODP if debit.date_from else debt.debits[debit.principal_debit - 1].fixed_date + ODP)
            if debit.model == 'cust4':
                cust4.append(debit)
                debit.mb = debit.default_date
                debit.mm = 25 if debit.currency == 'CZK' else 0
                debit.ui = debit.li = 0
            else:
                ncust4.append(debit)
    irs = cust4 + ncust4

    crd = {}
    for idx, credit in enumerate(debt.credits):
        credit.sp = 0
        dat = credit.date
        if dat not in crd:
            crd[dat] = []
        crd[dat].append(idx)
    bald = {}
    for idx, balance in enumerate(debt.balances):
        dat = balance.date
        if dat not in bald:
            bald[dat] = []
        bald[dat].append(idx)

    tra = []
    for dat, lst in drat.items():
        for idx in lst:
            tra.append({
                'type': DR,
                'date': dat,
                'id': idx,
                'object': debt.debits[idx],
            })
    for dat, lst in crd.items():
        for idx in lst:
            tra.append({
                'type': CR,
                'date': dat,
                'id': idx,
                'object': debt.credits[idx],
            })
    for dat, lst in bald.items():
        for idx in lst:
            tra.append({
                'type': BAL,
                'date': dat,
                'id': idx,
                'object': debt.balances[idx],
            })
    tra.sort(key=lambda x: x['type'])
    tra.sort(key=lambda x: x['date'])

    res.newd3 = res.newd * 3
    if res.newd:
        res.hrow = True
        res.crow = res.ccol = res.multicurrency
        res.scol = not res.multicurrency_debit and res.newd > 1
        res.cnt1 = 3 if res.crow else 2
        res.cnt2 = res.newd
        res.cnt3 = res.newd + (1 if res.scol else 0)
        res.cnt4 = (res.newd * 3) + 3 + (1 if res.scol else 0) + (1 if res.ccol else 0)
    else:
        res.hrow = res.crow = res.ccol = res.scol = False
        res.cnt1 = res.cnt2 = res.cnt3 = 1
        res.cnt4 = 6
    res.rng3 = list(range(3))

    if not tra:
        return res

    dat = tra[0]['date']
    for itr in irs:
        dat = min(dat, itr.default_date)
    dat -= ODP
    eps = 0
    cud = None
    while dat <= tra[-1]['date']:
        for itr in cust4:
            if dat >= itr.default_date and (not itr.date_to or dat <= itr.date_to):
                if dat == itr.mb:
                    itr.li = 0
                    itr.ui = itr.mm
                iitr = debt.debits[itr.principal_debit - 1].balance if itr.principal_debit else itr.principal_amount
                iitr /= 400
                iitr = max(iitr, 0)
                itr.li += iitr
                if itr.li > itr.ui:
                    ditr = itr.li - itr.ui
                    itr.ui = itr.li
                else:
                    ditr = 0.0
                if dat == itr.mb:
                    ditr += itr.mm
                    day = itr.default_date.day
                    month = dat.month + 1
                    year = dat.year
                    if month > 12:
                        month = 1
                        year += 1
                    day = min(day, monthrange(year, month)[1])
                    itr.mb = date(year, month, day)
                itr.balance += ditr

        while eps < len(tra) and tra[eps]['date'] == dat:
            trn = tra[eps]
            for debit in debt.debits:
                debit.newb = debit.balance
            for itr in ncust4:
                aitr, res.msg = calcint(itr, cud, dat, debt, res)
                if res.msg:  # pragma: no cover
                    return res
                itr.newb += aitr
            obj = trn['object']
            row = {
                'object': obj,
                'date': dat,
                'description': obj.description,
                'amount': pram(0.0),
                'pre': [],
                'change': [],
                'post': [],
                'pre_total': 0,
                'post_total': 0,
                'cr_distr': [0] * res.newd,
                'sp_distr': [0] * res.newd,
                'sps': [],
                'currency': '',
                'disp_currency': '',
            }
            typ = row['type'] = trn['type']
            for debit in debt.debits:
                debit.ob = debit.newb = round(debit.newb, debt.rounding)
                if typ == BAL:
                    row['pre'].append(pram(0))
                else:
                    row['pre'].append(pram(debit.newb))
                    row['pre_total'] += debit.newb
            if typ == DR:
                row['id'] = obj.id
                row['amount'] = pram(obj.fixed_amount)
                obj.newb += obj.fixed_amount
                obj.newb = round(obj.newb, debt.rounding)
            for credit in debt.credits:
                credit.nsp, res.msg = distr(debt, dat, credit, credit.sp, row['sp_distr'], res)
                if res.msg:
                    return res
            if typ == CR:
                row['amount'] = pram(-obj.amount)
                row['debits'] = obj.debits
                spa, res.msg = distr(debt, dat, obj, obj.amount, row['cr_distr'], res)
                if res.msg:
                    return res
                obj.nsp += spa
            for debit in debt.debits:
                row['post'].append(pram(debit.newb))
                if not res.multicurrency_debit:
                    row['post_total'] += debit.newb
                if typ == BAL:
                    row['change'].append(pram(0))
                else:
                    row['change'].append(pram(debit.newb - debit.ob))
            if typ == DR and obj.model == 'fixed':
                row['disp_currency'] = obj.fixed_currency
            elif typ == CR:
                row['disp_currency'] = obj.currency
            if not res.multicurrency_debit:
                row['post_total'] = pram(round(row['post_total'], debt.rounding))

            for credit in debt.credits:
                if credit.nsp > LIM:
                    for spa in row['sps']:
                        if spa['curr'] == credit.currency:
                            spa['total'] += credit.nsp
                            break
                    else:
                        row['sps'].append({
                            'curr': credit.currency,
                            'total': credit.nsp,
                        })
            row['sps'].sort(key=lambda x: x['curr'])

            lst = []
            for spa in row['sps']:
                lst.append('{} {}'.format(
                    pram(spa['total']),
                    spa['curr'] if res.multicurrency or spa['curr'] != 'CZK' else 'Kč'))
            row['sps_text'] = ', '.join(lst)

            if typ != BAL:
                for debit in debt.debits:
                    debit.balance = debit.newb
                for credit in debt.credits:
                    credit.sp = credit.nsp
                cud = dat

            res.rows.append(row)
            eps += 1

        dat += ODP

    return res


def to_xml(debt):

    dec = {
        'debt': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'.format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
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
    xml = new_xml('')
    tdebt = xml_decorate(xml.new_tag('debt'), dec)
    xml.append(tdebt)
    for key in ('title', 'note', 'internal_note'):
        tag = xml.new_tag(key)
        tag.append(xml_escape(debt.__getattribute__(key)))
        tdebt.append(tag)
    tag = xml.new_tag('rounding')
    tag.append(str(debt.rounding))
    tdebt.append(tag)

    tdebs = xml.new_tag('debits')
    for debit in debt.debits:
        tdeb = xml.new_tag('debit')
        tdeb['model'] = model = debit.model
        tag = xml.new_tag('description')
        tag.append(xml_escape(debit.description))
        tdeb.append(tag)
        if model == 'fixed':
            tag = xml.new_tag('fixed_date')
            tag.append(debit.fixed_date.isoformat())
            tdeb.append(tag)
            tag = xml.new_tag('fixed_amount')
            tag.append('{:.2f}'.format(debit.fixed_amount))
            tdeb.append(tag)
            tag = xml_decorate(xml.new_tag('fixed_currency'), dec)
            tag.append(debit.fixed_currency)
            tdeb.append(tag)
        else:
            if model == 'per_annum':
                tag = xml_decorate(xml.new_tag('pa_rate'), dec)
                tag.append('{:.6f}'.format(debit.rate))
                tdeb.append(tag)
                tag = xml.new_tag('day_count_convention')
                tag.append(debit.day_count_convention)
                tdeb.append(tag)
            elif model == 'per_mensem':
                tag = xml_decorate(xml.new_tag('pm_rate'), dec)
                tag.append('{:.6f}'.format(debit.rate))
                tdeb.append(tag)
                tag = xml.new_tag('day_count_convention')
                tag.append(debit.day_count_convention)
                tdeb.append(tag)
            elif model == 'per_diem':
                tag = xml_decorate(xml.new_tag('pd_rate'), dec)
                tag.append('{:.6f}'.format(debit.rate))
                tdeb.append(tag)
            if debit.principal_debit:
                tag = xml.new_tag('principal_debit')
                tag['id'] = '{:d}'.format(debit.principal_debit - 1)
                tdeb.append(tag)
            else:
                tag = xml.new_tag('principal_amount')
                tag.append('{:.2f}'.format(debit.principal_amount))
                tdeb.append(tag)
                tag = xml_decorate(xml.new_tag('principal_currency'), dec)
                tag.append(debit.principal_currency)
                tdeb.append(tag)
            if hasattr(debit, 'date_from') and debit.date_from:
                tag = xml.new_tag('date_from')
                tag.append(debit.date_from.isoformat())
                tdeb.append(tag)
            if hasattr(debit, 'date_to') and debit.date_to:
                tag = xml.new_tag('date_to')
                tag.append(debit.date_to.isoformat())
                tdeb.append(tag)
        tdebs.append(tdeb)
    tdebt.append(tdebs)

    tcreds = xml.new_tag('credits')
    for credit in debt.credits:
        tcred = xml.new_tag('credit')
        tag = xml.new_tag('description')
        tag.append(xml_escape(credit.description))
        tcred.append(tag)
        tag = xml.new_tag('date')
        tag.append(credit.date.isoformat())
        tcred.append(tag)
        tag = xml.new_tag('amount')
        tag.append('{:.2f}'.format(credit.amount))
        tcred.append(tag)
        tag = xml_decorate(xml.new_tag('currency'), dec)
        tag.append(credit.currency)
        tcred.append(tag)
        tag = xml.new_tag('debits')
        tcred.append(tag)
        for dbs in credit.debits:
            tst = xml.new_tag('debit')
            tst['id'] = dbs
            tag.append(tst)
        tcreds.append(tcred)
    tdebt.append(tcreds)

    tbals = xml.new_tag('balances')
    for balance in debt.balances:
        tbal = xml.new_tag('balance')
        tag = xml.new_tag('description')
        tag.append(xml_escape(balance.description))
        tbal.append(tag)
        tag = xml.new_tag('date')
        tag.append(balance.date.isoformat())
        tbal.append(tag)
        tbals.append(tbal)
    tdebt.append(tbals)

    tfxs = xml.new_tag('fxrates')
    for fxrate in debt.fxrates:
        tfx = xml.new_tag('fxrate')
        tag = xml_decorate(xml.new_tag('currency_from'), dec)
        tag.append(fxrate.currency_from)
        tfx.append(tag)
        tag = xml_decorate(xml.new_tag('currency_to'), dec)
        tag.append(fxrate.currency_to)
        tfx.append(tag)
        tag = xml.new_tag('rate_from')
        tag.append('{:.3f}'.format(fxrate.rate_from))
        tfx.append(tag)
        tag = xml.new_tag('rate_to')
        tag.append('{:.3f}'.format(fxrate.rate_to))
        tfx.append(tag)
        if hasattr(fxrate, 'date_from') and fxrate.date_from:
            tag = xml.new_tag('date_from')
            tag.append(fxrate.date_from.isoformat())
            tfx.append(tag)
        if hasattr(fxrate, 'date_to') and fxrate.date_to:
            tag = xml.new_tag('date_to')
            tag.append(fxrate.date_to.isoformat())
            tfx.append(tag)
        tfxs.append(tfx)

    tdebt.append(tfxs)
    return str(xml).encode('utf-8') + b'\n'


def from_xml(dat):

    string = get_xml(dat)
    if not string:
        return None, 'Chybný formát souboru (1)'
    tdebt = string.debt
    if not (tdebt and tdebt['application'] in [APP, 'hjp']):
        return None, 'Chybný formát souboru (2)'

    if tdebt['application'] == APP:
        debt = Debt()
        debt.title = xml_unescape(tdebt.title.text.strip())
        debt.note = xml_unescape(tdebt.note.text.strip())
        debt.internal_note = xml_unescape(tdebt.internal_note.text.strip())
        debt.rounding = int(tdebt.rounding.text.strip())

        for tdebs in tdebt.debits.findAll('debit'):
            debit = Debit()
            debt.debits.append(debit)
            debit.description = xml_unescape(tdebs.description.text.strip())
            debit.model = model = tdebs['model']
            if tdebs.fixed_amount:
                debit.fixed_amount = float(tdebs.fixed_amount.text.strip())
            if tdebs.fixed_currency:
                debit.fixed_currency = tdebs.fixed_currency.text.strip()
            if tdebs.fixed_date:
                debit.fixed_date = iso2date(tdebs.fixed_date)
            if tdebs.pa_rate:
                debit.rate = float(tdebs.pa_rate.text.strip())
            if tdebs.pm_rate:
                debit.rate = float(tdebs.pm_rate.text.strip())
            if tdebs.pd_rate:
                debit.rate = float(tdebs.pd_rate.text.strip())
            if tdebs.day_count_convention:
                debit.day_count_convention = tdebs.day_count_convention.text.strip()
            if tdebs.principal_debit:
                debit.principal_debit = (int(tdebs.principal_debit['id']) + 1)
            if tdebs.principal_amount:
                debit.principal_amount = float(tdebs.principal_amount.text.strip())
            if tdebs.principal_currency:
                debit.principal_currency = tdebs.principal_currency.text.strip()
            if tdebs.date_from:
                debit.date_from = iso2date(tdebs.date_from)
            if tdebs.date_to:
                debit.date_to = iso2date(tdebs.date_to)

        for tcreds in tdebt.credits.findAll('credit'):
            credit = Credit()
            debt.credits.append(credit)
            credit.description = xml_unescape(tcreds.description.text.strip())
            credit.date = iso2date(tcreds.date)
            credit.amount = float(tcreds.amount.text.strip())
            credit.currency = tcreds.currency.text.strip()
            for tdeb in tcreds.debits.findAll('debit'):
                credit.debits.append(int(tdeb['id']))

        for tbals in tdebt.balances.findAll('balance'):
            balance = Balance()
            debt.balances.append(balance)
            balance.description = xml_unescape(tbals.description.text.strip())
            balance.date = iso2date(tbals.date)

        for tfxs in tdebt.fxrates.findAll('fxrate'):
            fxrate = FXrate()
            debt.fxrates.append(fxrate)
            fxrate.currency_from = tfxs.currency_from.text.strip()
            fxrate.currency_to = tfxs.currency_to.text.strip()
            fxrate.rate_from = float(tfxs.rate_from.text.strip())
            fxrate.rate_to = float(tfxs.rate_to.text.strip())
            if tfxs.date_from:
                fxrate.date_from = iso2date(tfxs.date_from)
            if tfxs.date_to:
                fxrate.date_to = iso2date(tfxs.date_to)

    else:
        debt = Debt()
        debt.title = xml_unescape(tdebt.title.text.strip())
        debt.note = xml_unescape(tdebt.note.text.strip())
        debt.internal_note = xml_unescape(tdebt.internal_note.text.strip())
        debt.rounding = int(tdebt.rounding.text.strip())
        currency = tdebt.currency.text.strip()
        interest = tdebt.interest
        ttrs = list(tdebt.transactions.children)
        firstfix = True
        principals = []
        interests = []
        for ttr in ttrs:
            if not ttr.name:
                continue
            if (ttr.has_attr('type') and ttr['type'] == 'debit') or str(ttr.name) == 'debit':
                debit = Debit()
                idx = len(debt.debits)
                principals.append(idx)
                debt.debits.append(debit)
                debit.model = 'fixed'
                debit.description = xml_unescape(ttr.description.text.strip())
                debit.fixed_amount = float(ttr.amount.text.strip())
                debit.fixed_currency = currency
                debit.fixed_date = iso2date(ttr.date)
                model = interest['model']
                if model != 'none' and (model != 'fixed' or firstfix):
                    firstfix = False
                    debit = Debit()
                    interests.append(len(debt.debits))
                    debt.debits.append(debit)
                    debit.description = 'Úrok'
                    debit.model = model
                    debit.principal_debit = idx + 1
                    if model == 'fixed':
                        debit.fixed_amount = float(interest.amount.text.strip())
                        debit.fixed_currency = currency
                        debit.fixed_date = iso2date(ttr.date)
                    elif model == 'per_annum':
                        debit.rate = float(interest.pa_rate.text.strip())
                        debit.day_count_convention = interest.day_count_convention.text.strip()
                    elif model == 'per_mensem':
                        debit.rate = float(interest.pm_rate.text.strip())
                        debit.day_count_convention = interest.day_count_convention.text.strip()
                    elif model == 'per_diem':
                        debit.rate = float(interest.pd_rate.text.strip())
        orderi = interests + principals
        orderp = principals + interests
        for ttr in ttrs:
            if not ttr.name:
                continue
            tt_type = str(ttr.name)
            if tt_type == 'credit':
                credit = Credit()
                debt.credits.append(credit)
                credit.description = xml_unescape(ttr.description.text.strip())
                credit.amount = float(ttr.amount.text.strip())
                credit.currency = currency
                credit.date = iso2date(ttr.date)
                credit.debits = (orderp if ttr.repayment_preference.text.strip() == 'principal' else orderi)[:]
            elif tt_type == 'balance':
                balance = Balance()
                debt.balances.append(balance)
                balance.description = xml_unescape(ttr.description.text.strip())
                balance.date = iso2date(ttr.date)
    return debt, None


EL = ['']


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    def ftbl(amt):
        amt = round(amt, debt.rounding) if debt.rounding else int(round(amt))
        if abs(amt) < LIM:
            return '<span class="dr">&#160;</span>'
        elif amt > 0:
            return '<span class="dr">{}</span>'.format(famt(amt))
        return '<span class="cr">{}</span>'.format(famt(-amt))

    def lfamt(amt, curr):
        if not amt or abs(amt) < LIM:
            return ''
        temp = famt(round(amt, debt.rounding)
            if debt.rounding else int(round(amt))).replace('-', '−')
        if res.multicurrency or curr != 'CZK':
            return '{} {}'.format(temp, curr)
        return '{} Kč'.format(temp)

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
        form = MainForm(initial=var)

    else:
        button = getbutton(request)

        if button == 'empty':
            debt = Debt()
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

        if button == 'load':
            infile = request.FILES.get('load')
            if not infile:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                try:
                    dat = infile.read()
                    infile.close()
                    debt, msg = from_xml(dat)
                    if msg:
                        raise Exception('Error reading file')
                    setdebt(request, debt)
                    return redirect('hsp:mainpage')
                except:
                    err_message = 'Chyba při načtení souboru'

        debt = getdebt(request)
        if not debt:  # pragma: no cover
            return error(request)

        form = MainForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            debt.title = cld['title'].strip()
            debt.note = cld['note'].strip()
            debt.internal_note = cld['internal_note'].strip()
            debt.rounding = int(cld['rounding'])
            setdebt(request, debt)

            if not button and cld['next']:
                return redirect(cld['next'])

            if button == 'xml':
                response = HttpResponse(
                    to_xml(debt),
                    content_type='text/xml; charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename=Pohledavka.xml'
                return response

            if button == 'csv':
                res = calc(debt)
                response = HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename=Pohledavka.csv'
                writer = csv.writer(response)
                hdr = ['Datum', 'Popis', 'Částka', 'Měna']
                for debit in debt.debits:
                    hdr.append('Předchozí zůstatek {0.id} ({0.currency})'.format(debit))
                for debit in debt.debits:
                    hdr.append('Změna {0.id} ({0.currency})'.format(debit))
                for debit in debt.debits:
                    hdr.append('Nový zůstatek {0.id} ({0.currency})'.format(debit))
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

                style4 = ParagraphStyle(
                    name='STYLE4',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
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

                style13 = ParagraphStyle(
                    name='STYLE13',
                    fontName='Bookman',
                    fontSize=8,
                    leading=12,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                style14 = ParagraphStyle(
                    name='STYLE14',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=12,
                    allowWidows=False,
                    allowOrphans=False)

                style15 = ParagraphStyle(
                    name='STYLE15',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                style17 = ParagraphStyle(
                    name='STYLE17',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                style18 = ParagraphStyle(
                    name='STYLE18',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    allowWidows=False,
                    allowOrphans=False)

                style20 = ParagraphStyle(
                    name='STYLE20',
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

                style22 = ParagraphStyle(
                    name='STYLE22',
                    fontName='BookmanI',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                style23 = ParagraphStyle(
                    name='STYLE23',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    spaceBefore=15,
                    spaceAfter=4,
                    allowWidows=False,
                    allowOrphans=False,
                    keepWithNext=True)

                style24 = ParagraphStyle(
                    name='STYLE24',
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

                style25 = ParagraphStyle(
                    name='STYLE25',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    leftIndent=24,
                    allowWidows=False,
                    allowOrphans=False)

                style26 = ParagraphStyle(
                    name='STYLE26',
                    fontName='Bookman',
                    fontSize=6,
                    leading=9,
                    spaceBefore=-2,
                    allowWidows=False,
                    allowOrphans=False)

                doc1 = (([Paragraph('Historie peněžité pohledávky'.upper(), style1)],),)
                if debt.title:
                    doc1[0][0].append(Paragraph(escape(debt.title), style2))
                table1 = Table(doc1, colWidths=(483.3,))
                table1.setStyle(
                    TableStyle((
                        ('LINEABOVE', (0, 0), (0, -1), 1.0, black),
                        ('TOPPADDING', (0, 0), (0, -1), 2),
                        ('LINEBELOW', (-1, 0), (-1, -1), 1.0, black),
                        ('BOTTOMPADDING', (-1, 0), (-1, -1), 3),
                        ('LEFTPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    )))
                flow = [table1, Spacer(0, 36)]

                bst = [
                    ('SPAN', (0, 0), (4, 0)),
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
                    ('BOTTOMPADDING', (0, 0), (-1, 0), .5),
                    ('BOTTOMPADDING', (0, 1), (-1, 1), 1.5),
                    ('BOTTOMPADDING', (0, -1), (-1, -1), 18),
                ]

                cust2eff = {
                    'cust1': 'do 27.04.2005',
                    'cust2': 'od 28.04.2005 do 30.06.2010',
                    'cust3': 'od 01.07.2010',
                    'cust5': 'od 01.07.2013 do 31.12.2013',
                }

                mpitypes = {
                    'DISC': 'diskontní sazba',
                    'REPO': '2T repo sazba',
                }

                wid = 483.3
                widl = 8
                widr = 8
                widg = 12
                widf = widc = (wid - widl - widr - (widg * 2)) / 6
                cwid = (
                    (widl,) + ((widc / 5,) * 5) + ((widf / 5,) * 5) + (widg,) + ((widc / 5,) * 5) + ((widf / 5,) * 5)
                    + (widg,) + ((widc / 5,) * 5) + ((widf / 5,) * 5) + (widr,))

                res = calc(debt)
                thickness = .5

                info = []

                if debt.debits:
                    info.append(Paragraph('Závazky:', style23))
                    for debit in debt.debits:
                        info.append(Paragraph(
                            '<b>{}</b>'.format(debit.description) if debit.description else '<i>(bez názvu)</i>',
                            style24,
                            bulletText=debit.id + '.'))
                        model = debit.model
                        if model == 'fixed':
                            txt = (
                                'pevná částka {}, splatná {:%d.%m.%Y}'
                                .format(lfamt(debit.fixed_amount, debit.fixed_currency), debit.fixed_date))
                        else:
                            if model == 'per_annum':
                                txt = (
                                    'roční úrok {0.rate:n} % <i>p. a.</i> (konvence pro počítání dnů: '
                                    '{0.day_count_convention})'.format(debit))
                            elif model == 'per_mensem':
                                txt = (
                                    'měsíční úrok {0.rate:n} % <i>p. m.</i> (konvence pro počítání dnů: '
                                    '{0.day_count_convention})'.format(debit))
                            elif model == 'per_diem':
                                txt = 'denní úrok {:n} ‰ <i>p. d.</i>'.format(debit.rate)
                            elif model in ('cust1', 'cust2', 'cust3', 'cust5'):
                                txt = (
                                    'zákonný úrok z prodlení podle nařízení vlády č. 142/1994 Sb. ve znění účinném {}'
                                    .format(cust2eff[model]))
                            elif model == 'cust6':
                                txt = 'zákonný úrok z prodlení podle nařízení vlády č. 351/2013 Sb.'
                            else:
                                txt = 'zákonný poplatek z prodlení podle nařízení vlády č. 142/1994 Sb.'
                            if debit.principal_debit:
                                txt += ' ze závazku {}'.format(n2l(debit.principal_debit - 1))
                            else:
                                txt += (
                                    ' z částky {}'.format(lfamt(debit.principal_amount, debit.principal_currency)))
                            if debit.date_from:
                                txt += ' od {:%d.%m.%Y}'.format(debit.date_from)
                            elif debit.principal_debit:
                                txt += ' od splatnosti'
                            if debit.date_to:
                                txt += ' do {:%d.%m.%Y}'.format(debit.date_to)
                            elif debit.principal_debit:
                                txt += ' do zaplacení'
                        info.append(Paragraph(txt, style25))

                if debt.fxrates:
                    info.append(Paragraph(
                        'Pevně zadané směnné kursy:',
                        style23))
                    for fxrate in debt.fxrates:
                        txt = ''
                        if fxrate.date_from:
                            txt += ' od {:%d.%m.%Y}'.format(fxrate.date_from)
                        if fxrate.date_to:
                            txt += ' do {:%d.%m.%Y}'.format(fxrate.date_to)
                        if txt:
                            txt = ' ({})'.format(txt.strip())
                        info.append(Paragraph(
                            '{0.rate_from:n} {0.currency_from} = {0.rate_to:n} {0.currency_to}{1}'.format(fxrate, txt),
                            style20,
                            bulletText='–'))

                if res.fxinfo:
                    res.fxinfo.sort(key=lambda x: x['date_required'])
                    res.fxinfo.sort(key=lambda x: x['currency'])
                    rmdsl(res.fxinfo)
                    info.append(Paragraph('Použité směnné kursy ČNB:', style23))
                    for fxr in res.fxinfo:
                        info.append(Paragraph(
                            '{0[quantity]:d} {0[currency]} = {1:.3f} CZK, platný ke dni {0[date_required]:%d.%m.%Y}'
                            .format(fxr, LocalFloat(fxr['rate'])),
                            style20,
                            bulletText='–'))

                if res.fix:
                    res.fix.sort(key=lambda x: x['currency_to'])
                    res.fix.sort(key=lambda x: x['currency_from'])
                    rmdsl(res.fix)
                    info.append(Paragraph('Použité fixní směnné poměry:', style23))
                    for fix in res.fix:
                        info.append(Paragraph(
                            '{0} {1[currency_from]} = 1 {1[currency_to]}, platný od {1[date_from]:%d.%m.%Y}'
                            .format(famt(fix['rate']), fix),
                            style20,
                            bulletText='–'))

                if res.mpi:
                    res.mpi.sort(key=(lambda x: x['date']))
                    res.mpi.sort(key=(lambda x: x['type']))
                    rmdsl(res.mpi)
                    info += [Paragraph(('Použité úrokové sazby ČNB:'), style23)]
                    for mpi in res.mpi:
                        info.append(Paragraph(
                            '{} ke dni {:%d.%m.%Y}: {:.2f} % <i>p. a.</i>'
                            .format(mpitypes[mpi['type']], mpi['date'], LocalFloat(mpi['rate'])),
                            style20,
                            bulletText='–'))

                info.append(Spacer(0, 50))
                flow.extend(info)

                for row in res.rows:

                    typ = row['type']
                    spf = bool(row['sps'])

                    hdr = EL * 3
                    lin = ([0] * 3)
                    cleft = [[], [], []]
                    cright = [[], [], []]

                    if typ == DR:
                        hdr[0] = 'Závazek'
                        lin[0] = 1
                        cleft[0].append(row['id'])
                        cright[0].append((row['amount'], row['disp_currency']))

                    if typ == CR:
                        hdr[0] = 'Splátka'
                        lin[0] = 1
                        cleft[0].append('∑')
                        cright[0].append((-row['amount'], row['disp_currency']))
                        for debit, amount in zip(debt.debits, row['cr_distr']):
                            if abs(amount) > LIM:
                                lin[0] += 1
                                cleft[0].append(debit.id)
                                cright[0].append((amount, debit.currency))

                    if typ in (DR, CR):
                        for itm in row['pre']:
                            if abs(itm) > LIM:
                                hdr[1] = 'Předchozí zůstatek'
                                for debit, amount in zip(debt.debits, row['pre']):
                                    if abs(amount) > LIM:
                                        lin[1] += 1
                                        cleft[1].append(debit.id)
                                        cright[1].append((amount, debit.currency))
                                if not res.multicurrency_debit and lin[1] > 1:
                                    lin[1] += 1
                                    cleft[1].append('∑')
                                    cright[1].append((row['pre_total'], res.currency_debits))
                                break

                    if spf:
                        hdr[2] = 'Přeplatek'
                        for spa in row['sps']:
                            lin[2] += 1
                            cleft[2].append('∑')
                            cright[2].append((spa['total'], spa['curr']))
                    else:
                        hdr[2] = 'Nový zůstatek' if hdr[1] else 'Zůstatek'
                        for debit, amount in zip(debt.debits, row['post']):
                            if abs(amount) > LIM:
                                lin[2] += 1
                                cleft[2].append(debit.id)
                                cright[2].append((amount, debit.currency))
                        if not res.multicurrency_debit and lin[2] > 1:
                            lin[2] += 1
                            cleft[2].append('∑')
                            cright[2].append((row['post_total'], res.currency_debits))

                    lmax = max(lin)

                    for idx in range(3):
                        while len(cleft[idx]) < lmax:
                            cleft[idx].append('')
                        while len(cright[idx]) < lmax:
                            cright[idx].append((None, None))

                    ast = [
                        ('RIGHTPADDING', (2, 2), (10, 1 + lmax), 0),
                        ('RIGHTPADDING', (13, 2), (21, 1 + lmax), 0),
                        ('RIGHTPADDING', (24, 2), (32, 1 + lmax), 0),
                        ('BOTTOMPADDING', (0, 2), (-1, 1 + lmax), 0),
                    ]

                    for idx in range(lmax):
                        ast.extend([
                            ('SPAN', (2, 2 + idx), (10, 2 + idx)),
                            ('SPAN', (13, 2 + idx), (21, 2 + idx)),
                            ('SPAN', (24, 2 + idx), (32, 2 + idx)),
                        ])

                    for idx in range(3):
                        if hdr[idx]:
                            ast.append(('LINEBELOW', (1 + (11 * idx), 1), (10 + (11 * idx), 1), thickness, black))
                        if lin[idx]:
                            ast.append(
                                ('LINEAFTER', (1 + (11 * idx), 2), (1 + (11 * idx), 1 + lin[idx]), thickness, black))

                    doc3 = []
                    temp1 = [Paragraph('{:%d.%m.%Y}'.format(row['date']), style13)] + (EL * 4)
                    temp2 = Paragraph(
                        escape(row['description']).upper() if row['description'] else '<i>(bez názvu)</i>',
                        style14)
                    if typ == CR:
                        if len(row['debits']) > 1:
                            temp2 = (
                                temp2,
                                Paragraph('Pořadí závazků: {}'.format(' – '.join(map(n2l, row['debits']))), style26))
                    temp2 = [temp2] + (EL * 28)
                    doc3.extend([temp1 + temp2])

                    temp = (
                        EL + [Paragraph(hdr[0], style15)] + (EL * 10) + [Paragraph(hdr[1], style15)] + (EL * 10)
                        + [Paragraph(hdr[2], style15), ''])
                    doc3.extend([temp])

                    for idx in range(lmax):
                        temp = (
                            EL + [Paragraph(cleft[0][idx], style17)] + [Paragraph(lfamt(*cright[0][idx]), style18)]
                            + (EL * 9) + [Paragraph(cleft[1][idx], style17)]
                            + [Paragraph(lfamt(*cright[1][idx]), style18)] + (EL * 9)
                            + [Paragraph(cleft[2][idx], style17)] + [Paragraph(lfamt(*cright[2][idx]), style18)]
                            + (EL * 9))
                        doc3.extend([temp])

                    temp = (EL * 34)
                    doc3.extend([temp])

                    table3 = Table(doc3, colWidths=cwid)
                    table3.setStyle(TableStyle(bst + ast))
                    flow.append(KeepTogether(table3))

                if res.msg:
                    flow.extend(
                        [Spacer(0, 20),
                         Paragraph(
                             '(pro další transakce nejsou k disposici data, při výpočtu došlo k chybě)', style22)])

                if debt.note:
                    flow.append(Spacer(0, 24))
                    temp = [Paragraph('Poznámka:'.upper(), style4)]
                    for note in filter(bool, debt.note.strip().split('\n')):
                        temp.append(Paragraph(escape(note), style12))
                    flow.append(KeepTogether(temp[:2]))
                    if len(temp) > 2:
                        flow.extend(temp[2:])
                temp = BytesIO()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=Pohledavka.pdf'
                auth = '{} V{}'.format(APP.upper(), APPVERSION)
                doc = SimpleDocTemplate(
                    temp,
                    pagesize=A4,
                    title='Historie peněžité pohledávky',
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
                    xml=to_xml(debt))
                response.write(temp.getvalue())
                return response

    res = calc(debt, ftbl)

    for num, debit in enumerate(debt.debits):
        debit.id = n2l(num)
        model = debit.model
        if model == 'fixed':
            txt = (
                'pevná částka {}, splatná {:%d.%m.%Y}'
                .format(lfamt(debit.fixed_amount, debit.fixed_currency), debit.fixed_date))
        else:
            if model == 'per_annum':
                txt = 'roční úrok {:n} % <i>p. a.</i>'.format(debit.rate)
            elif model == 'per_mensem':
                txt = 'měsíční úrok {:n} % <i>p. m.</i>'.format(debit.rate)
            elif model == 'per_diem':
                txt = 'denní úrok {:n} ‰ <i>p. d.</i>'.format(debit.rate)
            elif model in ['cust1', 'cust2', 'cust3', 'cust5', 'cust6']:
                txt = 'zákonný úrok z prodlení'
            else:
                txt = 'zákonný poplatek z prodlení'
            if debit.principal_debit:
                txt += ' ze závazku {}'.format(n2l(debit.principal_debit - 1))
            else:
                txt += ' z částky {}'.format(
                    lfamt(debit.principal_amount, debit.principal_currency))
            if debit.date_from:
                txt += ' od {:%d.%m.%Y}'.format(debit.date_from)
            elif debit.principal_debit:
                txt += ' od splatnosti'
            if debit.date_to:
                txt += ' do {:%d.%m.%Y}'.format(debit.date_to)
            elif debit.principal_debit:
                txt += ' do zaplacení'
        debit.text = txt

    for credit in debt.credits:
        credit.text = 'částka {}'.format(lfamt(credit.amount, credit.currency))
        if len(debt.debits) > 1:
            credit.text += ', pořadí: {}'.format(' → '.join(map(n2l, credit.debits)))

    scr = debt.credits[:]
    idx = 1
    for ccr in scr:
        ccr.id = idx
        idx += 1
    scr.sort(key=lambda x: x.date)

    sbal = debt.balances[:]
    idx = 1
    for bbal in sbal:
        bbal.id = idx
        idx += 1
    sbal.sort(key=lambda x: x.date)

    return render(
        request,
        'hsp_mainpage.xhtml',
        {'app': APP,
         'page_title': 'Historie složené peněžité pohledávky',
         'form': form,
         'debt': debt,
         'res': res,
         'sc': scr,
         'sb': sbal,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def debitform(request, idx=0):

    LOGGER.debug('Debit form accessed using method {}, id={}'.format(request.method, idx), request, request.POST)

    page_title = 'Úprava závazku' if idx else 'Nový závazek'
    var = {}
    err_message = ''
    idx = int(idx)
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    fields.AmountField.rounding = debt.rounding
    numd = len(debt.debits)

    rows = [{'value': 0, 'text': 'pevné částky:', 'sel': False}]
    for num, deb in enumerate(debt.debits):
        if deb.model == 'fixed' and (not idx or num != (idx - 1)):
            row = {
                'value': num + 1,
                'text': '{} – {}'.format(n2l(num), deb.description if deb.description else '(bez názvu)'),
                'sel': False,
            }
            rows.append(row)

    if request.method == 'GET':
        if idx:
            if idx > numd:
                raise Http404
            debit = debt.debits[idx - 1]
            var['description'] = debit.description
            var['model'] = model = debit.model
            if model == 'fixed':
                var['fixed_amount'] = debit.fixed_amount
                var['fixed_currency'] = debit.fixed_currency
                var['fixed_date'] = debit.fixed_date
            elif model == 'per_annum':
                var['pa_rate'] = debit.rate
                var['ydconv'] = debit.day_count_convention
            elif model == 'per_mensem':
                var['pm_rate'] = debit.rate
                var['mdconv'] = debit.day_count_convention
            elif model == 'per_diem':
                var['pd_rate'] = debit.rate
            for row in rows:
                if row['value'] == debit.principal_debit:
                    row['sel'] = True
                    break
            else:  # pragma: no cover
                rows[0]['sel'] = True
            if model != 'fixed':
                var['date_from'] = debit.date_from
                var['date_to'] = debit.date_to
                if debit.principal_debit == 0:
                    var['principal_amount'] = debit.principal_amount
                    var['principal_currency'] = debit.principal_currency
            for debit in debt.debits:
                if debit.principal_debit == idx:
                    var['lock_fixed'] = True
                    break
            form = DebitForm(initial=var)
        else:
            rows[0]['sel'] = True
            form = DebitForm()
    else:
        form = DebitForm(request.POST)

        button = getbutton(request)
        if button == 'back':
            return redirect('hsp:mainpage')
        else:
            if request.POST.get('principal_debit'):
                for row in rows:
                    if row['value'] == int(request.POST['principal_debit']):
                        row['sel'] = True
                        break
            if idx and request.POST.get('model') != 'fixed':
                for debit in debt.debits:
                    if debit.principal_debit == idx:
                        err_message = 'Na závazek se váže úrok, vyžaduje pevnou částku'
            if not err_message and form.is_valid():
                cld = form.cleaned_data
                debit = Debit()
                debit.description = cld['description'].strip()
                debit.model = model = cld['model']
                if model == 'fixed':
                    debit.fixed_amount = cld['fixed_amount']
                    debit.fixed_currency = cld['fixed_currency'].upper()
                    debit.fixed_date = cld['fixed_date']
                elif model == 'per_annum':
                    debit.rate = cld['pa_rate']
                    debit.day_count_convention = cld['ydconv']
                elif model == 'per_mensem':
                    debit.rate = cld['pm_rate']
                    debit.day_count_convention = cld['mdconv']
                elif model == 'per_diem':
                    debit.rate = cld['pd_rate']
                if model != 'fixed':
                    debit.date_from = cld['date_from']
                    debit.date_to = cld['date_to']
                    debit.principal_debit = cld['principal_debit']
                    if debit.principal_debit == 0:
                        debit.principal_amount = cld['principal_amount']
                        debit.principal_currency = cld['principal_currency'].upper()
                if idx:
                    if idx > numd:
                        raise Http404
                    debt.debits[idx - 1] = debit
                else:
                    debt.debits.append(debit)
                    for credit in debt.credits:
                        credit.debits.append(numd)
                if not setdebt(request, debt):  # pragma: no cover
                    return error(request)
                return redirect('hsp:mainpage')

            else:
                LOGGER.debug('Invalid form', request)
                if not err_message:
                    err_message = INERR

    return render(
        request,
        'hsp_debitform.xhtml',
        {'app': APP,
         'form': form,
         'rows': rows,
         'page_title': page_title,
         'ydconvs': YDCONVS,
         'mdconvs': MDCONVS,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def debitdel(request, idx=0):

    LOGGER.debug('Debit delete page accessed using method {}, id={}'.format(request.method, idx), request, request.POST)
    idx = int(idx) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    numd = len(debt.debits)
    if idx >= numd:
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_debitdel.xhtml',
            {'app': APP,
             'page_title': 'Smazání závazku'})
    else:
        button = getbutton(request)
        if button == 'yes':
            temp = list(range(numd))
            for num in range(numd - 1, -1, -1):
                if num == idx or (debt.debits[num].principal_debit - 1) == idx:
                    temp[num] = None
                    del debt.debits[num]
            lst = [x for x in temp if x is not None]
            temp = [None if x is None else lst.index(x) for x in temp]
            for credit in debt.credits:
                lst = []
                for num in credit.debits:
                    if temp[num] != None:
                        lst.append(temp[num])
                credit.debits = lst
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:debitdeleted')
        return redirect('hsp:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def creditform(request, idx=0):

    LOGGER.debug('Credit form accessed using method {}, id={}'.format(request.method, idx), request, request.POST)

    page_title = 'Úprava splátky' if idx else 'Nová splátka'
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    fields.AmountField.rounding = debt.rounding
    rows = []
    numd = len(debt.debits)
    deb_class = ''
    if numd > 1:
        for num in range(len(debt.debits)):
            row = {'n': num, 'cols': []}
            for num2 in range(len(debt.debits)):
                row['cols'].append(
                    {'n': num2,
                     'id': n2l(num2),
                     'desc': debt.debits[num2].description})
            rows.append(row)
    idx = int(idx)
    if request.method == 'GET':
        if idx:
            if idx > len(debt.credits):
                raise Http404
            credit = debt.credits[idx - 1]
            var = {
                'description': credit.description,
                'date': credit.date,
                'amount': credit.amount,
                'currency': credit.currency,
            }
            form = CreditForm(initial=var)
            if numd > 1:
                for num in range(len(debt.debits)):
                    rows[num]['sel'] = credit.debits[num]
        else:
            form = CreditForm()
            if numd > 1:
                if hasattr(debt, 'last_debits') and len(debt.last_debits) == numd:
                    for num in range(len(debt.debits)):
                        rows[num]['sel'] = debt.last_debits[num]
                else:
                    for num in range(len(debt.debits)):
                        rows[num]['sel'] = num
    else:
        form = CreditForm(request.POST)

        button = getbutton(request)
        if button == 'back':
            return redirect('hsp:mainpage')
        else:
            if numd > 1:
                lst = []
                for num in range(numd):
                    txt = request.POST['r{:d}'.format(num)]
                    if txt in lst:
                        deb_class = 'err'
                        break
                    else:
                        lst.append(txt)
            if form.is_valid() and not deb_class:
                cld = form.cleaned_data
                credit = Credit()
                credit.description = cld['description'].strip()
                credit.date = cld['date']
                credit.amount = cld['amount']
                credit.currency = cld['currency'].upper()
                if numd > 1:
                    for num in range(numd):
                        credit.debits.append(int(
                            request.POST['r{:d}'.format(num)]))
                elif numd:
                    credit.debits = [0]
                if idx:
                    if idx > len(debt.credits):
                        raise Http404
                    debt.credits[idx - 1] = credit
                else:
                    debt.credits.append(credit)
                debt.last_debits = credit.debits
                if not setdebt(request, debt):  # pragma: no cover
                    return error(request)
                return redirect('hsp:mainpage')

            else:
                LOGGER.debug('Invalid form', request)
                err_message = INERR
                if numd > 1:
                    for num in range(numd):
                        rows[num]['sel'] = int(request.POST['r{:d}'.format(num)])

    return render(
        request,
        'hsp_creditform.xhtml',
        {'app': APP,
         'form': form,
         'rows': rows,
         'page_title': page_title,
         'err_message': err_message,
         'deb_class': deb_class})


@require_http_methods(('GET', 'POST'))
@login_required
def creditdel(request, idx=0):

    LOGGER.debug(
        'Credit delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    idx = int(idx) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if idx >= len(debt.credits):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_creditdel.xhtml',
            {'app': APP,
             'page_title': 'Smazání splátky',
             'date': debt.credits[idx].date})
    else:
        button = getbutton(request)
        if button == 'yes':
            del debt.credits[idx]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:creditdeleted')
        return redirect('hsp:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def balanceform(request, idx=0):

    LOGGER.debug(
        'Balance form accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)

    page_title = 'Úprava kontrolního bodu' if idx else 'Nový kontrolní bod'
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    idx = int(idx)
    if request.method == 'GET':
        if idx:
            if idx > len(debt.balances):
                raise Http404
            balance = debt.balances[idx - 1]
            var = {'description': balance.description, 'date': balance.date}
            form = BalanceForm(initial=var)
        else:
            form = BalanceForm()
    else:
        form = BalanceForm(request.POST)

        button = getbutton(request)
        if button == 'back':
            return redirect('hsp:mainpage')
        if button == 'set_date':
            form.data = form.data.copy()
            form.data['date'] = date.today()
        elif form.is_valid():
            cld = form.cleaned_data
            balance = Balance()
            balance.description = cld['description'].strip()
            balance.date = cld['date']
            if idx:
                if idx > len(debt.balances):
                    raise Http404
                debt.balances[idx - 1] = balance
            else:
                debt.balances.append(balance)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR

    return render(
        request,
        'hsp_balanceform.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def balancedel(request, idx=0):

    LOGGER.debug(
        'Balance delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    idx = int(idx) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if idx >= len(debt.balances):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_balancedel.xhtml',
            {'app': APP,
             'page_title': 'Smazání kontrolního bodu',
             'date': debt.balances[idx].date})
    else:
        button = getbutton(request)
        if button == 'yes':
            del debt.balances[idx]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:balancedeleted')
        return redirect('hsp:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def fxrateform(request, idx=0):

    LOGGER.debug('FX rate form accessed using method {}, id={}'.format(request.method, idx), request, request.POST)

    page_title = 'Úprava kursu' if idx else 'Nový kurs'
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    idx = int(idx)
    if request.method == 'GET':
        if idx:
            if idx > len(debt.fxrates):
                raise Http404
            fxrate = debt.fxrates[idx - 1]
            var = {
                'currency_from': fxrate.currency_from,
                'currency_to': fxrate.currency_to,
                'rate_from': fxrate.rate_from,
                'rate_to': fxrate.rate_to,
                'date_from': fxrate.date_from,
                'date_to': fxrate.date_to
            }
            form = FXform(initial=var)
        else:
            form = FXform()
    else:
        form = FXform(request.POST)

        button = getbutton(request)
        if button == 'back':
            return redirect('hsp:mainpage')
        if form.is_valid():
            cld = form.cleaned_data
            fxrate = FXrate()
            fxrate.currency_from = cld['currency_from'].upper()
            fxrate.currency_to = cld['currency_to'].upper()
            fxrate.rate_from = cld['rate_from']
            fxrate.rate_to = cld['rate_to']
            fxrate.date_from = cld['date_from']
            fxrate.date_to = cld['date_to']
            if idx:
                if idx > len(debt.fxrates):
                    raise Http404
                debt.fxrates[idx - 1] = fxrate
            else:
                debt.fxrates.append(fxrate)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:mainpage')

        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR

    return render(
        request,
        'hsp_fxrateform.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'display_note': True})


@require_http_methods(('GET', 'POST'))
@login_required
def fxratedel(request, idx=0):

    LOGGER.debug(
        'FX rate delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    idx = int(idx) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if idx >= len(debt.fxrates):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hsp_fxratedel.xhtml',
            {'app': APP,
             'page_title':
             'Smazání kursu',
             'fxrate': debt.fxrates[idx]})
    else:
        button = getbutton(request)
        if button == 'yes':
            del debt.fxrates[idx]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hsp:fxratedeleted')
        return redirect('hsp:mainpage')
