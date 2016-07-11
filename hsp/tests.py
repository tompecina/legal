# -*- coding: utf-8 -*-
#
# hsp/tests.py
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

from django.test import SimpleTestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from io import BytesIO
from common.settings import BASE_DIR
from cache.tests import DummyRequest
from . import forms, views

class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm({'rounding': '0'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm({'rounding': '0',
                            'note': 'n\rn',
                            'internal_note': 'i\rn'})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['note'], 'nn')
        self.assertEqual(f.cleaned_data['internal_note'], 'in')

    def test_DebitForm(self):
        f = forms.DebitForm({'model': 'fixed',
                             'fixed_currency_0': 'CZK',
                             'fixed_date': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'fixed',
                             'fixed_amount': '500',
                             'fixed_date': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'fixed',
                             'fixed_amount': '500',
                             'fixed_currency_0': 'CZK'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'fixed',
                             'fixed_amount': '500',
                             'fixed_currency_0': 'CZK',
                             'fixed_date': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'principal_debit': '0',
                             'principal_currency_0': 'CZK',
                             'date_from': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'principal_debit': '0',
                             'date_from': '1.1.2000',
                             'principal_amount': '80'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'principal_debit': '0',
                             'principal_currency_0': 'CZK',
                             'principal_amount': '80'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'principal_debit': '0',
                             'principal_currency_0': 'CZK',
                             'date_from': '1.1.2000',
                             'principal_amount': '80'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_annum'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'per_annum',
                             'pa_rate': '28.2'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_mensem'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'per_mensem',
                             'pm_rate': '0.84'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_diem'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'per_diem',
                             'pd_rate': '0.2'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'date_from': '1.1.2000',
                             'date_to': '31.12.1999'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'date_from': '1.1.2000',
                             'date_to': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'cust1',
                             'date_from': '1.1.2000',
                             'date_to': '2.1.2000'})
        self.assertTrue(f.is_valid())

    def test_FXform(self):
        f = forms.FXform({'currency_from': 'EUR',
                          'currency_to': 'EUR',
                          'rate_from': '1',
                          'rate_to': '1'})
        self.assertFalse(f.is_valid())
        f = forms.FXform({'currency_from': 'CZK',
                          'currency_to': 'EUR',
                          'rate_from': '16.6',
                          'rate_to': '1'})
        self.assertTrue(f.is_valid())
        f = forms.FXform({'currency_from': 'CZK',
                          'currency_to': 'EUR',
                          'rate_from': '16.6',
                          'rate_to': '1',
                          'date_from': '1.1.2000',
                          'date_to': '31.12.1999'})
        self.assertFalse(f.is_valid())
        f = forms.FXform({'currency_from': 'CZK',
                          'currency_to': 'EUR',
                          'rate_from': '16.6',
                          'rate_to': '1',
                          'date_from': '1.1.2000',
                          'date_to': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.FXform({'currency_from': 'CZK',
                          'currency_to': 'EUR',
                          'rate_from': '16.6',
                          'rate_to': '1',
                          'date_from': '1.1.2000',
                          'date_to': '2.1.2000'})
        self.assertTrue(f.is_valid())

ts = 'Příliš žluťoučký kůň úpěnlivě přepíná ďábelské kódy'
        
def stripxml(s):
    try:
        s = s.decode('utf-8')
        s = s.split('<debt', 1)
        return s[0] + '<debt>' + s[1].split('>', 1)[1]
    except:
        return ''

class TestViews(TransactionTestCase):
    fixtures = ['hsp_test.json']
    
    def setUp(self):
        self.client = Client()
        User.objects.create_user('user', 'user@pecina.cz', 'none')

    def tearDown(self):
        User.objects.all().delete()
        
    def test_main(self):
        res = self.client.get('/hsp')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hsp/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post('/hsp/', {'rounding': '0',
                                         'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post('/hsp/',
                               {'rounding': '0',
                                'submit_empty': 'Vyprázdnit'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post('/hsp/',
                               {'rounding': '0',
                                'title': 'test',
                                'note': 'n',
                                'internal_note': 'in',
                                'submit_empty': 'Vyprázdnit kalkulaci'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
        title = soup.select('#id_title')
        self.assertEqual(len(title), 1)
        self.assertNotIn('value', title[0])
        note = soup.select('#id_note')
        self.assertEqual(len(note), 1)
        self.assertEqual(note[0].text, '')
        internal_note = soup.select('#id_internal_note')
        self.assertEqual(len(internal_note), 1)
        self.assertEqual(internal_note[0].text, '')
        for suffix in [['xml', 'Uložit', 'text/xml'],
                       ['pdf', 'Export do PDF', 'application/pdf']]:
            with open(BASE_DIR + '/hsp/testdata/debt1.' + suffix[0],
                      'rb') as fi:
                res = self.client.post('/hsp/',
                                       {'rounding': '2',
                                        'submit_load': 'Načíst',
                                        'load': fi},
                                       follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], ts)
            note = soup.select('#id_note')
            self.assertEqual(len(note), 1)
            self.assertEqual(note[0].text, 'Poznámka')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'Interní poznámka')
            rounding = soup.select('#id_rounding option[value=0]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
            res = self.client.post('/hsp/',
                                   {'rounding': '2',
                                    'title': ts,
                                    'note': 'nn',
                                    'internal_note': 'in',
                                    'submit_' + suffix[0]: suffix[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suffix[2])
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post('/hsp/',
                                   {'submit_load': 'Načíst',
                                    'load': con},
                                   follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], ts)
            note = soup.select('#id_note')
            self.assertEqual(len(note), 1)
            self.assertEqual(note[0].text, 'nn')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'in')
            rounding = soup.select('#id_rounding option[value=2]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
        with open(BASE_DIR + '/hsp/testdata/debt1.xml', 'rb') as fi:
            res = self.client.post('/hsp/',
                                   {'rounding': '2',
                                    'submit_load': 'Načíst',
                                    'load': fi},
                                   follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post('/hsp/',
                               {'rounding': '0',
                                'title': ts,
                                'note': 'nn',
                                'internal_note': 'in',
                                'submit_csv': 'Export do CSV'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn('content-type', res)
        self.assertEqual(res['content-type'], 'text/csv')
        s = res.content.decode('utf-8')
        with open(BASE_DIR + '/hsp/testdata/debt1.csv', 'rb') as fi:
            t = fi.read().decode('utf-8')
        self.assertEqual(s, t)

    def test_form(self):
        for b in [['debit', 'Nový závazek'],
                  ['credit', 'Nová splátka'],
                  ['balance', 'Nový kontrolní bod'],
                  ['fxrate', 'Nový kurs']]:
            res = self.client.get('/hsp/' + b[0] + 'form')
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/hsp/' + b[0] + 'form/')
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/hsp/' + b[0] + 'form/', follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/hsp/' + b[0] + 'form/')
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'hsp_' + b[0] + 'form.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            p = soup.select('h1')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, b[1])
            self.client.logout()
            
    def test_debt(self):
        req = DummyRequest('test-session')
        c = views.Debt()
        c.title = ts
        self.assertTrue(views.setdebt(req, c))
        self.assertEqual(views.getdebt(req).title, ts)

    def test_n2l(self):
        self.assertEqual(views.n2l(0), 'A')
        self.assertEqual(views.n2l(1), 'B')
        self.assertEqual(views.n2l(25), 'Z')
        self.assertEqual(views.n2l(26), '?')

    def test_calcint(self):
        pp = [
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             9.999925144097613],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/365',
             },
             10],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/360',
             },
             10.13888888888889],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/364',
             },
             10.027472527472527],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30U/360',
             },
             10],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
             },
             10],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360 ISDA',
             },
             10],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E+/360',
             },
             10],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': 'ACT',
             },
             12],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30U',
             },
             12],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E',
             },
             12],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E ISDA',
             },
             12],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E+',
             },
             12],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0.767123287671233],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/365',
             },
             0.767123287671233],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/360',
             },
             0.7777777777777777],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/364',
             },
             0.7692307692307692],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30U/360',
             },
             0.7777777777777777],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
             },
             0.7777777777777777],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360 ISDA',
             },
             0.8333333333333331],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E+/360',
             },
             0.7777777777777777],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': 'ACT',
             },
             1],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30U',
             },
             0.9333333333333332],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E',
             },
             0.9333333333333332],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E ISDA',
             },
             1],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E+',
             },
             0.9333333333333332],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_diem',
             {'rate': 1},
             36.5],
            [date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_diem',
             {'rate': 1},
             2.8],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust1',
             {},
             44.33816902462759,
             [date(2001, 7, 1)]],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust2',
             {},
             13.607290964892584],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust3',
             {},
             19.427118796317085],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust4',
             {},
             106.5],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust5',
             {},
             20.59391271801781],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust6',
             {},
             18.78538213938169],
            [date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0],
        ]
        ee = [
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             0,
             'xxx',
             {},
             'Neznámý model'],
        ]
        for p in pp:
            pastdate = p[0]
            presdate = p[1]
            i = views.Debit()
            i.default_date = p[2]
            i.principal_debit = 0
            i.principal_amount = p[3]
            i.model = p[4]
            for k, v in p[5].items():
                i.__setattr__(k, v)
            d = views.Debt()
            d.interest = [i]
            r = views.Result()
            r.mpi = []
            c = views.calcint(i, pastdate, presdate, d, r)
            self.assertIsNotNone(c)
            self.assertEqual(len(c), 2)
            self.assertIsNone(c[1])
            self.assertAlmostEqual(c[0], p[6])
        for p in ee:
            pastdate = p[0]
            presdate = p[1]
            i = views.Debit()
            i.default_date = p[2]
            i.principal_debit = 0
            i.principal_amount = p[3]
            i.model = p[4]
            for k, v in p[5].items():
                i.__setattr__(k, v)
            d = views.Debt()
            d.interest = [i]
            r = views.Result()
            r.mpi = []
            c = views.calcint(i, pastdate, presdate, d, r)
            self.assertIsNotNone(c)
            self.assertEqual(len(c), 2)
            self.assertIsNone(c[0])
            self.assertEqual(c[1], p[6])

    def test_xml(self):
        i = 1
        while True:
            try:
                with open(BASE_DIR + '/hsp/testdata/debt%d.xml' % i,
                          'rb') as fi:
                    d = fi.read()
            except:
                self.assertGreater(i, 1)
                break
            c = views.fromxml(d)
            self.assertIsNone(c[1])
            self.assertIs(type(c[0]), views.Debt)
            e = views.toxml(c[0])
            self.assertXMLEqual(stripxml(d), stripxml(e), msg=str(i))
            i += 1

    def test_calculation(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        i = 1
        while True:
            try:
                with open(BASE_DIR + '/hsp/testdata/debt%d.xml' % i,
                          'rb') as fi:
                    res = self.client.post('/hsp/',
                                           {'rounding': '2',
                                            'submit_load': 'Načíst',
                                            'load': fi},
                                           follow=True)
            except:
                self.assertGreater(i, 1)
                break
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            d = {'title': ts,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_csv': 'Export do CSV'
            }
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
                for o in soup.select('#id_rounding option'):
                    if o.has_attr('selected'):
                        d['rounding'] = o['value']
                        break
            except:
                self.fail()
            res = self.client.post('/hsp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv')
            s = res.content.decode('utf-8')
            with open(BASE_DIR + '/hsp/testdata/debt%d.csv' % i, 'rb') as fi:
                t = fi.read().decode('utf-8')
            self.assertEqual(s, t, msg=str(i))
            i += 1

    def test_hjp2hsp(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        for i in range(1, 14):
            with open(BASE_DIR + '/hjp/testdata/debt%d.xml' % i, 'rb') as fi:
                res = self.client.post('/hsp/',
                                       {'rounding': '2',
                                        'submit_load': 'Načíst',
                                        'load': fi},
                                       follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            d = {'title': ts,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_csv': 'Export do CSV'
            }
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
                for o in soup.select('#id_rounding option'):
                    if o.has_attr('selected'):
                        d['rounding'] = o['value']
                        break
            except:
                self.fail()
            res = self.client.post('/hsp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv')
            s = res.content.decode('utf-8')
            with open(BASE_DIR + '/hsp/testdata/debt%d.csv' % i, 'rb') as fi:
                t = fi.read().decode('utf-8')
            self.assertEqual(s, t, msg=str(i))
