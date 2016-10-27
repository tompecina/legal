# -*- coding: utf-8 -*-
#
# common/utils.py
#
# Copyright (C) 2011-16 Tomáš Pecina <tomas@pecina.cz>
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

from django.http import QueryDict
from django.core import mail
from decimal import Decimal
from datetime import date, timedelta
from calendar import monthrange, isleap
from xml.sax.saxutils import escape, unescape
from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfName
from http import HTTPStatus
import requests
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfdoc import PDFName, PDFDictionary, PDFStream
from cache.models import Cache
from .glob import (
    hd, odp, ydconvs, mdconvs, registers, localsubdomain, localemail)
from .settings import TEST

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
    return ((dt.month == m) and (dt.day == d)) or \
           ((y >= 2016) and (dt2.month == m) and (dt2.day == d))

def pd(d):
    return '%d. %d. %d' % (d.day, d.month, d.year)

def tod(dt):

    y = dt.year
    m = dt.month
    d = dt.day

    for h in hd:
        if (d == h['d']) and \
           (m == h['m']) and \
           ((not h['f']) or (y >= h['f'])) and \
           ((not h['t']) or (y <= h['t'])):
            return True

    if easter(dt):
        return True

    return (dt.weekday() > 4)

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
    if (end < beg) or (dconv not in ydconvs):
        return None

    if dconv[:3] == 'ACT':
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
            if (d2 == 31) and (d1 >= 30):
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
    if (end < beg) or (dconv not in mdconvs):
        return None
    
    if dconv == 'ACT':
        beg += odp
        y = beg.year
        m = beg.month
        d = beg.day
        r = 0.0
        while (y < end.year) or (m != end.month):
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
            if (d2 == 31) and (d1 >= 30):
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
    elif (not a) or (a > 4):
        s = t[2]
    else:
        s = t[1]
    return ('%d %s' % (n, s))

def getbutton(request):
    for i in request.POST:
        if i.startswith('submit_'):
            return i[7:]
    return None

def p2c(s):
    return s.replace('.', ',')

def c2p(s):
    return s.replace(',', '.')

def formam(x):
    if type(x) == int:
        s = ('%d' % x)
    else:
        s = p2c(('%.2f' % x))
    i = s.find(',')
    if i < 0:
        i = len(s)
    l = list(s)
    i -= 3
    while (i > 0) and (l[i-1] != '-'):
        l.insert(i, '.')
        i -= 3
    return ''.join(l)

def getint(s):
    if s:
        return int(s)
    else:
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
                return newXML(d.encode('latin-1')
                               .split('endstream')[0]
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
        data = PDFStream(dictionary=PDFDictionary(
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
        from .tests import DummyResponse
        c = Cache.objects.filter(url=args[0])
        if c:
            return DummyResponse(c[0].text)
        else:
            return DummyResponse(None, status=HTTPStatus.NOT_FOUND)
    else:
        if not 'timeout' in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.get(*args, **kwargs)

def post(*args, **kwargs):  # pragma: no cover
    if TEST:
        from .tests import DummyResponse
        kk = list(args[1].keys())
        kk.sort()
        a = []
        for k in kk:
            q = QueryDict(mutable=True)
            q[k] = args[1][k][:32]
            a.append(q.urlencode())
        url = args[0] + '?' + '&'.join(a)
        c = Cache.objects.filter(url=url)
        if c:
            return DummyResponse(c[0].text)
        else:
            return DummyResponse(None, status=HTTPStatus.NOT_FOUND)
    else:
        if not 'timeout' in kwargs:
            kwargs['timeout'] = TIMEOUT
        return requests.post(*args, **kwargs)

def send_mail(subject, text, recipients):
    try:
        mail.send_mail(
            subject,
            text,
            'Server ' + localsubdomain + ' <' + localemail + '>',
            recipients,
            fail_silently=True)
    except:  # pragma: no cover
        pass

class Pager:

    def __init__(self, start, total, url, p, batch):

        def link(n):
            p['start'] = n
            return url + '?' + p.urlencode()

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
        s = '%d ' % args[0]
    else:
        s = ''
    s += '%s %d/%d' % args[1:4]
    if len(args) == 5:
        s += '-%d' % args[4]
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
        s[1] = s[0] + ' ' + s[1]
        del s[0]
    register = s[0]
    t = s[1].split('/')
    if page:
        return senate, register, int(t[0]), int(t[1]), page
    else:
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
    else:
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
    return [icontains, istartswith, iendswith, iexact][opt](needle, haystack)

def lim(lower, x, upper):
    return min(max(lower, x), upper)

def between(lower, x, upper):
    return (x >= lower) and (x <= upper)

def normalize(s):
    return ' '.join(s.replace('\u00a0', ' ').strip().split())

def icmp(x, y):
    if x and y:
        return x.lower() == y.lower()
    else:
        return x == y
