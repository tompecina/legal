# -*- coding: utf-8 -*-
#
# common/tests.py
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

from django.test import SimpleTestCase, TestCase, Client
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from decimal import Decimal
from copy import copy
from http import HTTPStatus
from re import compile
from . import fields, forms, utils

TEST_STRING = 'Příliš žluťoučký kůň úpěnlivě přepíná ďábelské kódy'

xml_regex = compile(r'^(<[^<]+<\w+)[^>]*(.*)$')

def stripxml(s):
    try:
        s = s.decode('utf-8')
        m = xml_regex.match(s)
        return m.group(1) + m.group(2)
    except:
        return ''

class DummyResponse:
    def __init__(self, content):
        self.text = content
        self.content = content.encode('utf-8')
        self.ok = True
        self.status_code = HTTPStatus.OK

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

    def setUp(self):
        User.objects.create_user('existing', 'existing@pecina.cz', 'none')

    def tearDown(self):
        User.objects.get(username='existing').delete()

    def test_UserAddForm(self):
        s = {'first_name': 'New',
             'last_name': 'User',
             'username': 'new',
             'password1': 'nopassword',
             'password2': 'nopassword',
             'captcha': 'Praha'
        }
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

class TestUtils(SimpleTestCase):

    def test_easter(self):
        es = [
            date(1900, 4, 15), date(1901, 4,  7), date(1902, 3, 30),
            date(1903, 4, 12), date(1904, 4,  3), date(1905, 4, 23),
            date(1906, 4, 15), date(1907, 3, 31), date(1908, 4, 19),
            date(1909, 4, 11), date(1910, 3, 27), date(1911, 4, 16),
            date(1912, 4,  7), date(1913, 3, 23), date(1914, 4, 12),
            date(1915, 4,  4), date(1916, 4, 23), date(1917, 4,  8),
            date(1918, 3, 31), date(1919, 4, 20), date(1920, 4,  4),
            date(1921, 3, 27), date(1922, 4, 16), date(1923, 4,  1),
            date(1924, 4, 20), date(1925, 4, 12), date(1926, 4,  4),
            date(1927, 4, 17), date(1928, 4,  8), date(1929, 3, 31),
            date(1930, 4, 20), date(1931, 4,  5), date(1932, 3, 27),
            date(1933, 4, 16), date(1934, 4,  1), date(1935, 4, 21),
            date(1936, 4, 12), date(1937, 3, 28), date(1938, 4, 17),
            date(1939, 4,  9), date(1940, 3, 24), date(1941, 4, 13),
            date(1942, 4,  5), date(1943, 4, 25), date(1944, 4,  9),
            date(1945, 4,  1), date(1946, 4, 21), date(1947, 4,  6),
            date(1948, 3, 28), date(1949, 4, 17), date(1950, 4,  9),
            date(1951, 3, 25), date(1952, 4, 13), date(1953, 4,  5),
            date(1954, 4, 18), date(1955, 4, 10), date(1956, 4,  1),
            date(1957, 4, 21), date(1958, 4,  6), date(1959, 3, 29),
            date(1960, 4, 17), date(1961, 4,  2), date(1962, 4, 22),
            date(1963, 4, 14), date(1964, 3, 29), date(1965, 4, 18),
            date(1966, 4, 10), date(1967, 3, 26), date(1968, 4, 14),
            date(1969, 4,  6), date(1970, 3, 29), date(1971, 4, 11),
            date(1972, 4,  2), date(1973, 4, 22), date(1974, 4, 14),
            date(1975, 3, 30), date(1976, 4, 18), date(1977, 4, 10),
            date(1978, 3, 26), date(1979, 4, 15), date(1980, 4,  6),
            date(1981, 4, 19), date(1982, 4, 11), date(1983, 4,  3),
            date(1984, 4, 22), date(1985, 4,  7), date(1986, 3, 30),
            date(1987, 4, 19), date(1988, 4,  3), date(1989, 3, 26),
            date(1990, 4, 15), date(1991, 3, 31), date(1992, 4, 19),
            date(1993, 4, 11), date(1994, 4,  3), date(1995, 4, 16),
            date(1996, 4,  7), date(1997, 3, 30), date(1998, 4, 12),
            date(1999, 4,  4), date(2000, 4, 23), date(2001, 4, 15),
            date(2002, 3, 31), date(2003, 4, 20), date(2004, 4, 11),
            date(2005, 3, 27), date(2006, 4, 16), date(2007, 4,  8),
            date(2008, 3, 23), date(2009, 4, 12), date(2010, 4,  4),
            date(2011, 4, 24), date(2012, 4,  8), date(2013, 3, 31),
            date(2014, 4, 20), date(2015, 4,  5), date(2016, 3, 27),
            date(2017, 4, 16), date(2018, 4,  1), date(2019, 4, 21),
            date(2020, 4, 12), date(2021, 4,  4), date(2022, 4, 17),
            date(2023, 4,  9), date(2024, 3, 31), date(2025, 4, 20),
            date(2026, 4,  5), date(2027, 3, 28), date(2028, 4, 16),
            date(2029, 4,  1), date(2030, 4, 21), date(2031, 4, 13),
            date(2032, 3, 28), date(2033, 4, 17), date(2034, 4,  9),
            date(2035, 3, 25), date(2036, 4, 13), date(2037, 4,  5),
            date(2038, 4, 25), date(2039, 4, 10), date(2040, 4,  1),
            date(2041, 4, 21), date(2042, 4,  6), date(2043, 3, 29),
            date(2044, 4, 17), date(2045, 4,  9), date(2046, 3, 25),
            date(2047, 4, 14), date(2048, 4,  5), date(2049, 4, 18),
            date(2050, 4, 10), date(2051, 4,  2), date(2052, 4, 21),
            date(2053, 4,  6), date(2054, 3, 29), date(2055, 4, 18),
            date(2056, 4,  2), date(2057, 4, 22), date(2058, 4, 14),
            date(2059, 3, 30), date(2060, 4, 18), date(2061, 4, 10),
            date(2062, 3, 26), date(2063, 4, 15), date(2064, 4,  6),
            date(2065, 3, 29), date(2066, 4, 11), date(2067, 4,  3),
            date(2068, 4, 22), date(2069, 4, 14), date(2070, 3, 30),
            date(2071, 4, 19), date(2072, 4, 10), date(2073, 3, 26),
            date(2074, 4, 15), date(2075, 4,  7), date(2076, 4, 19),
            date(2077, 4, 11), date(2078, 4,  3), date(2079, 4, 23),
            date(2080, 4,  7), date(2081, 3, 30), date(2082, 4, 19),
            date(2083, 4,  4), date(2084, 3, 26), date(2085, 4, 15),
            date(2086, 3, 31), date(2087, 4, 20), date(2088, 4, 11),
            date(2089, 4,  3), date(2090, 4, 16), date(2091, 4,  8),
            date(2092, 3, 30), date(2093, 4, 12), date(2094, 4,  4),
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
                         
    def test_ply(self):
        self.assertEqual(utils.ply(date(2016, 7, 5), 1), date(2017, 7, 5))
        self.assertEqual(utils.ply(date(2016, 2, 29), 1), date(2017, 2, 28))
        
    def test_plm(self):
        self.assertEqual(utils.plm(date(2016, 7, 5), 1), date(2016, 8, 5))
        self.assertEqual(utils.plm(date(2015, 1, 31), 1), date(2015, 2, 28))
        self.assertEqual(utils.plm(date(2016, 1, 31), 1), date(2016, 2, 29))

    def test_yfactor(self):
        self.assertIsNone(utils.yfactor(date(2011, 7, 12),
                                        date(2011, 7, 11),
                                        'ACT/ACT'))
        self.assertIsNone(utils.yfactor(date(2011, 7, 12),
                                        date(2016, 7, 5),
                                        'XXX'))
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             'ACT/ACT'),
                               4.9821618384609625)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             'ACT/365'),
                               1820/365)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             'ACT/360'),
                               1820/360)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             'ACT/364'),
                               1820/364)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30U/360'),
                               1793/360)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E/360'),
                               1793/360)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E/360 ISDA'),
                               1793/360)
        self.assertAlmostEqual(utils.yfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E+/360'),
                               1793/360)
        
    def test_mfactor(self):
        self.assertIsNone(utils.mfactor(date(2011, 7, 12),
                                        date(2011, 7, 11),
                                        'ACT'))
        self.assertIsNone(utils.mfactor(date(2011, 7, 12),
                                        date(2016, 7, 5),
                                        'XXX'))
        self.assertAlmostEqual(utils.mfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             'ACT'),
                               59.774193548387096)
        self.assertAlmostEqual(utils.mfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30U'),
                               1793/30)
        self.assertAlmostEqual(utils.mfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E'),
                               1793/30)
        self.assertAlmostEqual(utils.mfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E ISDA'),
                               1793/30)
        self.assertAlmostEqual(utils.mfactor(date(2011, 7, 12),
                                             date(2016, 7, 5),
                                             '30E+'),
                               1793/30)

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

    def test_rmdsl(self):
        self.assertEqual(utils.rmdsl([]), [])
        self.assertEqual(utils.rmdsl([1]), [1])
        self.assertEqual(utils.rmdsl([1, 2]), [1, 2])
        self.assertEqual(utils.rmdsl([1, 2, 2]), [1, 2])
        self.assertEqual(utils.rmdsl([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(utils.rmdsl([1, 2, 2, 3, 4, 4, 4]), [1, 2, 3, 4])

class TestViews(TestCase):

    def setUp(self):
        User.objects.create_user(
            'user',
            'user@pecina.cz',
            'none'
        )
        User.objects.create_superuser(
            'superuser',
            'superuser@pecina.cz',
            'none'
        )
        self.client = Client()
        
    def tearDown(self):
        User.objects.all().delete()

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

    def test_robots(self):
        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/plain; charset=utf-8')
        self.assertTemplateUsed(res, 'robots.txt')
        res = self.client.post('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)
        
    def test_unauth(self):
        res = self.client.get('/knr/userdbreset/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/userdbreset/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/userdbreset/')
        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTemplateUsed(res, 'unauth.html')
        self.assertTrue(self.client.login(username='superuser',
                                          password='none'))
        res = self.client.get('/knr/userdbreset/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        
    def test_error(self):
        self.assertTrue(self.client.login(username='superuser',
                                          password='none'))
        res = self.client.get('/knr/userdbreset/999/')
        self.assertEqual(res.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertTemplateUsed(res, 'error.html')

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

    def test_pwchange(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/accounts/pwchange/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        s = {'oldpw': 'none', 'newpw1': 'newpass', 'newpw2': 'newpass'}
        d = copy(s)
        d['oldpw'] = 'wrong'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(res.context['error_message'], 'Nesprávné heslo')
        d = copy(s)
        d['newpw1'] = 'different'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(res.context['error_message'],
                         'Zadaná hesla se neshodují')
        d = copy(s)
        d['newpw1'] = d['newpw2'] = 'short'
        res = self.client.post('/accounts/pwchange/', d)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(res.context['error_message'],
                         'Nové heslo je příliš krátké')
        res = self.client.post('/accounts/pwchange/', s)
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.post('/accounts/pwchange/', s, follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='newpass'))
        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        
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
        
    def test_useradd(self):
        res = self.client.get('/accounts/useradd/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        s = {'first_name': 'Tomáš',
             'last_name': 'Pecina',
             'username': 'tompecina',
             'password1': 'newpass',
             'password2': 'newpass',
             'email': 'tomas@pecina.cz',
             'captcha': 'Praha'
        }
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
        res = self.client.post('/accounts/useradd/', s)
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.post('/accounts/useradd/', s, follow=True)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue(self.client.login(username='tompecina',
                                          password='newpass'))
