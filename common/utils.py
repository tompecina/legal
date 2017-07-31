# -*- coding: utf-8 -*-
#
# common/utils.py
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

from logging import getLogger
from inspect import stack
import time
from datetime import date, timedelta
from calendar import monthrange, isleap
from math import inf
from xml.sax.saxutils import escape, unescape
from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfName
import requests
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfdoc import PDFName, PDFDictionary, PDFStream
from django.core import mail
from common.settings import TEST
from common.glob import (
    odp, ydconvs, mdconvs, registers, localsubdomain, localemail)
from common.models import Preset


class Logger:

    _logger = getLogger('logger')

    def _proc(meth, args, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['package'] = \
            stack()[2].frame.f_globals['__package__'].upper()
        if len(args) > 1:
            kwargs['extra']['request'] = args[1]
            args = list(args)
            del args[1]
            if len(args) > 1:
                kwargs['extra']['params'] = args[1]
                del args[1]
        meth(*args, **kwargs)

    def error(self, *args, **kwargs):
        Logger._proc(self._logger.error, args, kwargs)

    def warning(self, *args, **kwargs):
        Logger._proc(self._logger.warning, args, kwargs)

    def info(self, *args, **kwargs):
        Logger._proc(self._logger.info, args, kwargs)

    def debug(self, *args, **kwargs):
        Logger._proc(self._logger.debug, args, kwargs)


logger = Logger()


def lim(lower, arg, upper):
    """
    Return 'arg' bound by ['lower', 'upper'].
    """

    return min(max(lower, arg), upper)


def between(lower, arg, upper):
    """
    Check if 'arg' lies within ['lower', 'upper'].
    """

    return arg >= lower and arg <= upper


def pd(dt):
    """
    Return standard project-wide formatted string represenation of date 'dt'.
    """

    return '{0.day:02d}.{0.month:02d}.{0.year:02d}'.format(dt)


def easter_sunday(year):
    """
    Return the date of the Easter Sunday in 'year'.
    """

    a = year % 19
    b = year >> 2
    c = b // 25 + 1
    d = (c * 3) >> 2
    e = ((a * 19) - ((c * 8 + 5) // 25) + d + 15) % 30
    e += (29578 - a - e * 32) >> 10
    e -= ((year % 7) + b - d + e + 2) % 7
    d = e >> 5
    day = e - d * 31
    month = d + 3

    return date(year, month, day)


def movable_holiday(dt):
    """
    Check if 'dt' is a local movable banking holiday.
    """

    HOLIDAYS = (

        # Good Friday
        {'offset': -2, 'from': 1948, 'to': 1951},
        {'offset': -2, 'from': 2016, 'to': inf},

        # Easter Monday
        {'offset': 1, 'from': -inf, 'to': 1946},
        {'offset': 1, 'from': 1948, 'to': inf},

        # Ascension of Jesus
        {'offset': 39, 'from': -inf, 'to': 1946},
        {'offset': 39, 'from': 1948, 'to': 1951},

        # Whit Monday
        {'offset': 50, 'from': -inf, 'to': 1946},
        {'offset': 50, 'from': 1948, 'to': 1951},

        # Corpus Christi
        {'offset': 60, 'from': -inf, 'to': 1951},
    )

    year = dt.year
    es = easter_sunday(year)
    for hol in HOLIDAYS:
        if dt == (es + timedelta(hol['offset'])) \
            and between(hol['from'], year, hol['to']):
            return True
    return False


def holiday(dt):
    """
    Check if 'dt' is a local banking holiday.
    """

    HOLIDAYS = (

        # Circumcision of Jesus/New Year
        {'day': 1, 'month': 1, 'from': -inf, 'to': inf},

        # Epiphany/Magi
        {'day': 6, 'month': 1, 'from': -inf, 'to': 1946},
        {'day': 6, 'month': 1, 'from': 1948, 'to': 1951},

        # Purification of the Virgin
        {'day': 2, 'month': 2, 'from': -inf, 'to': 1925},

        # Birthday of T. G. Masaryk
        {'day': 7, 'month': 3, 'from': 1946, 'to': 1946},
        {'day': 7, 'month': 3, 'from': 1948, 'to': 1951},

        # Annunciation
        {'day': 25, 'month': 3, 'from': -inf, 'to': 1925},

        # Labor Day
        {'day': 1, 'month': 5, 'from': 1925, 'to': inf},

        # Liberation Day
        {'day': 8, 'month': 5, 'from': 1992, 'to': inf},
        {'day': 9, 'month': 5, 'from': 1946, 'to': 1946},
        {'day': 9, 'month': 5, 'from': 1952, 'to': 1991},

        # St. John of Nepomuk
        {'day': 16, 'month': 5, 'from': -inf, 'to': 1924}, # only in Bohemia

        # Saints Peter and Paul
        {'day': 29, 'month': 6, 'from': -inf, 'to': 1946},
        {'day': 29, 'month': 6, 'from': 1948, 'to': 1951},

        # Saints Cyril and Methodius
        {'day': 5, 'month': 7, 'from': -inf, 'to': 1924}, # only in Moravia
        {'day': 5, 'month': 7, 'from': 1925, 'to': 1951},
        {'day': 5, 'month': 7, 'from': 1990, 'to': inf},

        # John Huss
        {'day': 6, 'month': 7, 'from': 1925, 'to': 1951},
        {'day': 6, 'month': 7, 'from': 1990, 'to': inf},

        # Ascension of the Virgin
        {'day': 15, 'month': 8, 'from': -inf, 'to': 1951},

        # Nativity of the Virgin
        {'day': 8, 'month': 9, 'from': -inf, 'to': 1924},

        # St. Wenceslaus
        {'day': 28, 'month': 9, 'from': -inf, 'to': 1924}, # only in Bohemia
        {'day': 28, 'month': 9, 'from': 1925, 'to': 1946},
        {'day': 28, 'month': 9, 'from': 1948, 'to': 1951},
        {'day': 28, 'month': 9, 'from': 2000, 'to': inf},

        # Creation of Czechoslovakia/Nationalization Day
        {'day': 28, 'month': 10, 'from': 1919, 'to': 1939},
        {'day': 28, 'month': 10, 'from': 1946, 'to': 1969},
        {'day': 28, 'month': 10, 'from': 1988, 'to': inf},

        # All Saints
        {'day': 1, 'month': 11, 'from': -inf, 'to': 1951},

        # Velvet Revolution
        {'day': 17, 'month': 11, 'from': 2000, 'to': inf},

        # Immaculate Conception
        {'day': 8, 'month': 12, 'from': -inf, 'to': 1946},
        {'day': 28, 'month': 9, 'from': 1948, 'to': 1951},

        # Christmas Eve
        {'day': 24, 'month': 12, 'from': 1966, 'to': 1975},
        {'day': 24, 'month': 12, 'from': 1984, 'to': inf},

        # Nativity of Jesus/First Christmas Holiday
        {'day': 25, 'month': 12, 'from': -inf, 'to': inf},

        # St. Stephen/Second Christmas Holiday
        {'day': 26, 'month': 12, 'from': -inf, 'to': inf},
    )

    EXTRA_HOLIDAYS = {
        1966: ((8, 6), (9, 3), (10, 1), (10, 29), (11, 26)),
        1967: (
            (1, 7), (1, 21), (2, 4), (2, 18), (3, 4), (3, 18), (4, 1),
            (4, 15), (4, 29), (5, 13), (5, 27), (6, 10), (6, 24), (7, 8),
            (7, 22), (8, 5), (8, 19), (9, 2), (9, 16), (9, 30), (10, 14),
            (11, 11), (11, 25), (12, 9), (12, 23)),
        1968: (
            (1, 13), (1, 27), (2, 10), (2, 24), (3, 9), (3, 23), (4, 6),
            (4, 20), (5, 4), (5, 18), (6, 1), (6, 15), (6, 29), (7, 13),
            (7, 27), (8, 10), (8, 24), (9, 7), (9, 21), (12, 23), (12, 30),
            (12, 31)),
        1969: ((5, 2), (10, 27), (12, 31)),
        1970: ((1, 2), (10, 30)),
        1971: ((10, 29),),
        1972: ((5, 8),),
        1973: ((12, 31),),
        1974: ((5, 10), (10, 28), (12, 30), (12, 31)),
        1975: ((5, 2),),
        1978: ((5, 8),),
        1979: ((4, 30), (5, 7), (5, 8), (12, 24), (12, 31)),
        1980: ((5, 2),),
        1981: ((1, 2),),
        1984: ((4, 30), (12, 31)),
        1985: ((5, 2), (5, 3), (5, 10), (12, 30), (12, 31)),
        1986: ((5, 2), (12, 31)),
        1987: ((1, 2), (1, 9), (12, 31)),
        1988: ((1, 8),),
        1989: ((5, 8),),
        1990: ((4, 30),),
    }

    EXTRA_NON_HOLIDAYS = {
        1968: ((12, 21), (12, 22), (12, 28), (12, 29)),
        1969: ((5, 4), (10, 25), (12, 28)),
        1970: ((1, 3), (1, 4), (4, 4), (5, 16), (10, 25), (11, 14), (12, 27)),
        1971: ((1, 3), (4, 17), (10, 24), (12, 24)),
        1972: ((4, 8), (5, 6), (5, 13), (11, 11)),
        1973: ((4, 14), (9, 29), (11, 17), (12, 22), (12, 29)),
        1974: (
            (4, 6), (5, 12), (9, 28), (11, 16), (12, 22), (12, 28), (12, 29)),
        1975: ((3, 22), (4, 5), (5, 4), (9, 27), (11, 15), (12, 27), (12, 28)),
        1977: ((4, 16), (9, 24), (11, 12)),
        1978: ((3, 11), (4, 1), (5, 6), (5, 13), (9, 23), (9, 23), (10, 14)),
        1979: (
            (3, 31), (4, 21), (4, 28), (5, 5), (5, 6), (5, 12), (9, 22),
            (11, 10), (12, 22), (12, 29)),
        1980: ((3, 22), (4, 12), (5, 4), (9, 20), (10, 11)),
        1981: ((1, 4), (4, 25), (10, 24), (11, 28)),
        1982: ((4, 17),),
        1983: ((4, 9), (9, 24), (10, 22)),
        1984: (
            (3, 31), (4, 28), (5, 12), (9, 29), (11, 10), (12, 22), (12, 29)),
        1985: (
            (3, 23), (4, 13), (5, 4), (5, 5), (5, 12), (9, 28), (10, 19),
            (11, 16), (12, 21), (12, 28), (12, 29)),
        1986: (
            (3, 15), (11, 22), (4, 5), (5, 4), (10, 18), (10, 22), (12, 27),
            (12, 28)),
        1987: ((1, 3), (1, 4), (4, 25), (10, 17), (12, 12), (12, 27)),
        1988: ((1, 3), (4, 9)),
        1989: ((3, 11), (5, 6)),
        1990: ((4, 28),),
    }

    year = dt.year
    month = dt.month
    day = dt.day

    if year in EXTRA_HOLIDAYS and (month, day) in EXTRA_HOLIDAYS[year]:
        return True

    if year in EXTRA_NON_HOLIDAYS and (month, day) in EXTRA_NON_HOLIDAYS[year]:
        return False

    for hol in HOLIDAYS:
        if day == hol['day'] and month == hol['month'] and \
           between(hol['from'], year, hol['to']):
            return True

    if movable_holiday(dt):
        return True

    return dt.weekday() > (5 if dt < date(1968, 10, 5) else 4)


def ply(dt, num):
    """
    Return 'dt' plus 'num' years.
    """

    year = dt.year + num
    month = dt.month
    day = min(dt.day, monthrange(year, month)[1])
    return date(year, month, day)


def plm(dt, num):
    """
    Return 'dt' plus 'num' months.
    """

    month = dt.month + num
    year = dt.year + ((month - 1) // 12)
    month = ((month - 1) % 12) + 1
    day = min(dt.day, monthrange(year, month)[1])
    return date(year, month, day)


def yfactor(beg, end, dconv):
    """
    Return number of years between 'beg' and 'end', using day-count convention
    'dconv'.
    """

    if end < beg or dconv not in ydconvs:
        return None

    if dconv.startswith('ACT'):
        beg += odp
        y1 = beg.year
        m1 = beg.month
        d1 = beg.day
        end += odp
        y2 = end.year
        m2 = end.month
        d2 = end.day
        if dconv == 'ACT/ACT':
            leap = nleap = 0
            while y1 < y2:
                n = (date((y1 + 1), 1, 1) - date(y1, m1, d1)).days
                if isleap(y1):
                    leap += n
                else:
                    nleap += n
                d1 = m1 = 1
                y1 += 1
            n = (date(y2, m2, d2) - date(y1, m1, d1)).days
            if isleap(y1):
                leap += n
            else:
                nleap += n
            return (nleap / 365) + (leap / 366)
        if dconv == 'ACT/365':
            return (end - beg).days / 365
        if dconv == 'ACT/360':
            return (end - beg).days / 360
        return (end - beg).days / 364

    else:
        y1 = beg.year
        m1 = beg.month
        d1 = beg.day
        y2 = end.year
        m2 = end.month
        d2 = end.day
        if dconv == '30U/360':
            if d2 == 31 and d1 >= 30:
                d2 = 30
            if d1 == 31:
                d1 = 30
        elif dconv == '30E/360':
            if d1 == 31:
                d1 = 30
            if d2 == 31:
                d2 = 30
        elif dconv == '30E/360 ISDA':
            if d1 == monthrange(y1, m1)[1]:
                d1 = 30
            if d2 == monthrange(y2, m2)[1]:
                d2 = 30
        elif dconv == '30E+/360':
            if d1 == 31:
                d1 = 30
            if d2 == 31:
                m2 += 1
                d2 = 1
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360


def mfactor(beg, end, dconv):
    """
    Return number of months between 'beg' and 'end', using day-count convention
    'dconv'.
    """

    if end < beg or dconv not in mdconvs:
        return None

    if dconv == 'ACT':
        beg += odp
        y = beg.year
        m = beg.month
        d = beg.day
        r = 0.0
        while y < end.year or m != end.month:
            if d == 1:
                r += 1.0
            else:
                dm = monthrange(y, m)[1]
                r += float(dm - d + 1) / dm
            m += 1
            if m > 12:
                m = 1
                y += 1
            d = 1
        r += float(end.day - d + 1) / monthrange(y, m)[1]
        return r

    else:
        y1 = beg.year
        m1 = beg.month
        d1 = beg.day
        y2 = end.year
        m2 = end.month
        d2 = end.day
        if dconv == '30U':
            if d2 == 31 and d1 >= 30:
                d2 = 30
            if d1 == 31:
                d1 = 30
        elif dconv == '30E':
            if d1 == 31:
                d1 = 30
            if d2 == 31:
                d2 = 30
        elif dconv == '30E ISDA':
            if d1 == monthrange(y1, m1)[1]:
                d1 = 30
            if d2 == monthrange(y2, m2)[1]:
                d2 = 30
        elif dconv == '30E+':
            if d1 == 31:
                d1 = 30
            if d2 == 31:
                m2 += 1
                d2 = 1
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 30


def grammar(num, noun):
    """
    Return correct form of plural, 'num noun(s)'.
    """

    a = abs(num)
    if a == 1:
        s = noun[0]
    elif not a or a > 4:
        s = noun[2]
    else:
        s = noun[1]
    return '{:d} {}'.format(num, s)


def getbutton(request):
    """
    Get id of button pressed.
    """

    for i in request.POST:
        if i.startswith('submit_'):
            return i[7:]
    return None


def p2c(string):
    """
    Convert periods in 'string' to commas.
    """

    return string.replace('.', ',')


def c2p(string):
    """
    Convert commas in 'string' to periods.
    """

    return string.replace(',', '.')


class Lf(float):
    """
    Class for correct localized formatting of floats.
    """

    def __format__(self, format):
        return p2c(super().__format__(format))


def formam(amount):
    """
    Format 'amount' according to its type.
    """

    if isinstance(amount, int):
        s = '{:d}'.format(amount)
    else:
        s = '{:.2f}'.format(Lf(amount))
    i = s.find(',')
    if i < 0:
        i = len(s)
    l = list(s)
    i -= 3
    while i > 0 and l[i-1] != '-':
        l.insert(i, '.')
        i -= 3
    return ''.join(l)


def unrequire(form, fields):
    """
    Reset the required attribute for 'fields' in 'form'.
    """

    for fld in fields:
        form.fields[fld].required = False


def xmldecorate(tag, table):
    """
    Add all attributes in 'table' to XML tag 'tag'.
    """

    if tag.name in table:
        for key, val in table[tag.name].items():
            tag[key] = val
    return tag


def xmlescape(string):
    """
    XML-escape and strip 'string'.
    """

    return escape(string).strip()


def xmlunescape(string):
    """
    Strip and XML-unescape 'string'.
    """

    return unescape(string.strip())


def newXML(data):
    """
    Create new XML soup using correct parser, either from scratch or
    from 'data'.
    """

    if data:
        xml = BeautifulSoup(data, 'xml')
    else:
        xml = BeautifulSoup('', 'lxml')
    xml.is_xml = True
    return xml


def getXML(string):
    """
    Get XML soup from 'string'.
    """

    if string.startswith(b'<?xml'):
        try:
            return newXML(string)
        except:  # pragma: no cover
            return None
    try:
        r = PdfReader(fdata=string)
        c = r['/Root']
        m = c.get(PdfName('Data'))
        return newXML(m.stream.encode('latin-1'))
    # these are legacy branches; I don't believe such files actually exist
    except:  # pragma: no cover
        try:
            r = PdfReader(fdata=string)
            c = r['/Root']
            m = c.get(PdfName('Metadata'))
            return newXML(m.stream.encode('latin-1'))
        except:
            try:
                return newXML(
                    string.encode('latin-1').split('endstream')[0]
                    .split('stream')[1])
            except:
                try:
                    return newXML(string.encode('latin-1'))
                except:
                    return None


def iso2date(tag):
    """
    Extract date from XML tag 'tag'.
    """

    if tag.has_attr('year') and tag.has_attr('month') and tag.has_attr('day'):
        return date(int(tag['year']), int(tag['month']), int(tag['day']))
    t = tag.text.strip().split('-')
    return date(int(t[0]), int(t[1]), int(t[2]))


class CanvasXML(Canvas):
    """
    Subclassed Canvas adding XML information on save.
    """

    def save(self):
        data = PDFStream(
            dictionary=PDFDictionary(
                {'Type': PDFName('Data'),
                 'Subtype': PDFName('XML')}),
            content=self.xml,
            filters=None)
        self._doc.Reference(data)
        if 'Data' not in self._doc.Catalog.__NoDefault__:
            self._doc.Catalog.__NoDefault__.append('Data')
        self._doc.Catalog.__setattr__('Data', data)
        Canvas.save(self)


TIMEOUT = 1000


def get(*args, **kwargs):  # pragma: no cover
    """
    Test-compatible get.
    """

    if TEST:
        from .tests import testreq
        return testreq(False, *args)
    else:
        if 'timeout' not in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.get(*args, **kwargs)


def post(*args, **kwargs):  # pragma: no cover
    """
    Test-compatible post.
    """

    if TEST:
        from .tests import testreq
        return testreq(True, *args)
    else:
        if 'timeout' not in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.post(*args, **kwargs)


def sleep(*args, **kwargs):  # pragma: no cover
    """
    Test-compatible sleep.
    """

    if not TEST:
        time.sleep(*args, **kwargs)


def send_mail(subject, text, recipients):
    """
    Project-wide mail sender.
    """

    try:
        mail.send_mail(
            subject,
            text,
            'Server {} <{}>'.format(localsubdomain, localemail),
            recipients,
            fail_silently=True)
    except:  # pragma: no cover
        logger.warning('Failed to send mail')


class Pager:
    """
    General pager.
    """

    def __init__(self, start, total, url, p, batch):

        def link(n):
            p['start'] = n
            return '{}?{}'.format(url, p.urlencode())

        self.curr = (start // batch) + 1
        self.total = ((total - 1) // batch) + 1
        self.linkbb = None
        self.linkb = None
        self.linkf = None
        self.linkff = None
        if start:
            self.linkbb = link(0)
            self.linkb = link(start - batch)
        if (start + batch) < total:
            self.linkf = link(start + batch)
            self.linkff = link(((total - 1) // batch) * batch)


def composeref(*args):
    """
    Compose reference from senate, register, number, year and (optional) page.
    """

    if args[0]:
        s = '{:d} '.format(args[0])
    else:
        s = ''
    s += '{} {:d}/{:d}'.format(*args[1:4])
    if len(args) == 5:
        s += '-{:d}'.format(args[4])
    return s


def decomposeref(ref):
    """
    Decompose reference into senate, register, number, year and (optional) page.
    """

    s = ref.split('-')
    if len(s) == 1:
        page = 0
    else:
        page = int(s[1])
    s = s[0].split()
    if s[0].isdigit():
        senate = int(s[0])
        del s[0]
    else:
        senate = 0
    while not s[1][0].isdigit():
        s[1] = ' '.join(s[:2])
        del s[0]
    register = s[0]
    t = s[1].split('/')
    if page:
        return senate, register, int(t[0]), int(t[1]), page
    return senate, register, int(t[0]), int(t[1])


def normreg(reg):
    """
    Normalize register 'reg'.
    """

    rl = reg.lower()
    for r in registers:
        if r.lower() == rl:
            return r
    return reg.title()


def xmlbool(val):
    """
    Return XML representation of a Boolean value.
    """

    return 'true' if val else 'false'


def icontains(needle, haystack):
    """
    Search function for case-insensitive 'contains'.
    """

    return needle.lower() in haystack.lower()


def istartswith(needle, haystack):
    """
    Search function for case-insensitive 'startswith'.
    """

    return haystack.lower().startswith(needle.lower())


def iendswith(needle, haystack):
    """
    Search function for case-insensitive 'endswith'.
    """

    return haystack.lower().endswith(needle.lower())


def iexact(needle, haystack):
    """
    Search function for case-insensitive 'exact'.
    """

    return needle.lower() == haystack.lower()


def text_opt(needle, haystack, opt):
    """
    Search function with selectable search method.
    """

    if not needle:
        return True
    if not haystack:
        return False
    return [icontains, istartswith, iendswith, iexact][opt](needle, haystack)


def normalize(string):
    """
    Replace hard-spaces, strip and split.
    """
    return ' '.join(string.replace('\u00a0', ' ').strip().split())


def icmp(x, y):
    """
    Case-insensitive comparison.
    """

    if x and y:
        return x.lower() == y.lower()
    return x == y


def getpreset(id):
    """
    Get current preset.
    """

    try:
        return Preset.objects.filter(name=id, valid__lte=date.today()) \
            .latest('valid').value
    except:
        return 0
