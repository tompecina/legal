# -*- coding: utf-8 -*-
#
# cnb/utils.py
#
# Copyright (C) 2011-19 Tomáš Pecina <tomas@pecina.cz>
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

from legal.common.utils import new_xml, LOGGER, getcache
from legal.cnb.models import FXrate, MPIrate, MPIstat


DOWNLOAD_WAIT = timedelta(days=10)
DOWNLOAD_REPEAT = timedelta(hours=1)


def get_fx_rate(curr, dat, log=None, use_fixed=False, log_fixed=None):

    LOGGER.debug(
        'FX rate requested, currency "{0}" for {1.year:d}-{1.month:02d}-{1.day:02d}, fixed "{2}"'
        .format(curr, dat, use_fixed))

    fixed_list = {
        'XEU': {'currency_to': 'EUR',
                'fixed_rate': 1,
                'date_from': date(1999, 1, 1)},
        'ATS': {'currency_to': 'EUR',
                'fixed_rate': 13.7603,
                'date_from': date(1998, 12, 31)},
        'BEF': {'currency_to': 'EUR',
                'fixed_rate': 40.3399,
                'date_from': date(1998, 12, 31)},
        'NLG': {'currency_to': 'EUR',
                'fixed_rate': 2.20371,
                'date_from': date(1998, 12, 31)},
        'FIM': {'currency_to': 'EUR',
                'fixed_rate': 5.94573,
                'date_from': date(1998, 12, 31)},
        'FRF': {'currency_to': 'EUR',
                'fixed_rate': 6.55957,
                'date_from': date(1998, 12, 31)},
        'DEM': {'currency_to': 'EUR',
                'fixed_rate': 1.95583,
                'date_from': date(1998, 12, 31)},
        'IEP': {'currency_to': 'EUR',
                'fixed_rate': .787564,
                'date_from': date(1998, 12, 31)},
        'ITL': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)},
        'LUF': {'currency_to': 'EUR',
                'fixed_rate': 40.3399,
                'date_from': date(1998, 12, 31)},
        'MCF': {'currency_to': 'EUR',
                'fixed_rate': 6.55957,
                'date_from': date(1998, 12, 31)},
        'PTE': {'currency_to': 'EUR',
                'fixed_rate': 200.482,
                'date_from': date(1998, 12, 31)},
        'SML': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)},
        'ESP': {'currency_to': 'EUR',
                'fixed_rate': 166.386,
                'date_from': date(1998, 12, 31)},
        'VAL': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)},
        'GRD': {'currency_to': 'EUR',
                'fixed_rate': 340.75,
                'date_from': date(2000, 6, 19)},
        'SIT': {'currency_to': 'EUR',
                'fixed_rate': 239.64,
                'date_from': date(2006, 7, 11)},
        'CYP': {'currency_to': 'EUR',
                'fixed_rate': .585274,
                'date_from': date(2007, 7, 10)},
        'MTL': {'currency_to': 'EUR',
                'fixed_rate': .4293,
                'date_from': date(2007, 7, 10)},
        'SKK': {'currency_to': 'EUR',
                'fixed_rate': 30.126,
                'date_from': date(2008, 7, 8)},
        'EEK': {'currency_to': 'EUR',
                'fixed_rate': 15.6466,
                'date_from': date(2010, 7, 13)},
        'ROL': {'currency_to': 'RON',
                'fixed_rate': 10000,
                'date_from': date(2005, 7, 1)},
        'RUR': {'currency_to': 'RUB',
                'fixed_rate': 1000,
                'date_from': date(1998, 1, 1)},
        'MXP': {'currency_to': 'MXN',
                'fixed_rate': 1000,
                'date_from': date(1993, 1, 1)},
        'UAK': {'currency_to': 'UAH',
                'fixed_rate': 100000,
                'date_from': date(1996, 9, 2)},
        'TRL': {'currency_to': 'TRY',
                'fixed_rate': 1000000,
                'date_from': date(2005, 1, 1)},
        'BGL': {'currency_to': 'BGN',
                'fixed_rate': 1000,
                'date_from': date(1999, 7, 5)},
        'PLZ': {'currency_to': 'PLN',
                'fixed_rate': 10000,
                'date_from': date(1995, 1, 1)},
        'CSD': {'currency_to': 'RSD',
                'fixed_rate': 1,
                'date_from': date(2003, 1, 1)},
        }

    today = date.today()
    if dat.year < 1991 or dat > today:
        return None, None, None, 'Chybné datum, data nejsou k disposici'
    rat = FXrate.objects.filter(date=dat)
    if rat:
        txt = rat[0].text
    else:
        surl = (
            'https://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.xml?'
            'date={0.day:d}.{0.month:d}.{0.year:d}'.format(dat))
        txt = getcache(surl, DOWNLOAD_REPEAT)[0]
        if not txt:
            LOGGER.warning('No connection to CNB server')
            return None, None, None, 'Chyba spojení se serverem ČNB'
    try:
        soup = new_xml(txt)
        assert soup
        assert soup.find(
            'tabulka',
            {'typ': 'XML_TYP_CNB_KURZY_DEVIZOVEHO_TRHU'})
        dreq = soup.find('kurzy', {'banka': 'CNB'})['datum']
        dreq = date(int(dreq[6:]), int(dreq[3:5]), int(dreq[:2]))
    except:
        LOGGER.error('Invalid FX table structure for {0.year:d}-{0.month:02d}-{0.day:02d}'.format(dat))
        return None, None, None, 'Chyba struktury kursové tabulky'
    if not rat and (dreq == dat or (today - dat) > DOWNLOAD_WAIT):
        FXrate(date=dat, text=txt).save()
    lin = soup.find('radek', {'kod': curr})
    frat = 1
    curr_rq = curr
    if not lin:
        if use_fixed and curr in fixed_list and fixed_list[curr]['date_from'] <= dat:
            curr = fixed_list[curr]['currency_to']
            lin = soup.find('radek', {'kod': curr})
            if not lin:
                return None, None, dreq, 'Kurs není v kursové tabulce'
            frat = fixed_list[curr_rq]['fixed_rate']
            if log_fixed != None:
                log_fixed.append(
                    {'currency_from': curr_rq,
                     'currency_to': fixed_list[curr_rq]['currency_to'],
                     'rate': fixed_list[curr_rq]['fixed_rate'],
                     'date_from': fixed_list[curr_rq]['date_from']})
        else:
            return None, None, dreq, 'Kurs není v kursové tabulce'
    try:
        qty = int(lin['mnozstvi'])
        if lin.has_attr('kurz'):
            rate = lin['kurz']
        elif lin.has_attr('pomer'):
            rate = lin['pomer']
        rate = float(rate.replace(',', '.'))
    except:
        LOGGER.error('Invalid FX table line for {0.year:d}-{0.month:02d}-{0.day:02d}'.format(dat))
        return None, None, dreq, 'Chyba řádku kursové tabulky'
    if log != None:
        log.append(
            {'currency': curr,
             'quantity': qty,
             'rate': rate,
             'date_required': dat,
             'date': dreq})
    return rate / frat, qty, dreq, None


def get_mpi_rate(typ, dat, log=None):

    LOGGER.debug('MPI rate of type "{0}" requested for {1.year:d}-{1.month:02d}-{1.day:02d}'.format(typ, dat))

    now = datetime.now()

    prefix = 'https://www.cnb.cz/cs/faq/vyvoj_'
    suffix = '_historie.txt'
    types = {
        'DISC': ('diskontni', 'PLATNA_OD|CNB_DISKONTNI_SAZBA_V_%'),
        'LOMB': ('lombard', 'PLATNA_OD|CNB_LOMBARDNI_SAZBA_V_%'),
        'REPO': ('repo', 'PLATNA_OD|CNB_REPO_SAZBA_V_%'),
    }

    if typ not in types.keys():
        return None, 'Chybný druh sazby'

    if dat.year < 1990 or dat > now.date():
        return None, 'Chybné datum, data nejsou k disposici'

    stat = MPIstat.objects.get_or_create(type=typ)
    updated = stat[0].timestamp_update.date()
    if stat[1] or (not MPIrate.objects.filter(type=typ, valid__gte=dat).exists()
        and (updated - dat) < DOWNLOAD_WAIT):
        surl = prefix + types[typ][0] + suffix
        txt = getcache(surl, DOWNLOAD_REPEAT)[0]
        if not txt:
            LOGGER.warning('No connection to CNB server')
            return None, 'Chyba spojení se serverem ČNB'

        txt = txt.replace('\r', '').split('\n')
        if txt[0] != types[typ][1]:
            LOGGER.error('Error in rate table for {}'.format(types[typ][0]))
            return None, 'Chyba tabulky sazeb (1)'

        rates = []
        try:
            for lin in txt[1:]:
                assert lin[8] == '|'
                rates.append(
                    (float(lin[9:].replace(',', '.')),
                     date(int(lin[:4]), int(lin[4:6]), int(lin[6:8]))))
        except:
            LOGGER.error('Error in rate table for {}'.format(types[typ][0]))
            return None, 'Chyba tabulky sazeb (2)'

        try:
            for rat in rates:
                if stat[1] or (updated - rat[1]) < DOWNLOAD_WAIT:
                    MPIrate.objects.get_or_create(
                        type=typ,
                        rate=rat[0],
                        valid=rat[1])
        except:  # pragma: no cover
            LOGGER.error('Error writing in database')
            return None, 'Chyba zápisu do database (1)'
        try:
            MPIstat.objects.get_or_create(type=typ)[0].save()
        except:  # pragma: no cover
            LOGGER.error('Error writing in database')
            return None, 'Chyba zápisu do database (2)'

    res = MPIrate.objects.filter(type=typ, valid__lte=dat).order_by('-valid')
    if not res.exists():
        return None, 'Sazba není k disposici'

    if log != None:
        log.append({'type': typ, 'rate': res[0].rate, 'date': dat})
    return res[0].rate, None
