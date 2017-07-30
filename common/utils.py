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


def lim(lower, x, upper):

    return min(max(lower, x), upper)


def between(lower, x, upper):

    return x >= lower and x <= upper


def easter_monday(y):

    g = y % 19
    e = 0
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    p = i - j + e
    d = 1 + (p + 28 + (p + 6) // 40) % 31
    m = 3 + (p + 27) // 30
    return date(y, m, d)


def movable_holiday(dt):

    HOLIDAYS = (
        # Good Friday
        {'offset': -3, 'from': -inf, 'to': 1925},
        {'offset': -3, 'from': 1946, 'to': 1946},
        {'offset': -3, 'from': 1948, 'to': 1951},
        {'offset': -3, 'from': 2016, 'to': inf},
        # Easter Monday
        {'offset': 0, 'from': 1939, 'to': 1946},
        {'offset': 0, 'from': 1948, 'to': inf},
        # Ascension
        {'offset': 38, 'from': -inf, 'to': 1946},
        {'offset': 38, 'from': 1948, 'to': 1951},
        # Whit Monday
        {'offset': 49, 'from': 1939, 'to': 1946},
        {'offset': 49, 'from': 1948, 'to': 1951},
        # Corpus Christi
        {'offset': 59, 'from': -inf, 'to': 1951},
    )

    year = dt.year
    em = easter_monday(year)
    for hol in HOLIDAYS:
        if dt == (em + timedelta(hol['offset'])) \
            and between(hol['from'], year, hol['to']):
            return True
    return False

def pd(d):

    return '{0.day:02d}.{0.month:02d}.{0.year:02d}'.format(d)


def holiday(dt):

    HOLIDAYS = (
        {'day': 1, 'month': 1, 'from': -inf, 'to': inf},
        {'day': 6, 'month': 1, 'from': -inf, 'to': 1946},
        {'day': 2, 'month': 2, 'from': -inf, 'to': 1925},
        {'day': 7, 'month': 3, 'from': 1946, 'to': 1946},
        {'day': 25, 'month': 3, 'from': -inf, 'to': 1925},
        {'day': 1, 'month': 5, 'from': 1925, 'to': inf},
        {'day': 8, 'month': 5, 'from': 1992, 'to': inf},
        {'day': 9, 'month': 5, 'from': 1952, 'to': 1991},
        {'day': 16, 'month': 5, 'from': -inf, 'to': 1924},
        {'day': 29, 'month': 6, 'from': -inf, 'to': 1946},
        {'day': 5, 'month': 7, 'from': 1925, 'to': 1951},
        {'day': 5, 'month': 7, 'from': 1990, 'to': inf},
        {'day': 6, 'month': 7, 'from': 1925, 'to': 1951},
        {'day': 6, 'month': 7, 'from': 1990, 'to': inf},
        {'day': 15, 'month': 8, 'from': -inf, 'to': 1951},
        {'day': 8, 'month': 9, 'from': -inf, 'to': 1924},
        {'day': 28, 'month': 9, 'from': -inf, 'to': 1946},
        {'day': 28, 'month': 9, 'from': 2000, 'to': inf},
        {'day': 28, 'month': 10, 'from': 1919, 'to': 1939},
        {'day': 28, 'month': 10, 'from': 1946, 'to': 1969},
        {'day': 28, 'month': 10, 'from': 1988, 'to': inf},
        {'day': 1, 'month': 11, 'from': -inf, 'to': 1951},
        {'day': 17, 'month': 11, 'from': 2000, 'to': inf},
        {'day': 8, 'month': 12, 'from': -inf, 'to': 1946},
        {'day': 24, 'month': 12, 'from': 1966, 'to': 1975},
        {'day': 24, 'month': 12, 'from': 1984, 'to': inf},
        {'day': 25, 'month': 12, 'from': -inf, 'to': inf},
        {'day': 26, 'month': 12, 'from': 1939, 'to': inf},
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

    EXTRA_NOT_HOLIDAYS = {
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

    if year in EXTRA_NOT_HOLIDAYS and (month, day) in EXTRA_NOT_HOLIDAYS[year]:
        return False

    for hol in HOLIDAYS:
        if day == hol['day'] and month == hol['month'] and \
           between(hol['from'], year, hol['to']):
            return True

    if movable_holiday(dt):
        return True

    return dt.weekday() > (5 if dt < date(1968, 10, 5) else 4)


def ply(t, n):

    y = t.year + n
    m = t.month
    d = min(t.day, monthrange(y, m)[1])
    return date(y, m, d)


def plm(t, n):

    m = t.month + n
    y = t.year + ((m - 1) // 12)
    m = ((m - 1) % 12) + 1
    d = min(t.day, monthrange(y, m)[1])
    return date(y, m, d)


def yfactor(beg, end, dconv):

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
            return (nleap / 365.0) + (leap / 366.0)
        if dconv == 'ACT/365':
            return (end - beg).days / 365.0
        if dconv == 'ACT/360':
            return (end - beg).days / 360.0
        return (end - beg).days / 364.0

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
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360.0


def mfactor(beg, end, dconv):

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
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 30.0


def grammar(n, t):

    a = abs(n)
    if a == 1:
        s = t[0]
    elif not a or a > 4:
        s = t[2]
    else:
        s = t[1]
    return '{:d} {}'.format(n, s)


def getbutton(request):

    for i in request.POST:
        if i.startswith('submit_'):
            return i[7:]
    return None


def p2c(s):

    return s.replace('.', ',')

def c2p(s):

    return s.replace(',', '.')


class Lf(float):

    def __format__(self, format):
        return p2c(super().__format__(format))


def formam(x):

    if isinstance(x, int):
        s = '{:d}'.format(x)
    else:
        s = '{:.2f}'.format(Lf(x))
    i = s.find(',')
    if i < 0:
        i = len(s)
    l = list(s)
    i -= 3
    while i > 0 and l[i-1] != '-':
        l.insert(i, '.')
        i -= 3
    return ''.join(l)


def getint(s):

    if s:
        return int(s)
    return 0


def unrequire(f, flds):

    for fld in flds:
        f.fields[fld].required = False


def xmldecorate(tag, table):

    if tag.name in table:
        for key, val in table[tag.name].items():
            tag[key] = val
    return tag


def xmlescape(t):

    return escape(t).strip()


def xmlunescape(t):

    return unescape(t.strip())


def rmdsl(l):

    if l:
        s = l[-1]
        for i in range((len(l) - 2), -1, -1):
            if s == l[i]:
                del l[i]
            else:
                s = l[i]
    return l


def newXML(data):

    if data:
        xml = BeautifulSoup(data, 'xml')
    else:
        xml = BeautifulSoup('', 'lxml')
    xml.is_xml = True
    return xml


def getXML(d):

    if d.startswith(b'<?xml'):
        try:
            return newXML(d)
        except:  # pragma: no cover
            return None
    try:
        r = PdfReader(fdata=d)
        c = r['/Root']
        m = c.get(PdfName('Data'))
        return newXML(m.stream.encode('latin-1'))
    # these are legacy branches; I don't believe such files actually exist
    except:  # pragma: no cover
        try:
            r = PdfReader(fdata=d)
            c = r['/Root']
            m = c.get(PdfName('Metadata'))
            return newXML(m.stream.encode('latin-1'))
        except:
            try:
                return newXML(
                    d.encode('latin-1').split('endstream')[0]
                    .split('stream')[1])
            except:
                try:
                    return newXML(d.encode('latin-1'))
                except:
                    return None


def iso2date(tag):

    if tag.has_attr('year') and tag.has_attr('month') and tag.has_attr('day'):
        return date(int(tag['year']), int(tag['month']), int(tag['day']))
    t = tag.text.strip().split('-')
    return date(int(t[0]), int(t[1]), int(t[2]))


class CanvasXML(Canvas):

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

    if TEST:
        from .tests import testreq
        return testreq(False, *args)
    else:
        if 'timeout' not in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.get(*args, **kwargs)


def post(*args, **kwargs):  # pragma: no cover

    if TEST:
        from .tests import testreq
        return testreq(True, *args)
    else:
        if 'timeout' not in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.post(*args, **kwargs)


def sleep(*args, **kwargs):  # pragma: no cover

    if not TEST:
        time.sleep(*args, **kwargs)


def send_mail(subject, text, recipients):

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

    if args[0]:
        s = '{:d} '.format(args[0])
    else:
        s = ''
    s += '{} {:d}/{:d}'.format(*args[1:4])
    if len(args) == 5:
        s += '-{:d}'.format(args[4])
    return s


def decomposeref(ref):

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

    rl = reg.lower()
    for r in registers:
        if r.lower() == rl:
            return r
    return reg.title()


def xmlbool(x):

    if x:
        return 'true'
    return 'false'


def icontains(needle, haystack):

    return needle.lower() in haystack.lower()


def istartswith(needle, haystack):

    return haystack.lower().startswith(needle.lower())

def iendswith(needle, haystack):
    return haystack.lower().endswith(needle.lower())


def iexact(needle, haystack):

    return needle.lower() == haystack.lower()


def text_opt(needle, haystack, opt):

    if not needle:
        return True
    if not haystack:
        return False
    return [icontains, istartswith, iendswith, iexact][opt](needle, haystack)


def normalize(s):

    return ' '.join(s.replace('\u00a0', ' ').strip().split())


def icmp(x, y):

    if x and y:
        return x.lower() == y.lower()
    return x == y


def getpreset(id):

    try:
        return Preset.objects.filter(name=id, valid__lte=date.today()) \
            .latest('valid').value
    except:
        return 0
