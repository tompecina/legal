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
from os.path import join
from re import compile
from xml.sax.saxutils import escape, unescape

from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfName
import requests
import reportlab.rl_config
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfdoc import PDFName, PDFDictionary, PDFStream
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.lib.pagesizes import A4
from django.core import mail

from common.glob import (
    LIM, ODP, YDCONVS, MDCONVS, REGISTERS, LOCAL_SUBDOMAIN, LOCAL_EMAIL)
from common.settings import FONT_DIR, TEST
from common.models import Preset


class Logger:
    """
    Enhanced logging facility.
    """

    _logger = getLogger('logger')

    @staticmethod
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


def more(*args):
    """
    True of more than one argument evaluates to True.
    """

    res = 0
    for arg in args:
        if arg:
            res += 1
            if res > 1:
                return True
    return False


def fdt(dat):
    """
    Return standard project-wide formatted string represenation of date 'dt'.
    """

    return '{0.day:02d}.{0.month:02d}.{0.year:02d}'.format(dat)


def easter_sunday(year):
    """
    Return the date of the Easter Sunday in 'year'.
    """

    aux1 = year % 19
    aux2 = year >> 2
    aux3 = aux2 // 25 + 1
    aux4 = (aux3 * 3) >> 2
    aux5 = ((aux1 * 19) - ((aux3 * 8 + 5) // 25) + aux4 + 15) % 30
    aux5 += (29578 - aux1 - aux5 * 32) >> 10
    aux5 -= ((year % 7) + aux2 - aux4 + aux5 + 2) % 7
    aux4 = aux5 >> 5
    day = aux5 - aux4 * 31
    month = aux4 + 3

    return date(year, month, day)


def movable_holiday(dat):
    """
    Check if 'dat' is a local movable banking holiday.
    """

    holidays = (

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

    year = dat.year
    esun = easter_sunday(year)
    for hol in holidays:
        if dat == (esun + timedelta(hol['offset'])) \
            and between(hol['from'], year, hol['to']):
            return True
    return False


def holiday(dat):
    """
    Check if 'dat' is a local banking holiday.
    """

    holidays = (

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

    extra_holidays = {
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

    extra_non_holidays = {
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

    year = dat.year
    month = dat.month
    day = dat.day

    if year in extra_holidays and (month, day) in extra_holidays[year]:
        return True

    if year in extra_non_holidays and (month, day) in extra_non_holidays[year]:
        return False

    for hol in holidays:
        if day == hol['day'] and month == hol['month'] and \
           between(hol['from'], year, hol['to']):
            return True

    if movable_holiday(dat):
        return True

    return dat.weekday() > (5 if dat < date(1968, 10, 5) else 4)


def ply(dat, num):
    """
    Return 'dat' plus 'num' years.
    """

    year = dat.year + num
    month = dat.month
    day = min(dat.day, monthrange(year, month)[1])
    return date(year, month, day)


def plm(dat, num):
    """
    Return 'dat' plus 'num' months.
    """

    month = dat.month + num
    year = dat.year + ((month - 1) // 12)
    month = ((month - 1) % 12) + 1
    day = min(dat.day, monthrange(year, month)[1])
    return date(year, month, day)


def yfactor(beg, end, dconv):
    """
    Return number of years between 'beg' and 'end', using day-count convention
    'dconv'.
    """

    if end < beg or dconv not in YDCONVS:
        return None

    if dconv.startswith('ACT'):
        beg += ODP
        beg_year = beg.year
        beg_month = beg.month
        beg_day = beg.day
        end += ODP
        end_year = end.year
        end_month = end.month
        end_day = end.day
        if dconv == 'ACT/ACT':
            leap = nleap = 0
            while beg_year < end_year:
                num = (date((beg_year + 1), 1, 1) - \
                    date(beg_year, beg_month, beg_day)).days
                if isleap(beg_year):
                    leap += num
                else:
                    nleap += num
                beg_day = beg_month = 1
                beg_year += 1
            num = (date(end_year, end_month, end_day) - \
                date(beg_year, beg_month, beg_day)).days
            if isleap(beg_year):
                leap += num
            else:
                nleap += num
            return (nleap / 365) + (leap / 366)
        if dconv == 'ACT/365':
            return (end - beg).days / 365
        if dconv == 'ACT/360':
            return (end - beg).days / 360
        return (end - beg).days / 364

    else:
        beg_year = beg.year
        beg_month = beg.month
        beg_day = beg.day
        end_year = end.year
        end_month = end.month
        end_day = end.day
        if dconv == '30U/360':
            if end_day == 31 and beg_day >= 30:
                end_day = 30
            if beg_day == 31:
                beg_day = 30
        elif dconv == '30E/360':
            if beg_day == 31:
                beg_day = 30
            if end_day == 31:
                end_day = 30
        elif dconv == '30E/360 ISDA':
            if beg_day == monthrange(beg_year, beg_month)[1]:
                beg_day = 30
            if end_day == monthrange(end_year, end_month)[1]:
                end_day = 30
        elif dconv == '30E+/360':
            if beg_day == 31:
                beg_day = 30
            if end_day == 31:
                end_month += 1
                end_day = 1
        return (360 * (end_year - beg_year) + 30 * (end_month - beg_month) \
            + (end_day - beg_day)) / 360


def mfactor(beg, end, dconv):
    """
    Return number of months between 'beg' and 'end', using day-count convention
    'dconv'.
    """

    if end < beg or dconv not in MDCONVS:
        return None

    if dconv == 'ACT':
        beg += ODP
        year = beg.year
        month = beg.month
        day = beg.day
        res = .0
        while year < end.year or month != end.month:
            if day == 1:
                res += 1
            else:
                dim = monthrange(year, month)[1]
                res += float(dim - day + 1) / dim
            month += 1
            if month > 12:
                month = 1
                year += 1
            day = 1
        res += float(end.day - day + 1) / monthrange(year, month)[1]
        return res

    else:
        beg_year = beg.year
        beg_month = beg.month
        beg_day = beg.day
        end_year = end.year
        end_month = end.month
        end_day = end.day
        if dconv == '30U':
            if end_day == 31 and beg_day >= 30:
                end_day = 30
            if beg_day == 31:
                beg_day = 30
        elif dconv == '30E':
            if beg_day == 31:
                beg_day = 30
            if end_day == 31:
                end_day = 30
        elif dconv == '30E ISDA':
            if beg_day == monthrange(beg_year, beg_month)[1]:
                beg_day = 30
            if end_day == monthrange(end_year, end_month)[1]:
                end_day = 30
        elif dconv == '30E+':
            if beg_day == 31:
                beg_day = 30
            if end_day == 31:
                end_month += 1
                end_day = 1
        return (360 * (end_year - beg_year) + 30 * (end_month - beg_month) \
            + (end_day - beg_day)) / 30


def grammar(num, noun):
    """
    Return correct form of plural, 'num noun(s)'.
    """

    anum = abs(num)
    if anum == 1:
        suf = noun[0]
    elif not anum or anum > 4:
        suf = noun[2]
    else:
        suf = noun[1]
    return '{:d} {}'.format(num, suf)


def getbutton(request):
    """
    Get id of button pressed.
    """

    for key in request.POST:
        if key.startswith('submit_'):
            return key[7:]
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


def normfl(val):
    """
    Prevent the 'minus zero' effect.
    """

    return .0 if abs(val) < LIM else val


NEG_ZERO_REGEX = r'^-0\.0*$'


class LocalFloat(float):
    """
    Class for correct localized formatting of floats.
    """

    def __format__(self, fmt):
        string = super().__format__(fmt)
        if compile(NEG_ZERO_REGEX).match(string):
            string = string.replace('-', '', 1)
        return p2c(string)


def famt(amount):
    """
    Format 'amount' according to its type, adding thousands separators.
    """

    if isinstance(amount, int):
        string = '{:d}'.format(amount)
    else:
        string = '{:.2f}'.format(LocalFloat(amount))
    idx = string.find(',')
    if idx < 0:
        idx = len(string)
    lst = list(string)
    idx -= 3
    while idx > 0 and lst[idx - 1] != '-':
        lst.insert(idx, '.')
        idx -= 3
    return ''.join(lst)


def unrequire(form, fields):
    """
    Reset the required attribute for 'fields' in 'form'.
    """

    for fld in fields:
        form.fields[fld].required = False


def xml_decorate(tag, table):
    """
    Add all attributes in 'table' to XML tag 'tag'.
    """

    if tag.name in table:
        for key, val in table[tag.name].items():
            tag[key] = val
    return tag


def xml_espace(string):
    """
    XML-escape and strip 'string'.
    """

    return escape(string).strip()


def xml_unespace(string):
    """
    Strip and XML-unescape 'string'.
    """

    return unescape(string.strip())


def new_xml(data):
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


def get_xml(string):
    """
    Get XML soup from 'string'.
    """

    if string.startswith(b'<?xml'):
        try:
            return new_xml(string)
        except:  # pragma: no cover
            return None
    try:
        reader = PdfReader(fdata=string)
        root = reader['/Root']
        msg = root.get(PdfName('Data'))
        return new_xml(msg.stream.encode('latin-1'))
    # these are legacy branches; I don't believe such files actually exist
    except:  # pragma: no cover
        try:
            reader = PdfReader(fdata=string)
            root = reader['/Root']
            msg = root.get(PdfName('Metadata'))
            return new_xml(msg.stream.encode('latin-1'))
        except:
            try:
                return new_xml(
                    string.encode('latin-1').split('endstream')[0]
                    .split('stream')[1])
            except:
                try:
                    return new_xml(string.encode('latin-1'))
                except:
                    return None


def iso2date(tag):
    """
    Extract date from XML tag 'tag'.
    """

    if tag.has_attr('year') and tag.has_attr('month') and tag.has_attr('day'):
        return date(int(tag['year']), int(tag['month']), int(tag['day']))
    res = tag.text.strip().split('-')
    return date(*map(int, res[:3]))


def register_fonts():
    """
    Register fonts used for generation of PDF documents.
    """

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


def make_pdf(doc, flow, string=None, xml=None):
    """
    Finalize PDF document.
    """

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


    def first_page(canvas, doc):
        canvas.saveState()
        if string:
            canvas.setFont('Bookman', 7)
            canvas.drawString(64, 48, string)
        canvas.setFont('BookmanI', 7)
        canvas.drawRightString(
            A4[0] - 48,
            48,
            'Vytvořeno: {0.day:02d}.{0.month:02d}.{0.year:02d}'
            .format(today))
        canvas.restoreState()

    def later_page(canvas, doc):
        first_page(canvas, doc)
        canvas.saveState()
        canvas.setFont('Bookman', 8)
        canvas.drawCentredString(
            A4[0] / 2,
            A4[1] - 30,
            '– {:d} –'.format(doc.page))
        canvas.restoreState()

    today = date.today()
    if xml:
        CanvasXML.xml = xml
    doc.build(
        flow,
        onFirstPage=first_page,
        onLaterPages=later_page,
        canvasmaker=CanvasXML if xml else Canvas)


TIMEOUT = 1000


def get(*args, **kwargs):  # pragma: no cover
    """
    Test-compatible get.
    """

    if TEST:
        from test.utils import testreq
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
        from test.utils import testreq
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
            'Server {} <{}>'.format(LOCAL_SUBDOMAIN, LOCAL_EMAIL),
            recipients,
            fail_silently=True)
    except:  # pragma: no cover
        logger.warning('Failed to send mail')


class Pager:
    """
    General pager.
    """

    def __init__(self, start, total, url, par, batch):

        def link(num):
            par['start'] = num
            return '{}?{}'.format(url, par.urlencode())

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
        res = '{:d} '.format(args[0])
    else:
        res = ''
    res += '{} {:d}/{:d}'.format(*args[1:4])
    if len(args) == 5:
        res += '-{:d}'.format(args[4])
    return res


def decomposeref(ref):
    """
    Decompose reference into senate, register, number, year and (optional) page.
    """

    res = ref.split('-')
    if len(res) == 1:
        page = 0
    else:
        page = int(res[1])
    res = res[0].split()
    if res[0].isdigit():
        senate = int(res[0])
        del res[0]
    else:
        senate = 0
    while not res[1][0].isdigit():
        res[1] = ' '.join(res[:2])
        del res[0]
    register = res[0]
    num_year = res[1].split('/')
    if page:
        return senate, register, int(num_year[0]), int(num_year[1]), page
    return senate, register, int(num_year[0]), int(num_year[1])


def normreg(reg):
    """
    Normalize register 'reg'.
    """

    regl = reg.lower()
    for reg2 in REGISTERS:
        if reg2.lower() == regl:
            return reg2
    return regl.title()


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
    Replace hard-spaces, strip, split and join.
    """
    return ' '.join(string.replace('\u00a0', ' ').strip().split())


def icmp(string1, string2):
    """
    Case-insensitive comparison.
    """

    if string1 and string2:
        return string1.lower() == string2.lower()
    return string1 == string2


def getpreset(key):
    """
    Get current preset.
    """

    try:
        return Preset.objects.filter(name=key, valid__lte=date.today()) \
            .latest('valid').value
    except:
        return 0
