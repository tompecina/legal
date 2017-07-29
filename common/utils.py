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


def easter(dt):

    y = dt.year
    g = y % 19
    e = 0
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    p = i - j + e
    d = 1 + (p + 28 + (p + 6) // 40) % 31
    m = 3 + (p + 27) // 30
    dt2 = dt + timedelta(3)
    return (dt.month == m and dt.day == d) \
        or (y >= 2016 and dt2.month == m and dt2.day == d)


def pd(d):

    return '{0.day:02d}.{0.month:02d}.{0.year:02d}'.format(d)


HOLIDAY = (
    {'f': None, 't': None, 'd':  1, 'm':  1},
    {'f': None, 't': None, 'd':  1, 'm':  5},
    {'f': 1992, 't': None, 'd':  8, 'm':  5},
    {'f': None, 't': 1991, 'd':  9, 'm':  5},
    {'f': None, 't': 1951, 'd':  5, 'm':  7},
    {'f': 1990, 't': None, 'd':  5, 'm':  7},
    {'f': None, 't': 1951, 'd':  6, 'm':  7},
    {'f': 1990, 't': None, 'd':  6, 'm':  7},
    {'f': 2000, 't': None, 'd': 28, 'm':  9},
    {'f': None, 't': 1969, 'd': 28, 'm': 10},
    {'f': 1988, 't': None, 'd': 28, 'm': 10},
    {'f': 2000, 't': None, 'd': 17, 'm': 11},
    {'f': 1966, 't': 1975, 'd': 24, 'm': 12},
    {'f': 1984, 't': None, 'd': 24, 'm': 12},
    {'f': None, 't': None, 'd': 25, 'm': 12},
    {'f': None, 't': None, 'd': 26, 'm': 12},
)

EXTRA_HOLIDAY = (
    (1966, 8, 6), (1966, 9, 3), (1966, 10, 1), (1966, 10, 29),
    (1966, 11, 26), (1967, 1, 7), (1967, 1, 21), (1967, 2, 4),
    (1967, 2, 18), (1967, 3, 4), (1967, 3, 18), (1967, 4, 1),
    (1967, 4, 15), (1967, 4, 29), (1967, 5, 13), (1967, 5, 27),
    (1967, 6, 10), (1967, 6, 24), (1967, 7, 8), (1967, 7, 22),
    (1967, 8, 5), (1967, 8, 19), (1967, 9, 2), (1967, 9, 16),
    (1967, 9, 30), (1967, 10, 14), (1967, 11, 11), (1967, 11, 25),
    (1967, 12, 9), (1967, 12, 23), (1968, 1, 13), (1968, 1, 27),
    (1968, 2, 10), (1968, 2, 24), (1968, 3, 9), (1968, 3, 23),
    (1968, 4, 6), (1968, 4, 20), (1968, 5, 4), (1968, 5, 18),
    (1968, 6, 1), (1968, 6, 15), (1968, 6, 29), (1968, 7, 13),
    (1968, 7, 27), (1968, 8, 10), (1968, 8, 24), (1968, 9, 7),
    (1968, 9, 21), (1968, 12, 23), (1968, 12, 30), (1968, 12, 31),
    (1969, 5, 2), (1969, 10, 27), (1969, 12, 31), (1970, 1, 2),
    (1970, 10, 30), (1971, 10, 29), (1972, 5, 8), (1973, 12, 31),
    (1974, 5, 10), (1974, 10, 28), (1974, 12, 30), (1974, 12, 31),
    (1975, 5, 2), (1978, 5, 8), (1979, 4, 30), (1979, 5, 7),
    (1979, 5, 8), (1979, 12, 24), (1979, 12, 31), (1980, 5, 2),
    (1981, 1, 2), (1984, 4, 30), (1984, 12, 31), (1985, 5, 2),
    (1985, 5, 3), (1985, 5, 10), (1985, 12, 30), (1985, 12, 31),
    (1986, 5, 2), (1986, 12, 31), (1987, 1, 2), (1987, 1, 9),
    (1987, 12, 31), (1988, 1, 8), (1989, 5, 8), (1990, 4, 30),
)

EXTRA_NOT_HOLIDAY = (
    (1968, 12, 21), (1968, 12, 22), (1968, 12, 28), (1968, 12, 29),
    (1969, 5, 4), (1969, 10, 25), (1969, 12, 28), (1970, 1, 3),
    (1970, 1, 4), (1970, 4, 4), (1970, 5, 16), (1970, 10, 25),
    (1970, 11, 14), (1970, 12, 27), (1971, 1, 3), (1971, 4, 17),
    (1971, 10, 24), (1971, 12, 24), (1972, 4, 8), (1972, 5, 6),
    (1972, 5, 13), (1972, 11, 11), (1973, 4, 14), (1973, 9, 29),
    (1973, 11, 17), (1973, 12, 22), (1973, 12, 29), (1974, 4, 6),
    (1974, 5, 12), (1974, 9, 28), (1974, 11, 16), (1974, 12, 22),
    (1974, 12, 28), (1974, 12, 29), (1975, 3, 22), (1975, 4, 5),
    (1975, 5, 4), (1975, 9, 27), (1975, 11, 15), (1975, 12, 27),
    (1975, 12, 28), (1977, 4, 16), (1977, 9, 24), (1977, 11, 12),
    (1978, 3, 11), (1978, 4, 1), (1978, 5, 6), (1978, 5, 13),
    (1978, 9, 23), (1978, 9, 23), (1978, 10, 14), (1979, 3, 31),
    (1979, 4, 21), (1979, 4, 28), (1979, 5, 5), (1979, 5, 6),
    (1979, 5, 12), (1979, 9, 22), (1979, 11, 10), (1979, 12, 22),
    (1979, 12, 29), (1980, 3, 22), (1980, 4, 12), (1980, 5, 4),
    (1980, 9, 20), (1980, 10, 11), (1981, 1, 4), (1981, 4, 25),
    (1981, 10, 24), (1981, 11, 28), (1982, 4, 17), (1983, 4, 9),
    (1983, 9, 24), (1983, 10, 22), (1984, 3, 31), (1984, 4, 28),
    (1984, 5, 12), (1984, 9, 29), (1984, 11, 10), (1984, 12, 22),
    (1984, 12, 29), (1985, 3, 23), (1985, 4, 13), (1985, 5, 4),
    (1985, 5, 5), (1985, 5, 12), (1985, 9, 28), (1985, 10, 19),
    (1985, 11, 16), (1985, 12, 21), (1985, 12, 28), (1985, 12, 29),
    (1986, 3, 15), (1986, 11, 22), (1986, 4, 5), (1986, 5, 4),
    (1986, 10, 18), (1986, 10, 22), (1986, 12, 27), (1986, 12, 28),
    (1987, 1, 3), (1987, 1, 4), (1987, 4, 25), (1987, 10, 17),
    (1987, 12, 12), (1987, 12, 27), (1988, 1, 3), (1988, 4, 9),
    (1989, 3, 11), (1989, 5, 6), (1990, 4, 28),
)

def tod(dt):

    y = dt.year
    m = dt.month
    d = dt.day

    if (y, m, d) in EXTRA_HOLIDAY:
        return True

    if (y, m, d) in EXTRA_NOT_HOLIDAY:
        return False

    for h in HOLIDAY:
        if d == h['d'] and m == h['m'] and (not h['f'] or y >= h['f']) \
            and (not h['t'] or y <= h['t']):
            return True

    if easter(dt):
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


def lim(lower, x, upper):

    return min(max(lower, x), upper)


def between(lower, x, upper):

    return x >= lower and x <= upper


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
