# -*- coding: utf-8 -*-
#
# hsp/tests.py
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

from http import HTTPStatus
from datetime import date
from io import BytesIO
from os.path import join
from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from common.settings import BASE_DIR
from common.tests import TEST_STRING, stripxml
from cache.tests import DummyRequest
from hsp import forms, views


APP = __package__

TEST_DIR = join(BASE_DIR, APP, 'testdata')


class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm({'rounding': '0'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'rounding': '0',
             'note': 'n\rn',
             'internal_note': 'i\rn'})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['note'], 'nn')
        self.assertEqual(f.cleaned_data['internal_note'], 'in')

    def test_DebitForm(self):
        f = forms.DebitForm(
            {'model': 'fixed',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_date': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_currency_0': 'CZK'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'date_from': '1.1.2000'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'date_from': '1.1.2000',
             'principal_amount': '80'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'principal_amount': '80'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'date_from': '1.1.2000',
             'principal_amount': '80'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_annum'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'per_annum',
             'pa_rate': '28.2'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_mensem'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'per_mensem',
             'pm_rate': '0.84'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm({'model': 'per_diem'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'per_diem',
             'pd_rate': '0.2'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '31.12.1999'})
        self.assertFalse(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '2.1.2000'})
        self.assertTrue(f.is_valid())

    def test_FXform(self):
        f = forms.FXform(
            {'currency_from': 'EUR',
             'currency_to': 'EUR',
             'rate_from': '1',
             'rate_to': '1'})
        self.assertFalse(f.is_valid())
        f = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1'})
        self.assertTrue(f.is_valid())
        f = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '31.12.1999'})
        self.assertFalse(f.is_valid())
        f = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '1.1.2000'})
        self.assertTrue(f.is_valid())
        f = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '2.1.2000'})
        self.assertTrue(f.is_valid())


class TestViews1(SimpleTestCase):

    def test_n2l(self):
        self.assertEqual(views.n2l(0), 'A')
        self.assertEqual(views.n2l(1), 'B')
        self.assertEqual(views.n2l(25), 'Z')
        self.assertEqual(views.n2l(26), '?')

    def test_rmdsl(self):
        self.assertEqual(views.rmdsl([]), [])
        self.assertEqual(views.rmdsl([1]), [1])
        self.assertEqual(views.rmdsl([1, 2]), [1, 2])
        self.assertEqual(views.rmdsl([1, 2, 2]), [1, 2])
        self.assertEqual(views.rmdsl([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(views.rmdsl([1, 2, 2, 3, 4, 4, 4]), [1, 2, 3, 4])

    def test_xml(self):
        i = 1
        while True:
            try:
                with open('{}/hsp/testdata/debt{:d}.xml'.format(BASE_DIR, i),
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


class TestViews2(TestCase):

    fixtures = ['hsp_test.json']

    def setUp(self):
        User.objects.create_user('user', 'user@pecina.cz', 'none')

    def tearDown(self):
        self.client.logout()

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
        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'title': 'test',
             'note': 'n',
             'internal_note': 'in',
             'submit_empty': 'Vyprázdnit kalkulaci'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
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
            with open(join(TEST_DIR, 'debt1.' + suffix[0]), 'rb') as fi:
                res = self.client.post(
                    '/hsp/',
                    {'rounding': '2',
                     'submit_load': 'Načíst',
                     'load': fi},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
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
            rounding = soup.select('#id_rounding option[value=0]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
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
                '/hsp/',
                {'submit_load': 'Načíst',
                 'load': con},
                follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
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
            rounding = soup.select('#id_rounding option[value=2]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))
        with open(join(TEST_DIR, 'debt1.xml'), 'rb') as fi:
            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'title': TEST_STRING,
             'note': 'nn',
             'internal_note': 'in',
             'submit_csv': 'Export do CSV'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn('content-type', res)
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
        s = res.content.decode('utf-8')
        with open(join(TEST_DIR, 'debt1.csv'), 'rb') as fi:
            t = fi.read().decode('utf-8')
        self.assertEqual(s, t)
        res = self.client.post(
            '/hsp/',
            {'rounding': '2',
             'submit_load': 'Načíst',
             'load': None},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Nejprve zvolte soubor k načtení')
        with open(join(TEST_DIR, 'err_debt5.xml'), 'rb') as fi:
            res = self.client.post(
                '/hsp/',
                {'rounding': '0',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            self.assertEqual(
                res.context['err_message'],
                'Chyba při načtení souboru')
        with open(join(TEST_DIR, 'err_debt6.xml'), 'rb') as fi:
            res = self.client.post(
                '/hsp/',
                {'rounding': '0',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            self.assertEqual(
                res.context['err_message'],
                'Chyba při načtení souboru')
        res = self.client.post(
            '/hsp/',
            {'rounding': '2',
             'next': '/hsp/'})
        self.assertRedirects(res, '/hsp/')
        i = 1
        while True:
            try:
                fi = open(
                    '{}/hsp/testdata/debt{:d}.xml'.format(BASE_DIR, i),
                    'rb')
            except:
                self.assertGreater(i, 1)
                break
            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            fi.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            res = self.client.post(
                '/hsp/',
                {'title': res.context['f']['title'].value(),
                 'note': res.context['f']['note'].value(),
                 'rounding': str(res.context['f']['rounding'].value()),
                 'submit_pdf': 'Export do PDF'})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'application/pdf')
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post(
                '/hsp/',
                {'submit_load': 'Načíst',
                 'load': con},
                follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            i += 1
        with open(join(TEST_DIR, 'err_debt1.xml'), 'rb') as fi:
            res = self.client.post(
                '/hsp/',
                {'title': res.context['f']['title'].value(),
                 'note': res.context['f']['note'].value(),
                 'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        res = self.client.post(
            '/hsp/',
            {'rounding': str(res.context['f']['rounding'].value()),
             'submit_pdf': 'Export do PDF'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertIn('content-type', res)
        self.assertEqual(res['content-type'], 'application/pdf')
        con = BytesIO(res.content)
        con.seek(0)
        res = self.client.post(
            '/hsp/',
            {'submit_load': 'Načíst',
             'load': con},
            follow=True)
        con.close()
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')

    def test_form(self):
        for b in [['debit', 'Nový závazek'],
                  ['credit', 'Nová splátka'],
                  ['balance', 'Nový kontrolní bod'],
                  ['fxrate', 'Nový kurs']]:
            res = self.client.get('/hsp/{}form'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/hsp/{}form/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/hsp/{}form/'.format(b[0]), follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/hsp/{}form/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'hsp_{}form.html'.format(b[0]))
            soup = BeautifulSoup(res.content, 'html.parser')
            p = soup.select('h1')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, b[1])
            self.client.logout()

    def test_debit(self):
        res = self.client.get('/hsp/debitform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hsp/debitform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hsp/debitform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hsp/debitform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_debitform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový závazek')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '4.9.2015',
             'amount': '800',
             'currency_0': 'CZK',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '10000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '5000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '7.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_annum',
             'pa_rate': '11,42',
             'ydconv': 'ACT/ACT',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_mensem',
             'pm_rate': '1,985',
             'mdconv': 'ACT',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_diem',
             'pd_rate': '1',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_diem',
             'pd_rate': '1',
             'principal_debit': '0',
             'principal_amount': '78000',
             'principal_currency_0': 'CZK',
             'date_from': '11.4.2005',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/debitform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/debitform/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_debitform.html')
        for i in range(1, 7):
            res = self.client.get('/hsp/debitform/{:d}/'.format(i))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_debitform.html')
        res = self.client.post(
            '/hsp/debitform/3/',
            {'model': 'per_diem',
             'pd_rate': '3.4',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitform/100/',
            {'model': 'per_diem',
             'pd_rate': '1',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_mensem',
             'pm_rate': '-1',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/hsp/debitform/1/',
            {'model': 'per_annum',
             'pa_rate': '11,42',
             'ydconv': 'ACT/ACT',
             'principal_debit': '2',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitform.html')
        self.assertEqual(
            res.context['err_message'],
            'Na závazek se váže úrok, vyžaduje pevnou částku')
        res = self.client.get('/hsp/debitdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitdel.html')
        res = self.client.post(
            '/hsp/debitdel/6/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/debitdel/6/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitdeleted.html')
        res = self.client.get('/hsp/debitdel/6/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post('/hsp/debitdel/6/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_credit(self):
        res = self.client.get('/hsp/creditform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hsp/creditform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nová splátka')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '10000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '5.1.2015',
             'amount': '6200',
             'currency_0': 'CZK',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/creditdel/1/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditdeleted.html')
        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '5000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '7.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '14.7.2015',
             'amount': '6800',
             'currency_0': 'CZK',
             'r0': '0',
             'r1': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '4.9.2015',
             'amount': '800',
             'currency_0': 'CZK',
             'r0': '0',
             'r1': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '4.8.2015',
             'amount': '1600',
             'currency_0': 'CZK',
             'r0': '1',
             'r1': '0',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/',
            {'date': '6.8.2015',
             'amount': '1600',
             'currency_0': 'CZK',
             'r0': '0',
             'r1': '0',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/hsp/creditform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/creditform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/creditform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_creditform.html')
        for i in range(1, 4):
            res = self.client.get('/hsp/creditform/{:d}/'.format(i))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_creditform.html')
        res = self.client.post(
            '/hsp/creditform/3/',
            {'date': '5.5.2015',
             'amount': '8600',
             'currency_0': 'CZK',
             'r0': '0',
             'r1': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/creditform/100/',
            {'date': '14.10.2015',
             'amount': '600',
             'currency_0': 'CZK',
             'r0': '1',
             'r1': '0',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/creditdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditdel.html')
        res = self.client.post(
            '/hsp/creditdel/3/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/creditdel/3/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditdeleted.html')
        res = self.client.post('/hsp/creditdel/3/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_balance(self):
        res = self.client.get('/hsp/balanceform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hsp/balanceform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hsp/balanceform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hsp/balanceform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_balanceform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový kontrolní bod')
        res = self.client.post('/hsp/balanceform/', {'submit_set_date': 'Dnes'})
        self.assertEqual(res.context['f']['date'].value(), date.today())
        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '5.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '14.7.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '6.X.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balanceform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/hsp/balanceform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/balanceform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/balanceform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_balanceform.html')
        for i in range(1, 3):
            res = self.client.get('/hsp/balanceform/{:d}/'.format(i))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_balanceform.html')
        res = self.client.post(
            '/hsp/balanceform/2/',
            {'date': '15.7.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/balanceform/100/',
            {'date': '14.10.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/balancedel/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balancedel.html')
        res = self.client.post(
            '/hsp/balancedel/2/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/balancedel/2/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balancedeleted.html')
        res = self.client.post('/hsp/balancedel/2/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_fxrate(self):
        res = self.client.get('/hsp/fxrateform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/hsp/fxrateform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/hsp/fxrateform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/hsp/fxrateform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_fxrateform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový kurs')
        res = self.client.post(
            '/hsp/fxrateform/',
            {'currency_from': 'EUR',
             'currency_to': 'CZK',
             'rate_from': '1,0',
             'rate_to': '27,415',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/fxrateform/',
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '28,3',
             'rate_to': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/fxrateform/',
            {'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_fxrateform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/hsp/fxrateform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.get('/hsp/fxrateform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/fxrateform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hsp_fxrateform.html')
        for i in range(1, 3):
            res = self.client.get('/hsp/fxrateform/{:d}/'.format(i))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_fxrateform.html')
        res = self.client.post(
            '/hsp/fxrateform/2/',
            {'currency_from': 'USD',
             'currency_to': 'CZK',
             'rate_from': '1,0',
             'rate_to': '18,90',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/fxrateform/100/',
            {'currency_from': 'EUR',
             'currency_to': 'CZK',
             'rate_from': '1,0',
             'rate_to': '27,415',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/hsp/fxratedel/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_fxratedel.html')
        res = self.client.post(
            '/hsp/fxratedel/2/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.html')
        res = self.client.post(
            '/hsp/fxratedel/2/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_fxratedeleted.html')
        res = self.client.post('/hsp/fxratedel/2/', follow=True)
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
             date(2001, 5, 6),
             100,
             'cust3',
             {},
             16.626813384235344],
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
             date(2001, 1, 6),
             100,
             'cust5',
             {},
             17.79360730593607],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust6',
             {},
             18.78538213938169],
            [date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 4, 6),
             100,
             'cust6',
             {},
             17.79360730593607],
            [date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0],
            [date(2015, 1, 1),
             date(2016, 1, 10),
             date(2015, 1, 1),
             1000,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
              'date_to': date(2016, 1, 1),
             },
             100],
        ]
        ee = [
            [date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             0,
             'xxx',
             {},
             'Neznámý model'],
            [date(2001, 12, 14),
             date(2003, 2, 13),
             date(2000, 8, 6),
             100,
             'cust1',
             {},
             'Sazba není k disposici'],
            [date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust2',
             {},
             'Sazba není k disposici'],
            [date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust3',
             {},
             'Sazba není k disposici'],
            [date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust5',
             {},
             'Sazba není k disposici'],
            [date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust6',
             {},
             'Sazba není k disposici'],
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
            for k, v in p[5].items():  # pragma: no cover
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

    def test_calc(self):
        i = 1
        while True:
            try:
                with open(
                    '{}/hsp/testdata/err_debt{:d}.xml'.format(BASE_DIR, i),
                    'rb') as fi:
                    d = fi.read()
            except:
                self.assertGreater(i, 1)
                break
            debt, m = views.fromxml(d)
            if not m:
                self.assertIs(type(debt), views.Debt)
                res = views.calc(debt)
                self.assertTrue(res.msg)
            i += 1

    def test_calculation(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        i = 1
        while True:
            try:
                fi = open(
                    '{}/hsp/testdata/debt{:d}.xml'.format(BASE_DIR, i),
                    'rb')
            except:
                self.assertGreater(i, 1)
                break
            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            fi.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            d = {'title': TEST_STRING,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_csv': 'Export do CSV'}
            soup = BeautifulSoup(res.content, 'html.parser')
            for o in soup.select('#id_rounding option'):
                if o.has_attr('selected'):
                    d['rounding'] = o['value']
                    break
            res = self.client.post('/hsp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            s = res.content.decode('utf-8')
            with open(
                '{}/hsp/testdata/debt{:d}.csv'.format(BASE_DIR, i),
                'rb') as fi:
                t = fi.read().decode('utf-8')
            self.assertEqual(s, t, msg=str(i))
            i += 1

    def test_hjp2hsp(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        for i in range(1, 14):
            with open(
                '{}/hjp/testdata/debt{:d}.xml'.format(BASE_DIR, i),
                'rb') as fi:
                res = self.client.post(
                    '/hsp/',
                    {'rounding': '2',
                     'submit_load': 'Načíst',
                     'load': fi},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.html')
            d = {'title': TEST_STRING,
                 'note': 'nn',
                 'internal_note': 'in',
                 'submit_csv': 'Export do CSV'}
            soup = BeautifulSoup(res.content, 'html.parser')
            for o in soup.select('#id_rounding option'):
                if o.has_attr('selected'):
                    d['rounding'] = o['value']
                    break
            res = self.client.post('/hsp/', d)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            s = res.content.decode('utf-8')
            with open(
                '{}/hsp/testdata/debt{:d}.csv'.format(BASE_DIR, i),
                'rb') as fi:
                t = fi.read().decode('utf-8')
            self.assertEqual(s, t, msg=str(i))
