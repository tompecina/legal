# -*- coding: utf-8 -*-
#
# common/tests.py
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
from os.path import join
from decimal import Decimal
from copy import copy
from http import HTTPStatus
from re import compile
from hashlib import md5
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.http import QueryDict
from cache.tests import DummyRequest
from szr.cron import cron_update
from szr.models import Proceedings
from sir.models import Counter
from common.settings import BASE_DIR
from common import cron, glob, fields, forms, models, utils, views


TEST_STRING = 'Příliš žluťoučký kůň úpěnlivě přepíná ďábelské kódy'

xml_regex = compile(r'^(<[^<]+<\w+)[^>]*(.*)$')
pw_regex = compile(r'/accounts/resetpw/([0-9a-f]{32})/')


class DummyResponse:

    def __init__(self, content, status=HTTPStatus.OK):
        self.text = content
        if content:
            self.content = content.encode('utf-8')
        self.status_code = status
        self.ok = (status == HTTPStatus.OK)


def stripxml(s):

    try:
        s = s.decode('utf-8')
        m = xml_regex.match(s)
        return m.group(1) + m.group(2)
    except:
        return ''


testdata_prefix = join(BASE_DIR, 'common', 'testdata')


def testreq(post, *args):

    if post:
        r, d = args
        if isinstance(d, bytes):
            d = {'bytes': d.decode()}
    else:
        n = args[0]
        if '?' in n:
            r, q = n.split('?', 1)
        else:
            r = n
            q = ''
        d = QueryDict(q).dict()
    m = md5(r.encode())
    for k in sorted(d):
        m.update(k.encode())
        m.update(d[k].encode())
    fn = m.hexdigest() + '.dat'
    try:
        with open(join(testdata_prefix, fn), 'rb') as fi:
            return DummyResponse(fi.read().decode())
    except:
        return DummyResponse(None, status=HTTPStatus.NOT_FOUND)


def link_equal(a, b):

    a = a.split('?')
    b = b.split('?')
    if a[0] != b[0]:  # pragma: no cover
        return False
    a = a[1].split('&')
    b = b[1].split('&')
    return sorted(a) == sorted(b)


def setcounter(k, n):

    Counter.objects.update_or_create(id=k, defaults={'number': n})


def setdl(n):

    setcounter('DL', n)


def setpr(n):

    setcounter('PR', n)


def getcounter(k):

    return Counter.objects.get(id=k).number


def getdl():

    return getcounter('DL')


def getpr():

    return getcounter('PR')


class TestCron(TestCase):

    fixtures = ['common_test.json']

    def test_szr_notice(self):
        for dummy in range(Proceedings.objects.count()):
            cron_update()
        cron.cron_notify()
        m = mail.outbox
        self.assertEqual(len(m), 1)
        m = m[0]
        self.assertEqual(
            m.from_email,
            'Server {} <{}>'.format(glob.localsubdomain, glob.localemail))
        self.assertEqual(
            m.to,
            ['tomas@' + glob.localdomain])
        self.assertEqual(
            m.subject,
            'Zprava ze serveru ' + glob.localsubdomain)
        self.assertEqual(
            m.body,
            'V těchto soudních řízeních, která sledujete, došlo ke změně:\n\n'
            ' - Nejvyšší soud, sp. zn. 8 Tdo 819/2015\n'
            '   http://infosoud.justice.cz/InfoSoud/public/search.do?'
            'org=NSJIMBM&krajOrg=NSJIMBM&cisloSenatu=8&druhVec=TDO&'
            'bcVec=819&rocnik=2015&typSoudu=ns&autoFill=true&type=spzn\n\n'
            ' - Městský soud Praha, sp. zn. 41 T 3/2016 (Igor Ševcov)\n'
            '   http://infosoud.justice.cz/InfoSoud/public/search.do?'
            'org=MSPHAAB&krajOrg=MSPHAAB&cisloSenatu=41&druhVec=T'
            '&bcVec=3&rocnik=2016&typSoudu=os&autoFill=true&type=spzn\n\n'
            ' - Nejvyšší správní soud, sp. zn. 11 Kss 6/2015 '
            '(Miloš Zbránek)\n'
            '   http://www.nssoud.cz/mainc.aspx?cls=InfoSoud&'
            'kau_id=173442\n\n'
            ' - Městský soud Praha, sp. zn. 10 T 8/2014 (Opencard)\n'
            '   http://infosoud.justice.cz/InfoSoud/public/search.do?'
            'org=MSPHAAB&krajOrg=MSPHAAB&cisloSenatu=10&druhVec=T'
            '&bcVec=8&rocnik=2014&typSoudu=os&autoFill=true&type=spzn\n\n'
            ' - Obvodní soud Praha 2, sp. zn. 6 T 136/2013 (RWU)\n'
            '   http://infosoud.justice.cz/InfoSoud/public/search.do?'
            'org=OSPHA02&krajOrg=MSPHAAB&cisloSenatu=6&druhVec=T'
            '&bcVec=136&rocnik=2013&typSoudu=os&autoFill=true&type=spzn\n\n'
            'Server {} ({})\n'.format(glob.localsubdomain, glob.localurl))

    def test_run(self):
        cron.test_result = 0
        cron.run('test_func', '')
        self.assertEqual(cron.test_result, 6)
        cron.run('test_func', '1')
        self.assertEqual(cron.test_result, 2)
        cron.run('test_func', '5 2')
        self.assertEqual(cron.test_result, 3)

    def test_cron_run(self):
        cron.cron_clean()
        cron.SCHED = [
            {'name': 'test_func',
             'when': lambda t: True,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertFalse(cron.test_lock)
        self.assertFalse(cron.test_pending)
        cron.SCHED = [
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': False,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertEqual(len(cron.test_lock), 1)
        self.assertFalse(cron.test_pending)
        self.assertEqual(cron.test_lock[0].name, 'test')
        cron.SCHED = [
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertEqual(len(cron.test_lock), 1)
        self.assertFalse(cron.test_pending)
        self.assertEqual(cron.test_lock[0].name, 'test')
        models.Lock(name='test').save()
        cron.SCHED = [
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': False,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())
        cron.SCHED = [
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertEqual(models.Pending.objects.count(), 1)
        cron.SCHED = [
            {'name': 'test_func',
             'args': '1',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertEqual(models.Pending.objects.count(), 2)
        p = models.Pending.objects.latest('timestamp_add')
        self.assertEqual(p.name, 'test_func')
        self.assertEqual(p.args, '1')
        self.assertEqual(p.lock, 'test')
        cron.cron_unlock()
        cron.SCHED = []
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 2)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        models.Lock(name='another').save()
        cron.SCHED = [
            {'name': 'test_func',
             'args': '4',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            }]
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 8)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())
        models.Lock(name='test').save()
        models.Lock.objects.filter(name='test').update(
            timestamp_add=(datetime.now() - cron.EXPIRE - timedelta(days=1)))
        self.assertEqual(models.Lock.objects.count(), 2)
        cron.SCHED = []
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())

    def test_cron_unlock(self):
        models.Lock(name='test').save()
        self.assertTrue(models.Lock.objects.exists())
        cron.cron_unlock()
        self.assertFalse(models.Lock.objects.exists())

    def test_cron_clean(self):
        models.Lock(name='test').save()
        models.Pending(name='test', args='', lock='test').save()
        self.assertTrue(models.Lock.objects.exists())
        self.assertTrue(models.Pending.objects.exists())
        cron.cron_clean()
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())


class TestFields(SimpleTestCase):

    def test_prnum(self):
        self.assertEqual(fields.prnum('−11.216 530,5'), '-11216530.5')

    def test_DateField(self):
        f = fields.DateField()
        self.assertIsNone(f.to_python([]))
        self.assertEqual(f.to_python(datetime(2012, 4, 3, 15, 32)),
                         date(2012, 4, 3))
        self.assertEqual(f.to_python(date(2012, 4, 3)), date(2012, 4, 3))
        self.assertEqual(f.to_python('3.4.2012'), date(2012, 4, 3))
        self.assertEqual(f.to_python('03.04.2012'), date(2012, 4, 3))
        self.assertEqual(f.to_python('3. 4. 2012'), date(2012, 4, 3))
        self.assertEqual(f.to_python('03. 04. 2012'), date(2012, 4, 3))

    def test_AmountField(self):
        f = fields.AmountField()
        self.assertIsNone(f.prepare_value([]))
        f.rounding = 0
        self.assertEqual(f.prepare_value(115), '115')
        self.assertEqual(f.prepare_value(115.6), '116')
        self.assertEqual(f.prepare_value('115'), '115')
        self.assertIsNone(f.to_python([]))
        self.assertEqual(f.to_python('−11.216 530,7'), -11216531)
        with self.assertRaises(forms.ValidationError):
            f.to_python('x')
        f.rounding = 2
        self.assertEqual(f.prepare_value(115), '115,00')
        self.assertEqual(f.prepare_value(115.6), '115,60')
        self.assertAlmostEqual(f.to_python('−11.216 530,7'), -11216530.7)

    def test_DecimalField(self):
        f = fields.DecimalField()
        self.assertIsNone(f.to_python([]))
        self.assertAlmostEqual(f.to_python('−11.216 530,7'),
                               Decimal(-11216530.7))
        self.assertIsInstance(f.to_python('−11.216 530,7'), Decimal)
        self.assertAlmostEqual(f.to_python(-11216530.7), Decimal(-11216530.7))
        self.assertIsInstance(f.to_python(-11216530.7), Decimal)
        with self.assertRaises(forms.ValidationError):
            f.to_python('x')

    def test_FloatField(self):
        f = fields.FloatField()
        self.assertIsNone(f.to_python([]))
        self.assertAlmostEqual(f.to_python('−11.216 530,7'), -11216530.7)
        self.assertAlmostEqual(f.to_python(-11216530.7), -11216530.7)
        with self.assertRaises(forms.ValidationError):
            f.to_python('x')

    def test_IntegerField(self):
        f = fields.IntegerField()
        self.assertIsNone(f.to_python([]))
        self.assertEqual(f.to_python('−11.216 530,7'), -11216530)
        self.assertEqual(f.to_python(-11216530.7), -11216530)
        with self.assertRaises(forms.ValidationError):
            f.to_python('x')

    def test_CurrencyField(self):
        f = fields.CurrencyField()
        self.assertIsNone(f.compress([]))
        self.assertEqual(f.compress(['EUR', 'xxx']), 'EUR')
        self.assertEqual(f.compress(['OTH', 'xxx']), 'XXX')
        with self.assertRaises(forms.ValidationError):
            f.validate([])


class TestForms(TestCase):

    def test_UserAddForm(self):
        User.objects.create_user(
            'existing',
            'existing@' + glob.localdomain, 'none')
        s = {'first_name': 'New',
             'last_name': 'User',
             'username': 'new',
             'password1': 'nopassword',
             'password2': 'nopassword',
             'captcha': 'Praha'}
        self.assertTrue(forms.UserAddForm(s).is_valid())
        d = copy(s)
        del d['password1']
        del d['password2']
        self.assertFalse(forms.UserAddForm(d).is_valid())
        d = copy(s)
        d['password2'] = 'different'
        self.assertFalse(forms.UserAddForm(d).is_valid())
        d = copy(s)
        d['captcha'] = 'praha'
        self.assertTrue(forms.UserAddForm(d).is_valid())
        d = copy(s)
        d['captcha'] = 'Brno'
        self.assertFalse(forms.UserAddForm(d).is_valid())
        d = copy(s)
        d['username'] = 'existing'
        self.assertFalse(forms.UserAddForm(d).is_valid())


class TestGlob(SimpleTestCase):

    def test_register_regex(self):
        rr = compile(glob.register_regex)
        for p in glob.registers:
            self.assertIsNotNone(rr.match(p), msg=p)
        for p in ['X', '']:
            self.assertIsNone(rr.match(p), msg=p)


class TestModels(TestCase):

    def test_models(self):
        User.objects.create_user('user', 'user@' + glob.localdomain, 'none')
        uid = User.objects.all()[0].id
        p = models.PwResetLink(
            user_id=uid,
            link=('0' * 32))
        self.assertEqual(str(p), ('0' * 32))
        p = models.Preset(
            name='Test',
            value=15,
            valid=date(2016, 5, 18))
        self.assertEqual(str(p), 'Test, 2016-05-18')


def proc_link(l):
    if not l:
        return -1
    return int(l.split('=')[-1])


class TestUtils1(SimpleTestCase):

    def test_easter(self):
        es = [
            date(1900, 4, 15), date(1901, 4, 7), date(1902, 3, 30),
            date(1903, 4, 12), date(1904, 4, 3), date(1905, 4, 23),
            date(1906, 4, 15), date(1907, 3, 31), date(1908, 4, 19),
            date(1909, 4, 11), date(1910, 3, 27), date(1911, 4, 16),
            date(1912, 4, 7), date(1913, 3, 23), date(1914, 4, 12),
            date(1915, 4, 4), date(1916, 4, 23), date(1917, 4, 8),
            date(1918, 3, 31), date(1919, 4, 20), date(1920, 4, 4),
            date(1921, 3, 27), date(1922, 4, 16), date(1923, 4, 1),
            date(1924, 4, 20), date(1925, 4, 12), date(1926, 4, 4),
            date(1927, 4, 17), date(1928, 4, 8), date(1929, 3, 31),
            date(1930, 4, 20), date(1931, 4, 5), date(1932, 3, 27),
            date(1933, 4, 16), date(1934, 4, 1), date(1935, 4, 21),
            date(1936, 4, 12), date(1937, 3, 28), date(1938, 4, 17),
            date(1939, 4, 9), date(1940, 3, 24), date(1941, 4, 13),
            date(1942, 4, 5), date(1943, 4, 25), date(1944, 4, 9),
            date(1945, 4, 1), date(1946, 4, 21), date(1947, 4, 6),
            date(1948, 3, 28), date(1949, 4, 17), date(1950, 4, 9),
            date(1951, 3, 25), date(1952, 4, 13), date(1953, 4, 5),
            date(1954, 4, 18), date(1955, 4, 10), date(1956, 4, 1),
            date(1957, 4, 21), date(1958, 4, 6), date(1959, 3, 29),
            date(1960, 4, 17), date(1961, 4, 2), date(1962, 4, 22),
            date(1963, 4, 14), date(1964, 3, 29), date(1965, 4, 18),
            date(1966, 4, 10), date(1967, 3, 26), date(1968, 4, 14),
            date(1969, 4, 6), date(1970, 3, 29), date(1971, 4, 11),
            date(1972, 4, 2), date(1973, 4, 22), date(1974, 4, 14),
            date(1975, 3, 30), date(1976, 4, 18), date(1977, 4, 10),
            date(1978, 3, 26), date(1979, 4, 15), date(1980, 4, 6),
            date(1981, 4, 19), date(1982, 4, 11), date(1983, 4, 3),
            date(1984, 4, 22), date(1985, 4, 7), date(1986, 3, 30),
            date(1987, 4, 19), date(1988, 4, 3), date(1989, 3, 26),
            date(1990, 4, 15), date(1991, 3, 31), date(1992, 4, 19),
            date(1993, 4, 11), date(1994, 4, 3), date(1995, 4, 16),
            date(1996, 4, 7), date(1997, 3, 30), date(1998, 4, 12),
            date(1999, 4, 4), date(2000, 4, 23), date(2001, 4, 15),
            date(2002, 3, 31), date(2003, 4, 20), date(2004, 4, 11),
            date(2005, 3, 27), date(2006, 4, 16), date(2007, 4, 8),
            date(2008, 3, 23), date(2009, 4, 12), date(2010, 4, 4),
            date(2011, 4, 24), date(2012, 4, 8), date(2013, 3, 31),
            date(2014, 4, 20), date(2015, 4, 5), date(2016, 3, 27),
            date(2017, 4, 16), date(2018, 4, 1), date(2019, 4, 21),
            date(2020, 4, 12), date(2021, 4, 4), date(2022, 4, 17),
            date(2023, 4, 9), date(2024, 3, 31), date(2025, 4, 20),
            date(2026, 4, 5), date(2027, 3, 28), date(2028, 4, 16),
            date(2029, 4, 1), date(2030, 4, 21), date(2031, 4, 13),
            date(2032, 3, 28), date(2033, 4, 17), date(2034, 4, 9),
            date(2035, 3, 25), date(2036, 4, 13), date(2037, 4, 5),
            date(2038, 4, 25), date(2039, 4, 10), date(2040, 4, 1),
            date(2041, 4, 21), date(2042, 4, 6), date(2043, 3, 29),
            date(2044, 4, 17), date(2045, 4, 9), date(2046, 3, 25),
            date(2047, 4, 14), date(2048, 4, 5), date(2049, 4, 18),
            date(2050, 4, 10), date(2051, 4, 2), date(2052, 4, 21),
            date(2053, 4, 6), date(2054, 3, 29), date(2055, 4, 18),
            date(2056, 4, 2), date(2057, 4, 22), date(2058, 4, 14),
            date(2059, 3, 30), date(2060, 4, 18), date(2061, 4, 10),
            date(2062, 3, 26), date(2063, 4, 15), date(2064, 4, 6),
            date(2065, 3, 29), date(2066, 4, 11), date(2067, 4, 3),
            date(2068, 4, 22), date(2069, 4, 14), date(2070, 3, 30),
            date(2071, 4, 19), date(2072, 4, 10), date(2073, 3, 26),
            date(2074, 4, 15), date(2075, 4, 7), date(2076, 4, 19),
            date(2077, 4, 11), date(2078, 4, 3), date(2079, 4, 23),
            date(2080, 4, 7), date(2081, 3, 30), date(2082, 4, 19),
            date(2083, 4, 4), date(2084, 3, 26), date(2085, 4, 15),
            date(2086, 3, 31), date(2087, 4, 20), date(2088, 4, 11),
            date(2089, 4, 3), date(2090, 4, 16), date(2091, 4, 8),
            date(2092, 3, 30), date(2093, 4, 12), date(2094, 4, 4),
            date(2095, 4, 24), date(2096, 4, 15), date(2097, 3, 31),
            date(2098, 4, 20), date(2099, 4, 12),
        ]
        for s in es:
            self.assertFalse(utils.easter(s))
            self.assertTrue(utils.easter(s + timedelta(1)))
            if s.year >= 2016:
                self.assertTrue(utils.easter(s - timedelta(2)))

    def test_tod(self):
        self.assertTrue(utils.tod(date(2016, 1, 1)))
        self.assertFalse(utils.tod(date(2016, 1, 5)))
        self.assertTrue(utils.tod(date(2016, 1, 16)))
        self.assertTrue(utils.tod(date(2016, 2, 7)))
        self.assertFalse(utils.tod(date(2016, 2, 29)))
        self.assertFalse(utils.tod(date(2016, 3, 8)))
        self.assertTrue(utils.tod(date(2016, 3, 20)))
        self.assertTrue(utils.tod(date(2016, 3, 25)))
        self.assertTrue(utils.tod(date(2016, 3, 28)))
        self.assertFalse(utils.tod(date(2016, 4, 18)))
        self.assertFalse(utils.tod(date(2016, 5, 19)))
        self.assertFalse(utils.tod(date(2016, 6, 3)))
        self.assertFalse(utils.tod(date(1991, 5, 8)))
        self.assertTrue(utils.tod(date(1991, 5, 9)))
        self.assertTrue(utils.tod(date(1992, 5, 8)))
        self.assertTrue(utils.tod(date(1992, 5, 9)))
            # not testable as 1992-05-09 was Saturday

        CAL = {
            1951: (
                (1, 7, 14, 21, 28),
                (4, 11, 18, 25),
                (4, 11, 18, 25, 26),
                (1, 8, 15, 22, 29),
                (1, 6, 9, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 5, 6, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 25, 26, 30),
            ),
            1952: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (2, 9, 16, 23, 30),
                (6, 13, 14, 20, 27),
                (1, 4, 9, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26, 28),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 25, 26, 28),
            ),
            1953: (
                (1, 4, 11, 18, 25),
                (1, 8, 15, 22),
                (1, 8, 15, 22, 29),
                (5, 6, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1954: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (7, 14, 21, 28),
                (4, 11, 18, 19, 25),
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 28, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 25, 26),
            ),
            1955: (
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (6, 13, 20, 27),
                (3, 10, 11, 17, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 28, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 26),
            ),
            1956: (
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (4, 11, 18, 25),
                (1, 2, 8, 15, 22, 29),
                (1, 6, 9, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 25, 26, 30),
            ),
            1957: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 22, 28),
                (1, 5, 9, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27, 28),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 25, 26, 29),
            ),
            1958: (
                (1, 5, 12, 19, 26),
                (2, 9, 16, 23),
                (2, 9, 16, 23, 30),
                (6, 7, 13, 20, 27),
                (1, 4, 9, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26, 28),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 25, 26, 28),
            ),
            1959: (
                (1, 4, 11, 18, 25),
                (1, 8, 15, 22),
                (1, 8, 15, 22, 29, 30),
                (5, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1960: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (6, 13, 20, 27),
                (3, 10, 17, 18, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 28, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 26),
            ),
            1961: (
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (5, 12, 19, 26),
                (2, 3, 9, 16, 23, 30),
                (1, 7, 9, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 28, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 25, 26, 31),
            ),
            1962: (
                (1, 7, 14, 21, 28),
                (4, 11, 18, 25),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 23, 29),
                (1, 6, 9, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 25, 26, 30),
            ),
            1963: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (3, 10, 17, 24, 31),
                (7, 14, 15, 21, 28),
                (1, 5, 9, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27, 28),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 25, 26, 29),
            ),
            1964: (
                (1, 5, 12, 19, 26),
                (2, 9, 16, 23),
                (1, 8, 15, 22, 29, 30),
                (5, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1965: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (7, 14, 21, 28),
                (4, 11, 18, 19, 25),
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 28, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 25, 26),
            ),
            1966: (
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (6, 13, 20, 27),
                (3, 10, 11, 17, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (6, 7, 14, 21, 28),
                (3, 4, 11, 18, 25),
                (1, 2, 9, 16, 23, 28, 29, 30),
                (6, 13, 20, 26, 27),
                (4, 11, 18, 24, 25, 26),
            ),
            1967: (
                (1, 7, 8, 15, 21, 22, 29),
                (4, 5, 12, 18, 19, 26),
                (4, 5, 12, 18, 19, 26, 27),
                (1, 2, 9, 15, 16, 23, 29, 30),
                (1, 7, 9, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (2, 8, 9, 16, 22, 23, 30),
                (5, 6, 13, 19, 20, 27),
                (2, 3, 10, 16, 17, 24, 30),
                (1, 8, 14, 15, 22, 28, 29),
                (5, 11, 12, 19, 25, 26),
                (3, 9, 10, 17, 23, 24, 25, 26, 31),
            ),
            1968: (
                (1, 7, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (3, 9, 10, 17, 23, 24, 31),
                (6, 7, 14, 15, 20, 21, 28),
                (1, 4, 5, 9, 12, 18, 19, 26),
                (1, 2, 9, 15, 16, 23, 29, 30),
                (7, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (1, 7, 8, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 23, 24, 25, 26, 30, 31),
            ),
            1969: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 26, 27, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 31),
            ),
            1970: (
                (1, 2, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29, 30),
                (5, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 9, 10, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 30, 31),
                (1, 7, 8, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26),
            ),
            1971: (
                (1, 2, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 29, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1972: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1973: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 15, 21, 22, 23, 28, 29),
                (1, 5, 6, 9, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1974: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (7, 13, 14, 15, 20, 21, 27, 28),
                (1, 4, 5, 9, 10, 11, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 24, 25, 26, 30, 31),
            ),
            1975: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 23, 29, 30, 31),
                (6, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26),
            ),
            1976: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 19, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1977: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 11, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1978: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 12, 18, 19, 25, 26, 27),
                (2, 8, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 24, 30),
                (1, 7, 8, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1979: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 7, 8, 14, 15, 16, 22, 29, 30),
                (1, 7, 8, 9, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1980: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (5, 6, 7, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 21, 27, 28),
                (4, 5, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 25, 26, 27, 28),
            ),
            1981: (
                (1, 2, 3, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 26),
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 25, 26, 27),
            ),
            1982: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1983: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 25),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1984: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 7, 8, 14, 15, 21, 22, 23, 29, 30),
                (1, 5, 6, 9, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1985: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 24, 30, 31),
                (6, 7, 8, 14, 20, 21, 27, 28),
                (1, 2, 3, 9, 10, 11, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 20, 26, 27),
                (2, 3, 9, 10, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 22, 24, 25, 26, 30, 31),
            ),
            1986: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 16, 22, 23, 29, 30, 31),
                (6, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 31),
            ),
            1987: (
                (1, 2, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 26),
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 13, 19, 20, 24, 25, 26, 31),
            ),
            1988: (
                (1, 2, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1989: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 12, 18, 19, 25, 26, 27),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1990: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 16, 21, 22, 29, 30),
                (1, 5, 6, 9, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            1991: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 9, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            1992: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            1993: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            1994: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1995: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1996: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 8, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            1997: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30, 31),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            1998: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 13, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            1999: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 5, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2000: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 17, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            2001: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 16, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2002: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            2003: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 21, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2004: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 17, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2005: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            2006: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 17, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            2007: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2008: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2009: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 13, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 17, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            2010: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 5, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 17, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2011: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            2012: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2013: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            2014: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 21, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2015: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 17, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            2016: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (5, 6, 12, 13, 19, 20, 25, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
        }
        for y in range(1951, 2017):
            for m in range(1, 13):
                for d in range(1, (monthrange(y, m)[1] + 1)):
                    dt = date(y, m, d)
                    self.assertEqual(utils.tod(dt), (d in CAL[y][m - 1]))

    def test_ply(self):
        self.assertEqual(utils.ply(date(2016, 7, 5), 1), date(2017, 7, 5))
        self.assertEqual(utils.ply(date(2016, 2, 29), 1), date(2017, 2, 28))

    def test_plm(self):
        self.assertEqual(utils.plm(date(2016, 7, 5), 1), date(2016, 8, 5))
        self.assertEqual(utils.plm(date(2015, 1, 31), 1), date(2015, 2, 28))
        self.assertEqual(utils.plm(date(2016, 1, 31), 1), date(2016, 2, 29))

    def test_yfactor(self):
        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2011, 7, 11),
                'ACT/ACT'))
        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/ACT'),
            4.9821618384609625)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/365'),
            1820/365)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/360'),
            1820/360)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/364'),
            1820/364)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30U/360'),
            1793/360)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 30),
                date(2016, 7, 31),
                '30U/360'),
            5)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E/360'),
            1793/360)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E/360 ISDA'),
            1793/360)
        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E+/360'),
            1793/360)
        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/XXX'))
        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

    def test_mfactor(self):
        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2011, 7, 11),
                'ACT'))
        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT'),
            59.774193548387096)
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30U'),
            1793/30)
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 30),
                date(2016, 7, 31),
                '30U'),
            60)
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E'),
            1793/30)
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E ISDA'),
            1793/30)
        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E+'),
            1793/30)
        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

    def test_grammar(self):
        t = ['koruna', 'koruny', 'korun']
        self.assertEqual(utils.grammar(-5, t), '-5 korun')
        self.assertEqual(utils.grammar(-4, t), '-4 koruny')
        self.assertEqual(utils.grammar(-2, t), '-2 koruny')
        self.assertEqual(utils.grammar(-1, t), '-1 koruna')
        self.assertEqual(utils.grammar(0, t), '0 korun')
        self.assertEqual(utils.grammar(1, t), '1 koruna')
        self.assertEqual(utils.grammar(2, t), '2 koruny')
        self.assertEqual(utils.grammar(4, t), '4 koruny')
        self.assertEqual(utils.grammar(5, t), '5 korun')

    def test_formam(self):
        self.assertEqual(utils.formam(0), '0')
        self.assertEqual(utils.formam(1), '1')
        self.assertEqual(utils.formam(-1), '-1')
        self.assertEqual(utils.formam(1.4), '1,40')
        self.assertEqual(utils.formam(-1.4), '-1,40')
        self.assertEqual(utils.formam(1.489), '1,49')
        self.assertEqual(utils.formam(-1.489), '-1,49')
        self.assertEqual(utils.formam(537), '537')
        self.assertEqual(utils.formam(-537), '-537')
        self.assertEqual(utils.formam(1537), '1.537')
        self.assertEqual(utils.formam(-1537), '-1.537')
        self.assertEqual(utils.formam(68562515458), '68.562.515.458')
        self.assertEqual(utils.formam(-68562515458), '-68.562.515.458')
        self.assertEqual(utils.formam(68562515458.216), '68.562.515.458,22')
        self.assertEqual(utils.formam(-68562515458.216), '-68.562.515.458,22')
        self.assertEqual(utils.formam(968562515458.216), '968.562.515.458,22')
        self.assertEqual(utils.formam(-968562515458.216), '-968.562.515.458,22')

    def test_getint(self):
        self.assertEqual(utils.getint(None), 0)
        self.assertEqual(utils.getint(''), 0)
        self.assertEqual(utils.getint('1'), 1)
        with self.assertRaises(ValueError):
            utils.getint('2.6')

    def test_rmdsl(self):
        self.assertEqual(utils.rmdsl([]), [])
        self.assertEqual(utils.rmdsl([1]), [1])
        self.assertEqual(utils.rmdsl([1, 2]), [1, 2])
        self.assertEqual(utils.rmdsl([1, 2, 2]), [1, 2])
        self.assertEqual(utils.rmdsl([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(utils.rmdsl([1, 2, 2, 3, 4, 4, 4]), [1, 2, 3, 4])

    def test_getxml(self):
        self.assertIsNone(utils.getXML(b'test'))

    def test_iso2date(self):
        soup = utils.newXML(None)
        t = soup.new_tag('date')
        t['year'] = 2014
        t['month'] = 11
        t['day'] = 14
        self.assertEqual(utils.iso2date(t), date(2014, 11, 14))
        soup = utils.newXML(None)
        t = soup.new_tag('date')
        t.string = '2014-11-14'
        self.assertEqual(utils.iso2date(t), date(2014, 11, 14))

    def test_pager(self):
        pp = [
            [0, 1, [1, 1, -1, -1, -1, -1]],
            [0, 50, [1, 1, -1, -1, -1, -1]],
            [0, 51, [1, 2, -1, -1, 50, 50]],
            [0, 100, [1, 2, -1, -1, 50, 50]],
            [0, 101, [1, 3, -1, -1, 50, 100]],
            [0, 53697, [1, 1074, -1, -1, 50, 53650]],
            [50, 51, [2, 2, 0, 0, -1, -1]],
            [50, 100, [2, 2, 0, 0, -1, -1]],
            [50, 101, [2, 3, 0, 0, 100, 100]],
            [50, 53697, [2, 1074, 0, 0, 100, 53650]],
            [100, 53697, [3, 1074, 0, 50, 150, 53650]],
            [53600, 53697, [1073, 1074, 0, 53550, 53650, 53650]],
            [53650, 53697, [1074, 1074, 0, 53600, -1, -1]],
        ]
        i = 0
        for p in pp:
            pag = utils.Pager(p[0], p[1], 'url', QueryDict(mutable=True), 50)
            r = [pag.curr,
                 pag.total,
                 proc_link(pag.linkbb),
                 proc_link(pag.linkb),
                 proc_link(pag.linkf),
                 proc_link(pag.linkff),
                ]
            self.assertEqual(r, p[2], msg=str(i))
            i += 1

    def test_ref(self):
        pp = ['3 As 12/2015-8',
              '12 Azs 4/2009-118',
              'Konf 1/2011-221',
              '3 As 12/2015',
              '12 Azs 4/2009',
              'Konf 1/2011',
             ]
        for p in pp:
            self.assertEqual(utils.composeref(*utils.decomposeref(p)), p)
            self.assertEqual(utils.composeref(*utils.decomposeref(
                p.replace('-', ' - '))), p)

    def test_normreg(self):
        registers = [[
            'T', 'C', 'P A NC', 'D', 'E', 'P', 'NC', 'ERO', 'RO', 'EC',
            'EVC', 'EXE', 'EPR', 'PP', 'CM', 'SM', 'CA', 'CAD', 'AZ', 'TO',
            'NT', 'CO', 'NTD', 'CMO', 'KO', 'NCO', 'NCD', 'NCP', 'ECM',
            'ICM', 'INS', 'K', 'KV', 'EVCM', 'A', 'AD', 'AF', 'NA', 'UL',
            'CDO', 'ODO', 'TDO', 'TZ', 'NCU', 'ADS', 'AFS', 'ANS', 'AO',
            'AOS', 'APRK', 'APRN', 'APS', 'ARS', 'AS', 'ASZ', 'AZS', 'KOMP',
            'KONF', 'KSE', 'KSEO', 'KSS', 'KSZ', 'NA', 'NAD', 'NAO', 'NCN',
            'NK', 'NTN', 'OBN', 'PLEN', 'PLSN', 'PST', 'ROZK', 'RS', 'S',
            'SPR', 'SST', 'VOL', 'ABC', 'abc'
        ], [
            'T', 'C', 'P a Nc', 'D', 'E', 'P', 'Nc', 'ERo', 'Ro', 'EC',
            'EVC', 'EXE', 'EPR', 'PP', 'Cm', 'Sm', 'Ca', 'Cad', 'Az', 'To',
            'Nt', 'Co', 'Ntd', 'Cmo', 'Ko', 'Nco', 'Ncd', 'Ncp', 'ECm',
            'ICm', 'INS', 'K', 'Kv', 'EVCm', 'A', 'Ad', 'Af', 'Na', 'UL',
            'Cdo', 'Odo', 'Tdo', 'Tz', 'Ncu', 'Ads', 'Afs', 'Ans', 'Ao',
            'Aos', 'Aprk', 'Aprn', 'Aps', 'Ars', 'As', 'Asz', 'Azs', 'Komp',
            'Konf', 'Kse', 'Kseo', 'Kss', 'Ksz', 'Na', 'Nad', 'Nao', 'Ncn',
            'Nk', 'Ntn', 'Obn', 'Plen', 'Plsn', 'Pst', 'Rozk', 'Rs', 'S',
            'Spr', 'Sst', 'Vol', 'Abc', 'Abc'
        ]]
        for x, y in zip(registers[0], registers[1]):
            self.assertEqual(utils.normreg(x), y)

    def test_xmlbool(self):
        self.assertEqual(utils.xmlbool(False), 'false')
        self.assertEqual(utils.xmlbool(True), 'true')

    def test_icontains(self):
        self.assertTrue(utils.icontains('yz', 'xyzw'))
        self.assertFalse(utils.icontains('q', 'xyzw'))
        self.assertTrue(utils.icontains('YZ', 'xyzw'))
        self.assertTrue(utils.icontains('yz', 'XYZW'))
        self.assertTrue(utils.icontains('YZ', 'xyzw'))
        self.assertTrue(utils.icontains('čď', 'áčďě'))
        self.assertFalse(utils.icontains('é', 'áčďě'))
        self.assertTrue(utils.icontains('ČĎ', 'áčďě'))
        self.assertTrue(utils.icontains('čď', 'ÁČĎĚ'))
        self.assertTrue(utils.icontains('ČĎ', 'áčďě'))
        self.assertFalse(utils.icontains('yz', ''))
        self.assertTrue(utils.icontains('', 'xyzw'))
        self.assertTrue(utils.icontains('', ''))

    def test_istartswith(self):
        self.assertTrue(utils.istartswith('xy', 'xyzw'))
        self.assertFalse(utils.istartswith('y', 'xyzw'))
        self.assertFalse(utils.istartswith('q', 'xyzw'))
        self.assertTrue(utils.istartswith('XY', 'xyzw'))
        self.assertTrue(utils.istartswith('xy', 'XYZW'))
        self.assertTrue(utils.istartswith('XY', 'xyzw'))
        self.assertTrue(utils.istartswith('áč', 'áčďě'))
        self.assertFalse(utils.istartswith('č', 'áčďě'))
        self.assertFalse(utils.istartswith('ě', 'áčďě'))
        self.assertTrue(utils.istartswith('ÁČ', 'áčďě'))
        self.assertTrue(utils.istartswith('áč', 'ÁČĎĚ'))
        self.assertTrue(utils.istartswith('ÁČ', 'áčďě'))
        self.assertFalse(utils.istartswith('y', ''))
        self.assertTrue(utils.istartswith('', 'xyzw'))
        self.assertTrue(utils.istartswith('', ''))

    def test_iendswith(self):
        self.assertTrue(utils.iendswith('zw', 'xyzw'))
        self.assertFalse(utils.iendswith('y', 'xyzw'))
        self.assertFalse(utils.iendswith('q', 'xyzw'))
        self.assertTrue(utils.iendswith('ZW', 'xyzw'))
        self.assertTrue(utils.iendswith('zw', 'XYZW'))
        self.assertTrue(utils.iendswith('ZW', 'xyzw'))
        self.assertTrue(utils.iendswith('ďě', 'áčďě'))
        self.assertFalse(utils.iendswith('č', 'áčďě'))
        self.assertFalse(utils.iendswith('á', 'áčďě'))
        self.assertTrue(utils.iendswith('ĎĚ', 'áčďě'))
        self.assertTrue(utils.iendswith('ďě', 'ÁČĎĚ'))
        self.assertTrue(utils.iendswith('ĎĚ', 'áčďě'))
        self.assertFalse(utils.iendswith('y', ''))
        self.assertTrue(utils.iendswith('', 'xyzw'))
        self.assertTrue(utils.iendswith('', ''))

    def test_iexact(self):
        self.assertTrue(utils.iexact('xyzw', 'xyzw'))
        self.assertFalse(utils.iexact('y', 'xyzw'))
        self.assertFalse(utils.iexact('q', 'xyzw'))
        self.assertTrue(utils.iexact('XYZW', 'xyzw'))
        self.assertTrue(utils.iexact('xyzw', 'XYZW'))
        self.assertTrue(utils.iexact('XYZW', 'xyzw'))
        self.assertTrue(utils.iexact('áčďě', 'áčďě'))
        self.assertFalse(utils.iexact('č', 'áčďě'))
        self.assertFalse(utils.iexact('ě', 'áčďě'))
        self.assertTrue(utils.iexact('ÁČĎĚ', 'áčďě'))
        self.assertTrue(utils.iexact('áčďě', 'ÁČĎĚ'))
        self.assertTrue(utils.iexact('ÁČĎĚ', 'áčďě'))
        self.assertFalse(utils.iexact('y', ''))
        self.assertFalse(utils.iexact('', 'xyzw'))
        self.assertTrue(utils.iexact('', ''))

    def test_text_opt(self):
        self.assertTrue(utils.text_opt('yz', 'xyzw', 0))
        self.assertFalse(utils.text_opt('q', 'xyzw', 0))
        self.assertTrue(utils.text_opt('YZ', 'xyzw', 0))
        self.assertTrue(utils.text_opt('yz', 'XYZW', 0))
        self.assertTrue(utils.text_opt('YZ', 'xyzw', 0))
        self.assertTrue(utils.text_opt('čď', 'áčďě', 0))
        self.assertFalse(utils.text_opt('é', 'áčďě', 0))
        self.assertTrue(utils.text_opt('ČĎ', 'áčďě', 0))
        self.assertTrue(utils.text_opt('čď', 'ÁČĎĚ', 0))
        self.assertTrue(utils.text_opt('ČĎ', 'áčďě', 0))
        self.assertFalse(utils.text_opt('yz', '', 0))
        self.assertTrue(utils.text_opt('', 'xyzw', 0))
        self.assertTrue(utils.text_opt('', '', 0))
        self.assertTrue(utils.text_opt('xy', 'xyzw', 1))
        self.assertFalse(utils.text_opt('y', 'xyzw', 1))
        self.assertFalse(utils.text_opt('q', 'xyzw', 1))
        self.assertTrue(utils.text_opt('XY', 'xyzw', 1))
        self.assertTrue(utils.text_opt('xy', 'XYZW', 1))
        self.assertTrue(utils.text_opt('XY', 'xyzw', 1))
        self.assertTrue(utils.text_opt('áč', 'áčďě', 1))
        self.assertFalse(utils.text_opt('č', 'áčďě', 1))
        self.assertFalse(utils.text_opt('ě', 'áčďě', 1))
        self.assertTrue(utils.text_opt('ÁČ', 'áčďě', 1))
        self.assertTrue(utils.text_opt('áč', 'ÁČĎĚ', 1))
        self.assertTrue(utils.text_opt('ÁČ', 'áčďě', 1))
        self.assertFalse(utils.text_opt('y', '', 1))
        self.assertTrue(utils.text_opt('', 'xyzw', 1))
        self.assertTrue(utils.text_opt('', '', 1))
        self.assertTrue(utils.text_opt('zw', 'xyzw', 2))
        self.assertFalse(utils.text_opt('y', 'xyzw', 2))
        self.assertFalse(utils.text_opt('q', 'xyzw', 2))
        self.assertTrue(utils.text_opt('ZW', 'xyzw', 2))
        self.assertTrue(utils.text_opt('zw', 'XYZW', 2))
        self.assertTrue(utils.text_opt('ZW', 'xyzw', 2))
        self.assertTrue(utils.text_opt('ďě', 'áčďě', 2))
        self.assertFalse(utils.text_opt('č', 'áčďě', 2))
        self.assertFalse(utils.text_opt('á', 'áčďě', 2))
        self.assertTrue(utils.text_opt('ĎĚ', 'áčďě', 2))
        self.assertTrue(utils.text_opt('ďě', 'ÁČĎĚ', 2))
        self.assertTrue(utils.text_opt('ĎĚ', 'áčďě', 2))
        self.assertFalse(utils.text_opt('y', '', 2))
        self.assertTrue(utils.text_opt('', 'xyzw', 2))
        self.assertTrue(utils.text_opt('', '', 2))
        self.assertTrue(utils.text_opt('xyzw', 'xyzw', 3))
        self.assertFalse(utils.text_opt('y', 'xyzw', 3))
        self.assertFalse(utils.text_opt('q', 'xyzw', 3))
        self.assertTrue(utils.text_opt('XYZW', 'xyzw', 3))
        self.assertTrue(utils.text_opt('xyzw', 'XYZW', 3))
        self.assertTrue(utils.text_opt('XYZW', 'xyzw', 3))
        self.assertTrue(utils.text_opt('áčďě', 'áčďě', 3))
        self.assertFalse(utils.text_opt('č', 'áčďě', 3))
        self.assertFalse(utils.text_opt('ě', 'áčďě', 3))
        self.assertTrue(utils.text_opt('ÁČĎĚ', 'áčďě', 3))
        self.assertTrue(utils.text_opt('áčďě', 'ÁČĎĚ', 3))
        self.assertTrue(utils.text_opt('ÁČĎĚ', 'áčďě', 3))
        self.assertFalse(utils.text_opt('y', '', 3))
        self.assertTrue(utils.text_opt('', 'xyzw', 3))
        self.assertTrue(utils.text_opt('', '', 3))

    def test_lim(self):
        self.assertEqual(utils.lim(1, 2, 3), 2)
        self.assertEqual(utils.lim(1, -2, 3), 1)
        self.assertEqual(utils.lim(1, 4, 3), 3)

    def test_between(self):
        self.assertTrue(utils.between(1, 2, 3))
        self.assertTrue(utils.between(1, 1, 3))
        self.assertTrue(utils.between(1, 3, 3))
        self.assertFalse(utils.between(1, -2, 3))
        self.assertFalse(utils.between(1, 4, 3))

    def test_normalize(self):
        self.assertEqual(utils.normalize('a'), 'a')
        self.assertEqual(utils.normalize(' a'), 'a')
        self.assertEqual(utils.normalize('  a'), 'a')
        self.assertEqual(utils.normalize('a '), 'a')
        self.assertEqual(utils.normalize('a  '), 'a')
        self.assertEqual(utils.normalize('  a  '), 'a')
        self.assertEqual(utils.normalize('a b'), 'a b')
        self.assertEqual(utils.normalize('a  b'), 'a b')
        self.assertEqual(utils.normalize('  a b  '), 'a b')
        self.assertEqual(utils.normalize('  a  b  '), 'a b')
        self.assertEqual(utils.normalize('  a \u00a0 b  '), 'a b')

    def test_icmp(self):
        self.assertTrue(utils.icmp('ab', 'ab'))
        self.assertTrue(utils.icmp('aB', 'Ab'))
        self.assertFalse(utils.icmp('aB', 'AbC'))
        self.assertTrue(utils.icmp('', ''))
        self.assertFalse(utils.icmp(None, ''))
        self.assertTrue(utils.icmp(None, None))
        self.assertFalse(utils.icmp('a', ''))
        self.assertFalse(utils.icmp('', 'a'))


class TestUtils2(TestCase):

    def test_getpreset(self):
        today = date.today()
        models.Preset.objects.get_or_create(
            name='Test',
            value=15,
            valid=today)
        models.Preset.objects.get_or_create(
            name='Test',
            value=16,
            valid=(today + glob.odp))
        self.assertEqual(utils.getpreset('XXX'), 0)
        self.assertEqual(utils.getpreset('Test'), 15)


class TestViews(TestCase):

    def setUp(self):
        User.objects.create_user(
            'user',
            'user@' + glob.localdomain,
            'none'
        )
        User.objects.create_superuser(
            'superuser',
            'superuser@' + glob.localdomain,
            'none'
        )

    def test_login(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        res = self.client.get('/knr')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertFalse(self.client.login(username='user', password='wrong'))
        self.assertFalse(self.client.login(username='nouser', password='none'))
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.client.logout()
        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        res = self.client.get('/xxx/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/accounts/login/?next=/knr/',
            {'username': 'user',
             'password': 'wrong'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'login.html')
        self.assertContains(
            res,
            'Chybné uživatelské jméno nebo heslo')
        res = self.client.post(
            '/accounts/login/?next=/knr/',
            {'username': 'user',
             'password': 'none'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')

    def test_robots(self):
        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/plain; charset=utf-8')
        self.assertTemplateUsed(res, 'robots.txt')
        res = self.client.post('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_unauth(self):
        res = self.client.get('/knr/presets/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/presets/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/presets/')
        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTemplateUsed(res, 'unauth.html')
        self.assertTrue(self.client.login(
            username='superuser',
            password='none'))
        res = self.client.get('/knr/presets/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')

    def test_error(self):
        req = DummyRequest(None)
        req.method = 'GET'
        res = views.error(req)
        self.assertContains(
            res,
            'Interní chyba aplikace',
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_logout(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        res = self.client.get('/accounts/logout/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/accounts/logout/', follow=True)
        self.assertTemplateUsed(res, 'home.html')
        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/szr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_user(self):
        res = self.client.get('/accounts/user')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/accounts/user/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/accounts/user/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/accounts/user/')
        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_pwchange(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.post(
            '/accounts/pwchange/',
            {'back': 'Zpět'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'home.html')
        res = self.client.get('/accounts/pwchange/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        s = {'oldpassword': 'none',
             'newpassword1': 'newpass',
             'newpassword2': 'newpass',
             'submit': 'Změnit'}
        d = copy(s)
        d['oldpassword'] = 'wrong'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(res.context['error_message'], 'Nesprávné heslo')
        d = copy(s)
        d['newpassword1'] = 'different'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(
            res.context['error_message'],
            'Zadaná hesla se neshodují')
        d = copy(s)
        d['newpassword1'] = d['newpassword2'] = 'short'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(
            res.context['error_message'],
            'Nové heslo je příliš krátké')
        res = self.client.post('/accounts/pwchange/', s, follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchanged.html')
        self.assertTrue(self.client.login(username='user', password='newpass'))
        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_pwlost(self):
        res = self.client.get('/accounts/lostpw/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'lostpw.html')
        res = self.client.post(
            '/accounts/lostpw/',
            {'username': '',
             'back': 'Zpět'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'login.html')
        res = self.client.post(
            '/accounts/lostpw/',
            {'username': ''})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'lostpw.html')
        res = self.client.post(
            '/accounts/lostpw/',
            {'username': 'user'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwlinksent.html')
        m = mail.outbox
        self.assertEqual(len(m), 1)
        m = m[0]
        self.assertEqual(
            m.from_email,
            'Server {} <{}>'.format(glob.localsubdomain, glob.localemail))
        self.assertEqual(
            m.to,
            ['user@' + glob.localdomain])
        self.assertEqual(
            m.subject,
            'Link pro obnoveni hesla')
        match = pw_regex.search(m.body)
        self.assertTrue(match)
        link = match.group(1)
        res = self.client.get('/accounts/resetpw/{}/'.format(link))
        self.assertTemplateUsed(res, 'pwreset.html')
        newpassword = res.context['newpassword']
        self.assertEqual(len(newpassword), 10)
        self.assertFalse(self.client.login(username='user', password='none'))
        self.assertTrue(self.client.login(
            username='user',
            password=newpassword))

    def test_resetpw(self):
        res = self.client.get('/accounts/resetpw/{}/'.format('0' * 32))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_home(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'home.html')
        res = self.client.post('/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_about(self):
        res = self.client.get('/about/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'about.html')
        res = self.client.post('/about/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_stat(self):
        setdl(1)
        setpr(1)
        res = self.client.get('/stat/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'stat.html')
        res = self.client.post('/stat/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_useradd(self):
        res = self.client.get('/accounts/useradd/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        s = {'first_name': 'Tomáš',
             'last_name': 'Pecina',
             'username': 'newuser',
             'password1': 'newpass',
             'password2': 'newpass',
             'email': 'tomas@' + glob.localdomain,
             'captcha': 'Praha'}
        d = copy(s)
        d['first_name'] = ''
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['last_name'] = ''
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['username'] = ''
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['username'] = 'user'
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['password1'] = 'different'
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['password1'] = d['password2'] = 'short'
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        d = copy(s)
        d['email'] = 'noemail'
        res = self.client.post('/accounts/useradd/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        res = self.client.post('/accounts/useradd/', s, follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradded.html')
        self.assertTrue(self.client.login(
            username='newuser',
            password='newpass'))
