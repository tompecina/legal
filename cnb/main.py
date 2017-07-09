# -*- coding: utf-8 -*-
#
# cnb/main.py
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
from cache.main import getcache
from common.utils import newXML, logger
from .models import FXrate, MPIrate, MPIstat

sd = timedelta(days=10)
cd = timedelta(hours=1)

def getFXrate(curr, dt, log=None, use_fixed=False, log_fixed=None):

    logger.debug(
        'FX rate requested, currency "{}" for {:d}-{:02d}-{:02d}, fixed "{}"' \
            .format(curr, dt.year, dt.month, dt.day, use_fixed))
    
    fixed_list = {
        'XEU': {'currency_to': 'EUR',
                'fixed_rate': 1.0,
                'date_from': date(1999,  1,  1)
        },
        'ATS': {'currency_to': 'EUR',
                'fixed_rate': 13.7603,
                'date_from': date(1998, 12, 31)
        },
        'BEF': {'currency_to': 'EUR',
                'fixed_rate': 40.3399,
                'date_from': date(1998, 12, 31)
        },
        'NLG': {'currency_to': 'EUR',
                'fixed_rate': 2.20371,
                'date_from': date(1998, 12, 31)
        },
        'FIM': {'currency_to': 'EUR',
                'fixed_rate': 5.94573,
                'date_from': date(1998, 12, 31)
        },
        'FRF': {'currency_to': 'EUR',
                'fixed_rate': 6.55957,
                'date_from': date(1998, 12, 31)
        },
        'DEM': {'currency_to': 'EUR',
                'fixed_rate': 1.95583,
                'date_from': date(1998, 12, 31)
        },
        'IEP': {'currency_to': 'EUR',
                'fixed_rate': 0.787564,
                'date_from': date(1998, 12, 31)
        },
        'ITL': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)
        },
        'LUF': {'currency_to': 'EUR',
                'fixed_rate': 40.3399,
                'date_from': date(1998, 12, 31)
        },
        'MCF': {'currency_to': 'EUR',
                'fixed_rate': 6.55957,
                'date_from': date(1998, 12, 31)
        }, 
        'PTE': {'currency_to': 'EUR',
                'fixed_rate': 200.482,
                'date_from': date(1998, 12, 31)
        }, 
        'SML': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)
        },
        'ESP': {'currency_to': 'EUR',
                'fixed_rate': 166.386,
                'date_from': date(1998, 12, 31)
        }, 
        'VAL': {'currency_to': 'EUR',
                'fixed_rate': 1936.27,
                'date_from': date(1998, 12, 31)
        },
        'GRD': {'currency_to': 'EUR',
                'fixed_rate': 340.75,
                'date_from': date(2000,  6, 19)
        },
        'SIT': {'currency_to': 'EUR',
                'fixed_rate': 239.64,
                'date_from': date(2006,  7, 11)
        },
        'CYP': {'currency_to': 'EUR',
                'fixed_rate': 0.585274,
                'date_from': date(2007,  7, 10)
        },
        'MTL': {'currency_to': 'EUR',
                'fixed_rate': 0.4293,
                'date_from': date(2007,  7, 10)
        },
        'SKK': {'currency_to': 'EUR',
                'fixed_rate': 30.126,
                'date_from': date(2008,  7,  8)
        },
        'EEK': {'currency_to': 'EUR',
                'fixed_rate': 15.6466,
                'date_from': date(2010,  7, 13)
        },
        'ROL': {'currency_to': 'RON',
                'fixed_rate': 10000.0,
                'date_from': date(2005,  7,  1)
        },
        'RUR': {'currency_to': 'RUB',
                'fixed_rate': 1000.0,
                'date_from': date(1998,  1,  1)
        },
        'MXP': {'currency_to': 'MXN',
                'fixed_rate': 1000.0,
                'date_from': date(1993,  1,  1)
        },
        'UAK': {'currency_to': 'UAH',
                'fixed_rate': 100000.0,
                'date_from': date(1996,  9,  2)
        },
        'TRL': {'currency_to': 'TRY',
                'fixed_rate': 1000000.0,
                'date_from': date(2005,  1,  1)
        },
        'BGL': {'currency_to': 'BGN',
                'fixed_rate': 1000.0,
                'date_from': date(1999,  7,  5)
        },
        'PLZ': {'currency_to': 'PLN',
                'fixed_rate': 10000.0,
                'date_from': date(1995,  1,  1)
        },
        'CSD': {'currency_to': 'RSD',
                'fixed_rate': 1.0,
                'date_from': date(2003,  1,  1)
        },
        }

    today = date.today()
    if (dt.year < 1991) or (dt > today):
        return (None, None, None, 'Chybné datum, data nejsou k disposici')
    p = FXrate.objects.filter(date = dt)
    if p:
        tx = p[0].text
    else:
        surl = (
            'https://www.cnb.cz/cs/financni_trhy/devizovy_trh/' \
            'kurzy_devizoveho_trhu/denni_kurz.xml?date={:d}.{:d}.{:d}' \
                .format(dt.day, dt.month, dt.year))
        tx = getcache(surl, cd)[0]
        if not tx:
            logger.warning('No connection to CNB server')
            return (None, None, None, 'Chyba spojení se serverem ČNB')
    try:
        soup = newXML(tx)
        assert soup
        assert soup.find('tabulka',
                         {'typ': 'XML_TYP_CNB_KURZY_DEVIZOVEHO_TRHU'})
        dr = soup.find('kurzy', {'banka': 'CNB'})['datum']            
        dr = date(int(dr[6:]), int(dr[3:5]), int(dr[:2]))
    except:
        logger.error(
            'Invalid FX table structure for {:d}-{:02d}-{:02d}' \
                .format(dt.year, dt.month, dt.day))
        return (None, None, None, 'Chyba struktury kursové tabulky')
    if (not p) and ((dr == dt) or ((today - dt) > sd)):
        FXrate(date=dt, text=tx).save()
    ln = soup.find('radek', {'kod': curr})
    fr = 1.0
    curr_rq = curr
    if not ln:
        if use_fixed and \
           (curr in fixed_list) and \
           (fixed_list[curr]['date_from'] <= dt):
            curr = fixed_list[curr]['currency_to']
            ln = soup.find('radek', {'kod': curr})
            if not ln:
                return (None, None, dr, 'Kurs není v kursové tabulce')
            fr = fixed_list[curr_rq]['fixed_rate']
            if log_fixed != None:
                log_fixed.append(
                    {'currency_from': curr_rq,
                     'currency_to': fixed_list[curr_rq]['currency_to'],
                     'rate': fixed_list[curr_rq]['fixed_rate'],
                     'date_from': fixed_list[curr_rq]['date_from']})
        else:
            return (None, None, dr, 'Kurs není v kursové tabulce')
    try:
        qty = int(ln['mnozstvi'])
        if ln.has_attr('kurz'):
            rate = ln['kurz']
        elif ln.has_attr('pomer'):
            rate = ln['pomer']
        rate = float(rate.replace(',', '.'))
    except:
        logger.error(
            'Invalid FX table line for {:d}-{:02d}-{:02d}' \
                .format(dt.year, dt.month, dt.day))
        return (None, None, dr, 'Chyba řádku kursové tabulky')
    if log != None:
        log.append(
            {'currency': curr,
             'quantity': qty,
             'rate': rate,
             'date_required': dt,
             'date': dr})
    return ((rate / fr), qty, dr, None)

def getMPIrate(tp, dt, log=None):

    logger.debug(
        'MPI rate of type "{}" requested for {:d}-{:02d}-{:02d}' \
            .format(tp, dt.year, dt.month, dt.day))

    now = datetime.now()

    prefix = 'https://www.cnb.cz/cs/faq/vyvoj_'
    suffix = '_historie.txt'
    types = {'DISC': ('diskontni', 'PLATNA_OD|CNB_DISKONTNI_SAZBA_V_%'),
             'LOMB': ('lombard', 'PLATNA_OD|CNB_LOMBARDNI_SAZBA_V_%'),
             'REPO': ('repo', 'PLATNA_OD|CNB_REPO_SAZBA_V_%')}

    if tp not in types.keys():
        return (None, 'Chybný druh sazby')

    if (dt.year < 1990) or (dt > now.date()):
        return (None, 'Chybné datum, data nejsou k disposici')

    st = MPIstat.objects.get_or_create(type=tp)
    updated = st[0].timestamp_update.date()
    if st[1] or \
       ((not MPIrate.objects.filter(valid__gte=dt).exists()) and \
        ((updated - dt) < sd)):
        surl = prefix + types[tp][0] + suffix
        tx = getcache(surl, cd)[0]
        if not tx:
            logger.warning('No connection to CNB server')
            return (None, 'Chyba spojení se serverem ČNB')

        tx = tx.replace('\r', '').split('\n')
        if tx[0] != types[tp][1]:
            logger.error('Error in rate table for ' + types[tp][0])
            return (None, 'Chyba tabulky sazeb (1)')

        rates = []
        try:
            for l in tx[1:]:
                assert l[8] == '|'
                rates.append([float(l[9:].replace(',', '.')),
                              date(int(l[0:4]), int(l[4:6]), int(l[6:8]))])
        except:
            logger.error('Error in rate table for ' + types[tp][0])
            return (None, 'Chyba tabulky sazeb (2)')

        try:
            for r in rates:
                if st[1] or ((updated - r[1]) < sd):
                    MPIrate.objects.get_or_create(
                        type=tp,
                        rate=r[0],
                        valid=r[1])
        except:  # pragma: no cover
            logger.error('Error writing in database')
            return (None, 'Chyba zápisu do database (1)')
        try:
            MPIstat.objects.get_or_create(type=tp)[0].save()
        except:  # pragma: no cover
            logger.error('Error writing in database')
            return (None, 'Chyba zápisu do database (2)')
        
    d = MPIrate.objects.filter(type=tp, valid__lte=dt).order_by('-valid')
    if not d.exists():
        return (None, 'Sazba není k disposici')

    if log != None:
        log.append({'type': tp, 'rate': d[0].rate, 'date': dt})
    return (d[0].rate, None)
