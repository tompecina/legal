# -*- coding: utf-8 -*-
#
# hjp/tests.py
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
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from io import BytesIO
from common.settings import BASE_DIR
from cache.tests import DummyRequest
from common.tests import TEST_STRING, stripxml
from common.utils import p2c
from . import forms, views

class TestForms(SimpleTestCase):

    def test_TransForm(self):
        f = forms.TransForm(
            {'transaction_type': 'balance',
             'repayment_preference': 'principal'})
        self.assertFalse(f.is_valid())
        f = forms.TransForm(
            {'transaction_type': 'balance',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertTrue(f.is_valid())
        f = forms.TransForm(
            {'transaction_type': 'debit',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertFalse(f.is_valid())
        f = forms.TransForm(
            {'transaction_type': 'debit',
             'date': '1.7.2016',
             'repayment_preference': 'principal',
             'amount': '2000'})
        self.assertTrue(f.is_valid())
        f = forms.TransForm(
            {'transaction_type': 'credit',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertFalse(f.is_valid())
        f = forms.TransForm(
            {'transaction_type': 'credit',
             'date': '1.7.2016',
             'repayment_preference': 'principal',
             'amount': '2000'})
        self.assertTrue(f.is_valid())

    def test_MainForm(self):
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'none'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'none',
             'note': 'n\rn',
             'internal_note': 'i\rn'})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['note'], 'nn')
        self.assertEqual(f.cleaned_data['internal_note'], 'in')
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'fixed'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'fixed',
             'fixed_amount': '8000'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_annum'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_annum',
             'pa_rate': '13.65'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_mensem'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_mensem',
             'pm_rate': '0.94'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_diem'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'model': 'per_diem',
             'pd_rate': '0.125'})
        self.assertTrue(f.is_valid())

class TestViews1(SimpleTestCase):

    def test_xml(self):
        i = 1
        while True:
            try:
                with open(BASE_DIR + '/hjp/testdata/debt%d.xml' % i,
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
        self.assertEqual(views.fromxml(b'XXX'), (None, 'Chybný formát souboru'))

    def test_dispcurr(self):
        self.assertEqual(views.dispcurr('CZK'), 'Kč')
        self.assertEqual(views.dispcurr('EUR'), 'EUR')

    def test_getrows(self):
        self.assertEqual(views.getrows(views.Debt()), [])

    def test_getrows4(self):
        self.assertEqual(views.getrows4(views.Debt()), [])

class TestViews2(TestCase):
    fixtures = ['hjp_test.json']
    
    @classmethod
    def setUpClass(cls):
        super(TestViews2, cls).setUpClass()
        User.objects.create_user('user', 'user@pecina.cz', 'none')
        
    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        super(TestViews2, cls).tearDownClass()
        
    def test_main(self):
        res = self.client.get('/hjp')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hjp/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hjp/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hjp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'fixed',
             'fixed_amount': 'XXX',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'title': 'test',
             'note': 'n',
             'internal_note': 'in',
             'submit_empty': 'Vyprázdnit kalkulaci'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('#id_title')
        self.assertEqual(len(title), 1)
        self.assertNotIn('value', title[0])
        note = soup.select('#id_note')
        self.assertEqual(len(note), 1)
        self.assertEqual(note[0].text, '')
        internal_note = soup.select('#id_internal_note')
        self.assertEqual(len(internal_note), 1)
        self.assertEqual(internal_note[0].text, '')
        for suffix in [['xml', 'Uložit', 'text/xml; charset=utf-8'],
                       ['pdf', 'Export do PDF', 'application/pdf']]:
            with open(BASE_DIR + '/hjp/testdata/debt1.' + suffix[0],
                      'rb') as fi:
                res = self.client.post(
                    '/hjp/',
                    {'currency_0': 'EUR',
                     'rounding': '2',
                     'model': 'none',
                     'submit_load': 'Načíst',
                     'load': fi},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], TEST_STRING)
            note = soup.select('#id_note')
            self.assertEqual(len(note), 1)
            self.assertEqual(note[0].text, 'Poznámka')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'Interní poznámka')
            currency_0 = soup.select('#id_currency_0 option[value=CZK]')
            self.assertEqual(len(currency_0), 1)
            self.assertTrue(currency_0[0].has_attr('selected'))
            rounding = soup.select('#id_rounding option[value=0]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'OTH',
                 'currency_1': 'AUD',
                 'rounding': '2',
                 'model': 'none',
                 'title': TEST_STRING,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_' + suffix[0]: suffix[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suffix[2])
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post(
                '/hjp/',
                {'submit_load': 'Načíst',
                 'load': con},
                follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], TEST_STRING)
            note = soup.select('#id_note')
            self.assertEqual(len(note), 1)
            self.assertEqual(note[0].text, 'nn')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'in')
            currency_0 = soup.select('#id_currency_0 option[value=OTH]')
            self.assertEqual(len(currency_0), 1)
            self.assertTrue(currency_0[0].has_attr('selected'))
            currency_1 = soup.select('#id_currency_1')
            self.assertEqual(len(currency_1), 1)
            self.assertEqual(currency_1[0]['value'], 'AUD')
            rounding = soup.select('#id_rounding option[value=2]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
        with open(BASE_DIR + '/hjp/testdata/debt1.xml', 'rb') as fi:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/',
            {'currency_0': 'CZK',
             'rounding': '0',
             'model': 'per_annum',
             'pa_rate': '12,6',
             'ydconv': 'ACT/ACT',
             'title': TEST_STRING,
             'note': 'nn',
             'internal_note': 'in',
             'submit_csv': 'Export do CSV'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn('content-type', res)
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
        s = res.content.decode('utf-8')
        with open(BASE_DIR + '/hjp/testdata/debt1.csv', 'rb') as fi:
            t = fi.read().decode('utf-8')
        self.assertEqual(s, t)
        with open(BASE_DIR + '/hjp/testdata/err_debt1.xml', 'rb') as fi:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        b = soup.select('input[name=submit_csv]')
        self.assertEqual(len(b), 1)
        self.assertTrue(b[0].has_attr('disabled'))
        self.assertContains(res, 'Chybné datum, data nejsou k disposici')
        res = self.client.post(
            '/hjp/',
            {'currency_0': 'OTH',
             'currency_1': 'AUD',
             'rounding': '2',
             'model': 'none',
             'title': TEST_STRING,
             'note': 'nn',
             'internal_note': 'in',
             'submit_pdf': 'Export do PDF'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn('content-type', res)
        self.assertEqual(res['content-type'], 'application/pdf')
        res = self.client.post(
            '/hjp/',
            {'currency_0': 'EUR',
             'rounding': '2',
             'model': 'none',
             'submit_load': 'Načíst',
             'load': None},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Nejprve zvolte soubor k načtení')
        with open(BASE_DIR + '/hjp/testdata/err_debt2.xml', 'rb') as fi:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            self.assertEqual(
                res.context['err_message'],
                'Chyba při načtení souboru')
        with open(BASE_DIR + '/hjp/testdata/err_debt3.xml', 'rb') as fi:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            self.assertEqual(
                res.context['err_message'],
                'Chyba při načtení souboru')
        res = self.client.post(
            '/hjp/',
            {'currency_0': 'EUR',
             'rounding': '2',
             'model': 'none',
             'next': '/hjp/'})
        self.assertRedirects(res, '/hjp/')
        i = 1
        while True:
            try:
                fi = open(BASE_DIR + '/hjp/testdata/debt%d.xml' % i, 'rb')
            except:
                self.assertGreater(i, 1)
                break
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            fi.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            d = {'submit_pdf': 'Export do PDF'}
            f = res.context['f']
            for n in f.fields.keys():
                v = f[n].value()
                if v != None:
                    d[n] = p2c(str(v))
            soup = BeautifulSoup(res.content, 'html.parser')
            d['currency_0'] = \
                soup.select('#id_currency_0 option[selected]')[0]['value']
            d['currency_1'] = d['currency']
            res = self.client.post('/hjp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'application/pdf')
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post(
                '/hjp/',
                {'submit_load': 'Načíst',
                 'load': con},
                follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            i += 1
        
    def test_trans(self):
        res = self.client.get('/hjp/transform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hjp/transform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hjp/transform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        today = date.today()
        res = self.client.post(
            '/hjp/transform/',
            {'transaction_type': 'balance',
             'submit_set_date': 'Dnes'})
        self.assertEqual(res.context['f']['date'].value(), today)
        res = self.client.get('/hjp/transform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hjp_transform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nová transakce')
        res = self.client.post(
            '/hjp/transform/',
            {'date': '5.8.2014',
             'transaction_type': 'debit',
             'amount': '5000',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/transform/',
            {'date': '25.10.2014',
             'transaction_type': 'credit',
             'amount': '4000',
             'repayment_preference': 'interest',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/transform/',
            {'date': '25.10.2015',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/transform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.get('/hjp/transform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hjp/transform/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hjp_transform.html')
        res = self.client.post(
            '/hjp/transform/3/',
            {'date': '25.10.2015',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/transform/100/',
            {'date': '25.10.2015',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/hjp/transform/',
            {'date': 'XXX',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_transform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.get('/hjp/transdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_transdel.html')
        res = self.client.post(
            '/hjp/transdel/3/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        res = self.client.post(
            '/hjp/transdel/3/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_transdeleted.html')
        res = self.client.get('/hjp/transdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post('/hjp/transdel/3/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
            
    def test_debt(self):
        req = DummyRequest('test-session')
        c = views.Debt()
        c.title = TEST_STRING
        self.assertTrue(views.setdebt(req, c))
        self.assertEqual(views.getdebt(req).title, TEST_STRING)

    def test_calcint(self):
        pp = [
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'none',
             {},
             0],
            [date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'none',
             {},
             0],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             0],
            [date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             0],
            [None,
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             300],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             9.999925144097613],
            [date(2014, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             10.027322404371585],
            [date(2014, 1, 1),
             date(2015, 1, 1),
             date(2016, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0],
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
            [date(2006, 12, 14),
             date(2008, 2, 13),
             date(2002, 2, 6),
             100,
             'cust3',
             {},
             17.618588217680962],
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
            [date(2006, 12, 14),
             date(2008, 2, 13),
             date(2002, 2, 6),
             100,
             'cust5',
             {},
             18.78538213938169],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust6',
             {},
             18.78538213938169],
            [date(2007, 6, 14),
             date(2008, 10, 13),
             date(2006, 2, 6),
             100,
             'cust6',
             {},
             13.320982109439328],
        ]
        ee = [
            [date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             'Chybný interval'],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             0,
             'xxx',
             {},
             'Neznámý model'],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust1',
             {},
             'Chybné datum, data nejsou k disposici'],
            [date(1980, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust2',
             {},
             'Chybné datum, data nejsou k disposici'],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust3',
             {},
             'Chybné datum, data nejsou k disposici'],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust5',
             {},
             'Chybné datum, data nejsou k disposici'],
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust6',
             {},
             'Chybné datum, data nejsou k disposici'],
        ]
        for p in pp:
            pastdate = p[0]
            presdate = p[1]
            default_date = p[2]
            principal = p[3]
            i = views.Interest()
            i.model = p[4]
            for k, v in p[5].items():
                i.__setattr__(k, v)
            d = views.Debt()
            d.interest = i
            c = views.calcint(pastdate, presdate, principal, d, default_date)
            self.assertIsNotNone(c)
            self.assertEqual(len(c), 2)
            self.assertIsNone(c[1])
            self.assertAlmostEqual(c[0], p[6])
        for p in ee:
            pastdate = p[0]
            presdate = p[1]
            default_date = p[2]
            principal = p[3]
            i = views.Interest()
            i.model = p[4]
            for k, v in p[5].items():
                i.__setattr__(k, v)
            d = views.Debt()
            d.interest = i
            c = views.calcint(pastdate, presdate, principal, d, default_date)
            self.assertIsNotNone(c)
            self.assertEqual(len(c), 2)
            self.assertIsNone(c[0])
            self.assertEqual(c[1], p[6])

    def test_calculation(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        i = 1
        while True:
            try:
                fi = open(BASE_DIR + '/hjp/testdata/debt%d.xml' % i, 'rb')
            except:
                self.assertGreater(i, 1)
                break
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            fi.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            d = {'title': TEST_STRING,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_csv': 'Export do CSV'
            }
            soup = BeautifulSoup(res.content, 'html.parser')
            for f in ['currency_0', 'rounding', 'ydconv', 'mdconv']:
                for o in soup.select('#id_' + f + ' option'):
                    if o.has_attr('selected'):
                        d[f] = o['value']
                        break
            for f in ['currency_1',
                      'fixed_amount',
                      'pa_rate',
                      'pm_rate',
                      'pd_rate']:
                try:
                    d[f] = soup.select('#id_' + f)[0]['value']
                except:
                    pass
            for f in ['model']:
                for o in soup.select('input[name=' + f + ']'):
                    if o.has_attr('checked'):
                        d[f] = o['value']
                        break
            res = self.client.post('/hjp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            s = res.content.decode('utf-8')
            with open(BASE_DIR + '/hjp/testdata/debt%d.csv' % i, 'rb') as fi:
                t = fi.read().decode('utf-8')
            self.assertEqual(s, t, msg=str(i))
            i += 1
