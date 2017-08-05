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

from datetime import date, datetime
from calendar import monthrange
from pickle import dumps, loads
from xml.sax.saxutils import escape
import csv
from io import BytesIO

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

from common.glob import (
    YDCONVS, MDCONVS, LIM, INERR, LOCAL_SUBDOMAIN, LOCAL_URL, ASSET_EXP)
from common.utils import (
    getbutton, yfactor, mfactor, ODP, famt, xml_decorate,
    xml_espace, xml_unespace, normfl, LocalFloat, get_xml, new_xml,
    iso2date, register_fonts, make_pdf, logger)
from common.views import error
from cache.utils import getasset, setasset
from cnb.utils import get_mpi_rate
from hjp.forms import MainForm, TransForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version


class Debt:

    def __init__(self):
        self.title = ''
        self.note = ''
        self.internal_note = ''
        self.currency = 'CZK'
        self.rounding = 0
        self.interest = Interest()
        self.transactions = []
        self.rates = {}


class Interest:

    def __init__(self):
        self.model = 'none'


class Transaction:

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


def dispcurr(curr):

    return 'Kč' if curr == 'CZK' else curr


def calcint(pastdate, presdate, principal, debt, default_date):

    interest = debt.interest

    if interest.model == 'none':
        return .0, None

    if interest.model == 'fixed':
        return .0 if pastdate else interest.fixed_amount, None

    if not pastdate or pastdate > presdate:
        return None, 'Chybný interval'

    if pastdate < (default_date - ODP):
        pastdate = default_date - ODP

    if pastdate >= presdate:
        return .0, None

    if interest.model == 'per_annum':
        return principal * yfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100, None

    if interest.model == 'per_mensem':
        return principal * mfactor(pastdate, presdate,
            interest.day_count_convention) * interest.rate / 100, None

    if interest.model == 'per_diem':
        return principal * (presdate - pastdate).days \
            * interest.rate / 1000, None

    if interest.model == 'cust1':
        rate = get_mpi_rate('DISC', default_date)
        if rate[1]:
            return None, rate[1]
        debt.rates[default_date] = rate[0]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') \
            * rate[0] / 50, None

    if interest.model == 'cust2':
        temp = 0
        dat = pastdate
        while True:
            dat += ODP
            year1 = dat.year
            month1 = dat.month
            day1 = 1
            if month1 > 6:
                month1 = 7
            else:
                month1 = 1
            rate = get_mpi_rate('REPO', date(year1, month1, day1))
            if rate[1]:
                return None, rate[1]
            debt.rates[date(year1, month1, day1)] = rate[0]
            year2 = year1
            if year1 < presdate.year or (month1 == 1 and presdate.month > 6):
                if month1 == 1:
                    month2 = 6
                    day2 = 30
                else:
                    month2 = 12
                    day2 = 31
                ndat = date(year2, month2, day2)
                temp += yfactor((dat - ODP), ndat, 'ACT/ACT') * (rate[0] + 7)
                dat = ndat
            else:
                month2 = presdate.month
                day2 = presdate.day
                return principal * (temp + yfactor(dat - ODP,
                    date(year2, month2, day2), 'ACT/ACT') \
                    * (rate[0] + 7)) / 100, None

    if interest.model == 'cust3':
        year = default_date.year
        month = default_date.month
        day = default_date.day
        if month > 6:
            month = 6
            day = 30
        else:
            month = 12
            day = 31
            year -= 1
        rate = get_mpi_rate('REPO', date(year, month, day))
        if rate[1]:
            return None, rate[1]
        debt.rates[date(year, month, day)] = rate[0]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') \
            * (rate[0] + 7) / 100, None

    if interest.model == 'cust5':
        year = default_date.year
        month = default_date.month
        day = default_date.day
        if month > 6:
            month = 6
            day = 30
        else:
            month = 12
            day = 31
            year -= 1
        rate = get_mpi_rate('REPO', date(year, month, day))
        if rate[1]:
            return None, rate[1]
        debt.rates[date(year, month, day)] = rate[0]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') \
            * (rate[0] + 8) / 100, None

    if interest.model == 'cust6':
        year = default_date.year
        month = default_date.month
        if month > 6:
            month = 7
        else:
            month = 1
        rate = get_mpi_rate('REPO', date(year, month, 1))
        if rate[1]:
            return None, rate[1]
        debt.rates[date(year, month, 1)] = rate[0]
        return principal * yfactor(pastdate, presdate, 'ACT/ACT') \
            * (rate[0] + 8) / 100, None

    if interest.model == 'cust4':
        return principal * (presdate - pastdate).days / 400, None

    return None, 'Neznámý model'


def getrows(debt):

    if not debt.transactions:
        return []

    if debt.interest.model == 'cust4':
        return getrows4(debt)

    trs = debt.transactions[:]
    idx = 1
    for trn in trs:
        trn.id = idx
        idx += 1
    trs.sort(key=lambda x: x.transaction_type, reverse=True)
    trs.sort(key=lambda x: x.date)

    rows = []
    principal = interest = 0
    cud = None
    err = False
    for trn in trs:
        if trn.transaction_type == 'debit':
            default_date = trn.date + ODP
            break
    else:
        default_date = None
    debt.default_date = default_date

    for trn in trs:
        row = {}
        amt = round(trn.amount, debt.rounding) if hasattr(trn, 'amount') else 0
        row['id'] = trn.id
        row['date'] = trn.date
        row['description'] = trn.description
        row['trt'] = trt = trn.transaction_type
        if trt == 'credit':
            row['rep'] = 'jistina' if trn.repayment_preference == 'principal' \
                else 'úrok'
        if trt == 'debit':
            row['change'] = amt
        elif trt == 'credit':
            row['change'] = -amt
        else:
            row['change'] = 0
        if not err:
            oldp = principal
            oldi = interest
            if (cud and debt.interest.model != 'none' and principal > 0) \
                or debt.interest.model == 'fixed':
                itr = calcint(cud, trn.date, principal, debt, default_date)
                if itr[1]:
                    err = True
                    row['msg'] = itr[1]
                else:
                    interest += round(itr[0], debt.rounding)
            if trt != 'balance':
                row['pre_principal'] = principal
                row['pre_interest'] = interest
                row['pre_total'] = principal + interest
            else:
                for key in ('pre_principal', 'pre_interest', 'pre_total'):
                    row[key] = 0
            if trt == 'debit':
                chp = -amt
                chi = 0
            elif trt == 'credit':
                if trn.repayment_preference == 'principal':
                    chp = principal if amt > principal else amt
                    amt -= chp
                    chi = interest if amt > interest else amt
                    amt -= chi
                    if amt:
                        principal -= amt
                else:
                    chi = interest if amt > interest else amt
                    amt -= chi
                    chp = amt
            else:
                chp = chi = 0
            principal -= chp
            interest -= chi
            row['change_principal'] = -chp
            row['change_interest'] = -chi
            row['post_principal'] = principal
            row['post_interest'] = interest
            row['post_total'] = principal + interest
            if trt == 'balance':
                principal = oldp
                interest = oldi
            else:
                cud = trn.date

        row['err'] = err
        rows.append(row)

    return rows


def getrows4(debt):

    if not debt.transactions:
        return []

    minm = 25 if debt.currency == 'CZK' else 0

    trs = debt.transactions[:]
    idx = 1
    for trn in trs:
        trn.id = idx
        idx += 1
    trs.sort(key=lambda x: x.transaction_type, reverse=True)
    trs.sort(key=lambda x: x.date)

    for trn in trs:
        if trn.transaction_type == 'debit':
            default_date = trn.date + ODP
            break
    else:
        default_date = None
    debt.default_date = default_date

    rows = []
    err = ''
    principal = interest = 0
    currd = default_date
    normi = lasti = 0
    dat = trs[0].date
    idx = 0
    while dat <= trs[-1].date:
        if dat == currd:
            lasti = 0
            normi = minm
        inci = principal / 400
        if inci < 0:
            inci = 0
        lasti += inci
        if lasti > normi:
            diffi = lasti - normi
            normi = lasti
        else:
            diffi = 0
        if dat == currd:
            diffi += minm
            dday = default_date.day
            month = dat.month + 1
            year = dat.year
            if month > 12:
                month = 1
                year += 1
            dday = min(dday, monthrange(year, month)[1])
            currd = date(year, month, dday)

        interest += diffi
        while idx < len(trs) and trs[idx].date == dat:
            trn = trs[idx]
            row = {}
            row['id'] = trn.id
            row['date'] = dat
            row['description'] = trn.description
            amt = round(trs[idx].amount, debt.rounding) \
                if hasattr(trs[idx], 'amount') else 0
            row['change'] = amt if trs[idx].transaction_type == 'debit' \
                else -amt
            row['trt'] = trn.transaction_type
            if trn.transaction_type != 'balance':
                row['pre_principal'] = principal
                row['pre_interest'] = interest
                row['pre_total'] = principal + interest
            if trs[idx].transaction_type == 'debit':
                principal += amt
                chp = -amt
                chi = 0
            elif trs[idx].transaction_type == 'credit':
                if trs[idx].repayment_preference == 'principal':
                    chp = principal if amt > principal else amt
                    amt -= chp
                    chi = interest if amt > interest else amt
                    amt -= chi
                    if amt:
                        principal -= amt
                else:
                    chi = interest if amt > interest else amt
                    amt -= chi
                    chp = amt
                principal -= chp
                interest -= chi
            else:
                chp = chi = .0

            if trn.transaction_type == 'credit':
                row['rep'] = 'jistina' \
                    if trn.repayment_preference == 'principal' else 'úrok'
            if trn.transaction_type != 'balance':
                row['change_principal'] = -chp
                row['change_interest'] = -chi
            else:
                for key in ('pre_principal', 'pre_interest', 'pre_total',
                    'change_principal', 'change_interest'):
                    row[key] = 0
            row['post_principal'] = principal
            row['post_interest'] = interest
            row['post_total'] = principal + interest
            row['err'] = err
            rows.append(row)
            idx += 1

        dat += ODP

    return rows


def to_xml(debt):

    dec = {
        'debt': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'
            .format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        },
        'currency': {'standard': 'ISO 4217'},
        'pa_rate': {'unit': 'percent per annum'},
        'pm_rate': {'unit': 'percent per month'},
        'pd_rate': {'unit': 'per mil per day'}
    }
    xml = new_xml('')
    tdebt = xml_decorate(xml.new_tag('debt'), dec)
    xml.append(tdebt)
    for key in ('title', 'note', 'internal_note'):
        tag = xml.new_tag(key)
        tag.append(xml_espace(debt.__getattribute__(key)))
        tdebt.append(tag)
    tag = xml_decorate(xml.new_tag('currency'), dec)
    tag.append(debt.currency)
    tdebt.append(tag)
    tag = xml.new_tag('rounding')
    tag.append(str(debt.rounding))
    tdebt.append(tag)
    titr = xml.new_tag('interest')
    interest = debt.interest
    model = interest.model
    titr['model'] = model
    if model == 'fixed':
        tag = xml.new_tag('amount')
        tag.append('{:.2f}'.format(interest.fixed_amount))
        titr.append(tag)
    elif model == 'per_annum':
        tag = xml_decorate(xml.new_tag('pa_rate'), dec)
        tag.append('{:.6f}'.format(interest.rate))
        titr.append(tag)
    elif model == 'per_mensem':
        tag = xml_decorate(xml.new_tag('pm_rate'), dec)
        tag.append('{:.6f}'.format(interest.rate))
        titr.append(tag)
    elif model == 'per_diem':
        tag = xml_decorate(xml.new_tag('pd_rate'), dec)
        tag.append('{:.6f}'.format(interest.rate))
        titr.append(tag)
    if model in ('per_annum', 'per_mensem'):
        tag = xml.new_tag('day_count_convention')
        tag.append(interest.day_count_convention)
        titr.append(tag)
    tdebt.append(titr)
    trs = xml.new_tag('transactions')
    for trn in debt.transactions:
        ttrn = xml.new_tag(trn.transaction_type)
        tag = xml.new_tag('description')
        tag.append(xml_espace(trn.description))
        ttrn.append(tag)
        tag = xml.new_tag('date')
        tag.append(trn.date.isoformat())
        ttrn.append(tag)
        if hasattr(trn, 'amount'):
            tag = xml.new_tag('amount')
            tag.append('{:.2f}'.format(trn.amount))
            ttrn.append(tag)
        if hasattr(trn, 'repayment_preference'):
            tag = xml.new_tag('repayment_preference')
            tag.append(trn.repayment_preference)
            ttrn.append(tag)
        trs.append(ttrn)
    tdebt.append(trs)
    return str(xml).encode('utf-8') + b'\n'


def from_xml(dat):

    string = get_xml(dat)
    if not string:
        return None, 'Chybný formát souboru'
    tdebt = string.debt
    assert tdebt and tdebt['application'] == APP
    debt = Debt()
    debt.title = xml_unespace(tdebt.title.text.strip())
    debt.note = xml_unespace(tdebt.note.text.strip())
    debt.internal_note = xml_unespace(tdebt.internal_note.text.strip())
    debt.rounding = int(tdebt.rounding.text.strip())
    debt.currency = tdebt.currency.text.strip()
    interest = Interest()
    debt.interest = interest
    titr = tdebt.interest
    interest.model = model = titr['model']
    if model == 'fixed':
        interest.fixed_amount = float(titr.amount.text.strip())
    elif model == 'per_annum':
        interest.rate = float(titr.pa_rate.text.strip())
        interest.day_count_convention = titr.day_count_convention.text.strip()
    elif model == 'per_mensem':
        interest.rate = float(titr.pm_rate.text.strip())
        interest.day_count_convention = titr.day_count_convention.text.strip()
    elif model == 'per_diem':
        interest.rate = float(titr.pd_rate.text.strip())
    for trn in tdebt.transactions.children:
        if not trn.name:
            continue
        transaction = Transaction()
        debt.transactions.append(transaction)
        transaction.description = xml_unespace(trn.description.text.strip())
        transaction.transaction_type = str(trn.name)
        transaction.date = iso2date(trn.date)
        if transaction.transaction_type != 'balance':
            transaction.amount = float(trn.amount.text.strip())
        if transaction.transaction_type == 'credit':
            transaction.repayment_preference = \
                trn.repayment_preference.text.strip()
    return debt, None


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    def cellam(amt, slb=False):
        amt = (float(amt) if debt.rounding else int(round(amt)))
        suf = 's' if slb else ''
        if abs(amt) < LIM:
            return '<td class="cr{}"></td>'.format(suf)
        if amt > 0:
            return '<td class="cr{}">{}</td>'.format(suf, famt(amt))
        return '<td class="dr{}">{}</td>'.format(suf, famt(-amt))

    def lfamt(amt):
        return '{}&nbsp;{}'.format(
            famt(round(amt, debt.rounding) if debt.rounding
            else int(round(amt))).replace('-', '−'), dispcurr(debt.currency))

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
        interest = debt.interest
        var['model'] = model = interest.model
        if model == 'fixed':
            var['fixed_amount'] = '{:.2f}'.format(LocalFloat(
                interest.fixed_amount)) if debt.rounding \
                else int(round(interest.fixed_amount))
        elif model == 'per_annum':
            var['pa_rate'] = interest.rate
            var['ydconv'] = interest.day_count_convention
        elif model == 'per_mensem':
            var['pm_rate'] = interest.rate
            var['mdconv'] = interest.day_count_convention
        elif model == 'per_diem':
            var['pd_rate'] = interest.rate

        form = MainForm(initial=var)

    else:
        button = getbutton(request)

        if button == 'empty':
            debt = Debt()
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:mainpage')

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

        form = MainForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            debt.title = cld['title'].strip()
            debt.note = cld['note'].strip()
            debt.internal_note = cld['internal_note'].strip()
            debt.currency = cld['currency']
            debt.rounding = int(cld['rounding'])
            interest = Interest()
            debt.interest = interest
            interest.model = model = cld['model']
            if model == 'fixed':
                interest.fixed_amount = float(cld['fixed_amount'])
            elif model == 'per_annum':
                interest.rate = float(cld['pa_rate'])
                interest.day_count_convention = cld['ydconv']
            elif model == 'per_mensem':
                interest.rate = float(cld['pm_rate'])
                interest.day_count_convention = cld['mdconv']
            elif model == 'per_diem':
                interest.rate = float(cld['pd_rate'])
            setdebt(request, debt)

            if not button and cld['next']:
                return redirect(cld['next'])

            if button == 'xml':
                response = HttpResponse(
                    to_xml(debt),
                    content_type='text/xml; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.xml'
                return response

            if button == 'csv' and not rows_err:
                response = \
                    HttpResponse(content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.csv'
                writer = csv.writer(response)
                writer.writerow(
                    ('Datum',
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
                     'Nový zůstatek/celkem'))
                for row in rows:
                    writer.writerow(
                        (row['date'].isoformat(),
                         row['description'],
                         row.get('rep', ''),
                         '{:.2f}'.format(normfl(row['change'])),
                         '{:.2f}'.format(normfl(row['pre_principal'])),
                         '{:.2f}'.format(normfl(row['pre_interest'])),
                         '{:.2f}'.format(normfl(row['pre_total'])),
                         '{:.2f}'.format(normfl(row['change_principal'])),
                         '{:.2f}'.format(normfl(row['change_interest'])),
                         '{:.2f}'.format(normfl(row['post_principal'])),
                         '{:.2f}'.format(normfl(row['post_interest'])),
                         '{:.2f}'.format(normfl(row['post_total']))))
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

                style16 = ParagraphStyle(
                    name='STYLE16',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                style17 = ParagraphStyle(
                    name='STYLE17',
                    fontName='BookmanB',
                    fontSize=8,
                    leading=10,
                    alignment=TA_RIGHT,
                    allowWidows=False,
                    allowOrphans=False)

                style18 = ParagraphStyle(
                    name='STYLE18',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    allowWidows=False,
                    allowOrphans=False)

                style19 = ParagraphStyle(
                    name='STYLE19',
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
                    leftIndent=8,
                    allowWidows=False,
                    allowOrphans=False)

                style21 = ParagraphStyle(
                    name='STYLE21',
                    fontName='Bookman',
                    fontSize=8,
                    leading=10,
                    leftIndent=16,
                    allowWidows=False,
                    allowOrphans=False)

                style22 = ParagraphStyle(
                    name='STYLE22',
                    fontName='BookmanI',
                    fontSize=8,
                    leading=10,
                    alignment=TA_CENTER,
                    allowWidows=False,
                    allowOrphans=False)

                doc1 = (([Paragraph('Historie peněžité pohledávky'.upper(),
                    style1)],),)
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

                wid = 483.3
                widl = 8
                widr = 8
                widg = 12
                widf = widc = (wid - widl - widr - (widg * 2)) / 6
                cwid = (widl,) + ((widc / 5,) * 5) + ((widf / 5,) * 5) \
                    + (widg,) + ((widc / 5,) * 5) + ((widf / 5,) * 5) \
                    + (widg,) + ((widc / 5,) * 5) + ((widf / 5,) * 5) + (widr,)

                thickness = .5

                res = [Paragraph(('<b>Měna:</b> {}'.format(debt.currency)),
                    style19)]
                if hasattr(debt, 'default_date') and debt.default_date:
                    res.append(Paragraph(
                        '<b>První den prodlení:</b> {:%d.%m.%Y}'
                        .format(debt.default_date),
                        style19))
                interest2 = None
                interest3 = []
                if debt.interest.model == 'none':
                    interest1 = 'bez úroku'
                elif debt.interest.model == 'fixed':
                    interest1 = \
                        'pevnou částkou {}' \
                        .format(lfamt(debt.interest.fixed_amount))
                elif debt.interest.model == 'per_annum':
                    interest1 = \
                        'pevnou sazbou {0.rate:n} % <i>p. a.</i>, ' \
                        'konvence pro počítání dnů: {0.day_count_convention}' \
                        .format(debt.interest)
                elif debt.interest.model == 'per_mensem':
                    interest1 = \
                        'pevnou sazbou {0.rate:n} % <i>p. m.</i>, ' \
                        'konvence pro počítání dnů: {0.day_count_convention}' \
                        .format(debt.interest)
                elif debt.interest.model == 'per_diem':
                    interest1 = \
                        'pevnou sazbou {:n} ‰ <i>p. d.</i>' \
                        .format(debt.interest.rate)
                elif debt.interest.model == 'cust1':
                    interest1 = \
                        'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                        '(účinnost do 27.04.2005)'
                    if debt.rates:
                        rate = debt.rates.popitem()
                        interest2 = \
                            'Diskontní sazba ČNB ke dni {:%d.%m.%Y}: {:.2f}' \
                            ' % <i>p. a.</i>' \
                            .format(rate[0], LocalFloat(rate[1]))
                elif debt.interest.model == 'cust2':
                    interest1 = \
                        'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                        '(účinnost od 28.04.2005 do 30.06.2010)'
                    if len(debt.rates) == 1:
                        rate = debt.rates.popitem()
                        interest2 = \
                            'Použita 2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                            ' {:.2f} % <i>p. a.</i>' \
                            .format(rate[0], LocalFloat(rate[1]))
                    elif len(debt.rates) > 1:
                        interest2 = 'Použity následující 2T repo sazby ČNB:'
                        for dat in sorted(debt.rates.keys()):
                            interest3.append(
                                '– ke dni {:%d.%m.%Y}: {:.2f} % <i>p. a.</i>' \
                                .format(dat, LocalFloat(debt.rates[dat])))
                elif debt.interest.model == 'cust3':
                    interest1 = \
                        'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                        '(účinnost od 01.07.2010 do 30.06.2013)'
                    if debt.rates:
                        rate = debt.rates.popitem()
                        interest2 = \
                            '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                            ' {:.2f} % <i>p. a.</i>' \
                            .format(rate[0], LocalFloat(rate[1]))
                elif debt.interest.model == 'cust5':
                    interest1 = \
                        'úrok z prodlení podle nařízení č. 142/1994 Sb. ' \
                        '(účinnost od 01.07.2013 do 31.12.2013)'
                    if debt.rates:
                        rate = debt.rates.popitem()
                        interest2 = \
                            '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                            ' {:.2f} % <i>p. a.</i>' \
                            .format(rate[0], LocalFloat(rate[1]))
                elif debt.interest.model == 'cust6':
                    interest1 = 'úrok z prodlení podle nařízení č. 351/2013 Sb.'
                    if debt.rates:
                        rate = debt.rates.popitem()
                        interest2 = \
                            '2T repo sazba ČNB ke dni {:%d.%m.%Y}:' \
                            ' {:.2f} % <i>p. a.</i>' \
                            .format(rate[0], LocalFloat(rate[1]))
                else:
                    interest1 = \
                        'poplatek z prodlení podle nařízení č. 142/1994 Sb.'
                    if debt.currency != 'CZK':
                        interest2 = \
                            '<i>(minimální sazba 25 Kč za každý ' \
                            'započatý měsíc prodlení není pro jinou ' \
                            'měnu než CZK podporována)</i>'

                res.append(
                    Paragraph('<b>Úročení:</b> {}'.format(interest1), style19))
                if interest2:
                    res.append(Paragraph(interest2, style20))
                for key in interest3:
                    res.append(Paragraph(key, style21))
                res.append(Spacer(0, 50))
                flow.extend(res)

                bst = (
                    ('SPAN', (0, 0), (4, 0)),
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
                    ('BOTTOMPADDING', (0, 0), (-1, 0), .5),
                    ('BOTTOMPADDING', (0, 1), (-1, 1), 1.5),
                    ('BOTTOMPADDING', (0, 2), (-1, 4), 0),
                    ('BOTTOMPADDING', (0, -1), (-1, -1), 18),
                )

                ast = {
                    'debit': (
                        ('LINEBELOW', (1, 1), (10, 1), thickness, black),
                        ('LINEAFTER', (3, 2), (3, 2), thickness, black),
                        ('LINEBELOW', (12, 1), (21, 1), thickness, black),
                        ('LINEAFTER', (14, 2), (14, 4), thickness, black),
                        ('LINEBELOW', (23, 1), (32, 1), thickness, black),
                        ('LINEAFTER', (25, 2), (25, 4), thickness, black)),
                    'credit': (
                        ('LINEBELOW', (1, 1), (10, 1), thickness, black),
                        ('LINEAFTER', (3, 2), (3, 4), thickness, black),
                        ('LINEBELOW', (12, 1), (21, 1), thickness, black),
                        ('LINEAFTER', (14, 2), (14, 4), thickness, black),
                        ('LINEBELOW', (23, 1), (32, 1), thickness, black),
                        ('LINEAFTER', (25, 2), (25, 4), thickness, black)),
                    'balance': (
                        ('LINEBELOW', (23, 1), (32, 1), thickness, black),
                        ('LINEAFTER', (25, 2), (25, 4), thickness, black))
                }

                for row in rows:
                    if row['err']:
                        flow.extend(
                            [Spacer(0, 20),
                             Paragraph(
                                 '(pro další transakce nejsou k disposici'
                                 ' data, při výpočtu došlo k chybě)', style22)])
                        break
                    trt = row['trt']
                    doc3 = []
                    temp1 = \
                        [Paragraph(
                            '{:%d.%m.%Y}'.format(row['date']),
                            style13)] \
                        + ([''] * 4)
                    temp2 = \
                        [Paragraph(
                            escape(row['description']).upper(),
                            style14)] \
                        + ([''] * 28)
                    doc3.extend([temp1 + temp2])

                    if trt == 'debit':
                        temp = \
                            ['', Paragraph('Závazek', style15)] \
                            + ([''] * 10) \
                            + [Paragraph('Předchozí zůstatek', style15)] \
                            + ([''] * 10) \
                            + [Paragraph('Nový zůstatek', style15), '']
                    elif trt == 'credit':
                        temp = \
                            ['', Paragraph('<b>Splátka</b> (přednost {}'
                            .format(row['rep']), style16)] \
                            + ([''] * 10) \
                            + [Paragraph('Předchozí zůstatek', style15)] \
                            + ([''] * 10) \
                            + [Paragraph('Nový zůstatek', style15), '']
                    else:
                        temp = \
                            ([''] * 23) \
                            + [Paragraph('Zůstatek', style15), '']
                    doc3.extend([temp])

                    if trt != 'balance':
                        temp = \
                            ['', Paragraph('Částka', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt((row['change'] if (trt == 'debit')
                                else (-row['change']))),
                                style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Jistina', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['pre_principal']),
                                style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Jistina', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['post_principal']),
                                style18)] \
                            + ([''] * 7)
                    else:
                        temp = \
                            ([''] * 23) \
                            + [Paragraph('Jistina', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['post_principal']),
                                style18)] \
                            + ([''] * 7)
                    doc3.extend([temp])

                    if trt == 'debit':
                        temp = \
                            ([''] * 12) \
                            + [Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['pre_interest']), style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['post_interest']),
                                style18)] \
                            + ([''] * 7)
                    elif trt == 'credit':
                        temp = \
                            ['', Paragraph('Jistina', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(-row['change_principal']),
                                style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['pre_interest']), style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['post_interest']),
                                style18)] \
                            + ([''] * 7)
                    else:
                        temp = \
                            ([''] * 23) \
                            + [Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(row['post_interest']),
                                style18)] \
                            + ([''] * 7)
                    doc3.extend([temp])

                    if trt == 'debit':
                        temp = \
                            ([''] * 12) \
                            + [Paragraph('Celkem', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['pre_total']), style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['post_total']), style18)] \
                            + ([''] * 7)
                    elif trt == 'credit':
                        temp = \
                            ['', Paragraph('Úrok', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(
                                lfamt(-row['change_interest']),
                                style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['pre_total']), style18)] \
                            + ([''] * 7) \
                            + [Paragraph('Celkem', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['post_total']), style18)] \
                            + ([''] * 7)
                    else:
                        temp = \
                            ([''] * 23) \
                            + [Paragraph('Celkem', style17)] \
                            + ([''] * 2) \
                            + [Paragraph(lfamt(row['post_total']), style18)] \
                            + ([''] * 7)
                    doc3.extend([temp])

                    temp = [''] * 34
                    doc3.extend([temp])

                    table3 = Table(doc3, colWidths=cwid)
                    table3.setStyle(TableStyle(bst + ast[trt]))
                    flow.append(KeepTogether(table3))

                if debt.note:
                    flow.append(Spacer(0, 24))
                    temp = [Paragraph('Poznámka:'.upper(), style4)]
                    for line in filter(bool, debt.note.strip().split('\n')):
                        temp.append(Paragraph(escape(line), style12))
                    flow.append(KeepTogether(temp[:2]))
                    if len(temp) > 2:
                        flow.extend(temp[2:])
                temp = BytesIO()
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = \
                    'attachment; filename=Pohledavka.pdf'
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

        else:
            logger.debug('Invalid form', request)
            err_message = INERR

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
         'form': form,
         'rows': rows,
         'currency': dispcurr(debt.currency),
         'YDCONVS': YDCONVS,
         'MDCONVS': MDCONVS,
         'err_message': err_message,
         'rows_err': rows_err})


@require_http_methods(('GET', 'POST'))
@login_required
def transform(request, idx=0):

    logger.debug(
        'Transaction form accessed using method {}, id={}'
        .format(request.method, idx),
        request,
        request.POST)
    page_title = 'Úprava transakce' if idx else 'Nová transakce'
    err_message = ''
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    idx = int(idx)
    if request.method == 'GET':
        if idx:
            if idx > len(debt.transactions):
                raise Http404
            transaction = debt.transactions[idx - 1]
            var = {
                'description': transaction.description,
                'transaction_type': transaction.transaction_type,
                'date': transaction.date}
            if hasattr(transaction, 'amount'):
                var['amount'] = \
                    '{:.2f}'.format(LocalFloat(transaction.amount)) \
                    if debt.rounding else int(round(transaction.amount))
            if hasattr(transaction, 'repayment_preference'):
                var['repayment_preference'] = transaction.repayment_preference
            form = TransForm(initial=var)
        else:
            form = TransForm()
    else:
        form = TransForm(request.POST)

        button = getbutton(request)
        if button == 'back':
            return redirect('hjp:mainpage')
        if button == 'set_date':
            form.data = form.data.copy()
            form.data['date'] = date.today()
        elif form.is_valid():
            cld = form.cleaned_data
            transaction = Transaction()
            transaction.description = cld['description'].strip()
            transaction.transaction_type = cld['transaction_type']
            transaction.date = cld['date']
            if transaction.transaction_type != 'balance':
                transaction.amount = float(cld['amount'])
            if transaction.transaction_type == 'credit':
                transaction.repayment_preference = cld['repayment_preference']
            if idx:
                if idx > len(debt.transactions):
                    raise Http404
                debt.transactions[idx - 1] = transaction
            else:
                debt.transactions.append(transaction)
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:mainpage')

        else:
            logger.debug('Invalid form', request)
            err_message = INERR

    return render(
        request,
        'hjp_transform.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'currency': dispcurr(debt.currency),
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def transdel(request, idx=0):

    logger.debug(
        'Transaction delete page accessed using method {}, id={}'
        .format(request.method, idx),
        request,
        request.POST)
    idx = int(idx) - 1
    debt = getdebt(request)
    if not debt:  # pragma: no cover
        return error(request)
    if idx >= len(debt.transactions):
        raise Http404
    if request.method == 'GET':
        return render(
            request,
            'hjp_transdel.html',
            {'app': APP,
             'page_title': 'Smazání transakce',
             'date': debt.transactions[idx].date})
    else:
        button = getbutton(request)
        if button == 'yes':
            del debt.transactions[idx]
            if not setdebt(request, debt):  # pragma: no cover
                return error(request)
            return redirect('hjp:transdeleted')
        return redirect('hjp:mainpage')
