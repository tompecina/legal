# -*- coding: utf-8 -*-
#
# tests/test_hsp.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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
from django.apps import apps
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User

from legal.settings import TEST_DATA_DIR, BASE_DIR, FULL_CONTENT_TYPE
from legal.hsp import forms, views

from tests.glob import TEST_STRING
from tests.utils import DummyRequest, strip_xml, validate_xml, check_html


APP = __file__.rpartition('_')[2].partition('.')[0]
APPVERSION = apps.get_app_config(APP).version
with open(join(BASE_DIR, 'legal', APP, 'static', '{}-{}.xsd'.format(APP, APPVERSION)), 'rb') as xsdfile:
    XSD = xsdfile.read()


class TestForms(SimpleTestCase):

    def test_main_form(self):

        form = forms.MainForm({'rounding': '0'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'note': 'n\rn',
             'internal_note': 'i\rn'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], 'nn')
        self.assertEqual(form.cleaned_data['internal_note'], 'in')

    def test_debit_form(self):

        form = forms.DebitForm(
            {'model': 'fixed',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2000'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_date': '1.1.2000'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_currency_0': 'CZK'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'fixed',
             'fixed_amount': '500',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2000'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'date_from': '1.1.2000'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'date_from': '1.1.2000',
             'principal_amount': '80'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'principal_amount': '80'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'principal_debit': '0',
             'principal_currency_0': 'CZK',
             'date_from': '1.1.2000',
             'principal_amount': '80'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm({'model': 'per_annum'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'per_annum',
             'pa_rate': '28.2'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm({'model': 'per_mensem'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'per_mensem',
             'pm_rate': '0.84'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm({'model': 'per_diem'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'per_diem',
             'pd_rate': '0.2'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '31.12.1999'})
        self.assertFalse(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '1.1.2000'})
        self.assertTrue(form.is_valid())

        form = forms.DebitForm(
            {'model': 'cust1',
             'date_from': '1.1.2000',
             'date_to': '2.1.2000'})
        self.assertTrue(form.is_valid())

    def test_fx_form(self):

        form = forms.FXform(
            {'currency_from': 'EUR',
             'currency_to': 'EUR',
             'rate_from': '1',
             'rate_to': '1'})
        self.assertFalse(form.is_valid())

        form = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1'})
        self.assertTrue(form.is_valid())

        form = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '31.12.1999'})
        self.assertFalse(form.is_valid())

        form = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '1.1.2000'})
        self.assertTrue(form.is_valid())

        form = forms.FXform(
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '16.6',
             'rate_to': '1',
             'date_from': '1.1.2000',
             'date_to': '2.1.2000'})
        self.assertTrue(form.is_valid())


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

        idx = 1
        while True:
            try:
                with open(join(TEST_DATA_DIR, 'hsp_debt{:d}.xml'.format(idx)), 'rb') as infile:
                    dat = infile.read()
            except:
                self.assertGreater(idx, 1)
                break
            debt = views.from_xml(dat)
            self.assertIsNone(debt[1])
            self.assertIs(type(debt[0]), views.Debt)
            xml = views.to_xml(debt[0])
            self.assertTrue(validate_xml(xml, XSD))
            self.assertXMLEqual(strip_xml(dat), strip_xml(xml), msg=str(idx))
            idx += 1


class TestViews2(TestCase):

    fixtures = ('hsp_test.json',)

    def setUp(self):
        User.objects.create_user('user', 'user@pecina.cz', 'none')

    def test_main(self):

        res = self.client.get('/hsp')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/hsp/', follow=True)
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/',
            {'rounding': '0',
             'title': 'test',
             'note': 'n',
             'internal_note': 'in',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)
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

        for suf in (
                ('xml', 'Uložit', 'text/xml; charset=utf-8'),
                ('pdf', 'Export do PDF', 'application/pdf'),
        ):
            with open(
                    join(
                        TEST_DATA_DIR,
                        'hsp_debt1.{}'.format(suf[0])),
                    'rb') as infile:
                res = self.client.post(
                    '/hsp/',
                    {'rounding': '2',
                     'submit_load': 'Načíst',
                     'load': infile},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            check_html(self, res.content, key=suf[0])
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
                 'submit_' + suf[0]: suf[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suf[2])
            if suf[0] == 'xml':
                self.assertTrue(validate_xml(res.content, XSD))

            con = BytesIO(res.content)
            con.seek(0)

            res = self.client.post(
                '/hsp/',
                {'submit_load': 'Načíst',
                 'load': con},
                follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            check_html(self, res.content)
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

        with open(join(TEST_DATA_DIR, 'hsp_debt1.xml'), 'rb') as infile:
            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

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
        string = res.content.decode('utf-8')
        with open(join(TEST_DATA_DIR, 'hsp_debt1.csv'), 'rb') as infile:
            dat = infile.read().decode('utf-8')
        self.assertEqual(string, dat)

        res = self.client.post(
            '/hsp/',
            {'rounding': '2',
             'submit_load': 'Načíst',
             'load': None},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        self.assertEqual(res.context['err_message'], 'Nejprve zvolte soubor k načtení')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'hsp_err_debt5.xml'), 'rb') as infile:
            res = self.client.post(
                '/hsp/',
                {'rounding': '0',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            self.assertEqual(res.context['err_message'], 'Chyba při načtení souboru')
            check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'hsp_err_debt6.xml'), 'rb') as infile:
            res = self.client.post(
                '/hsp/',
                {'rounding': '0',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            self.assertEqual(res.context['err_message'], 'Chyba při načtení souboru')
            check_html(self, res.content)

        res = self.client.post(
            '/hsp/',
            {'rounding': '2',
             'next': '/hsp/'})
        self.assertRedirects(res, '/hsp/')

        idx = 1
        while True:
            try:
                infile = open(join(TEST_DATA_DIR, 'hsp_debt{:d}.xml'.format(idx)), 'rb')
            except:
                self.assertGreater(idx, 1)
                break

            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            infile.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            check_html(self, res.content, key=idx)
            soup = BeautifulSoup(res.content, 'html.parser')

            res = self.client.post(
                '/hsp/',
                {'title': res.context['form']['title'].value(),
                 'note': res.context['form']['note'].value(),
                 'rounding': str(res.context['form']['rounding'].value()),
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
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            idx += 1

        with open(join(TEST_DATA_DIR, 'hsp_err_debt1.xml'), 'rb') as infile:
            res = self.client.post(
                '/hsp/',
                {'title': res.context['form']['title'].value(),
                 'note': res.context['form']['note'].value(),
                 'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')

        res = self.client.post(
            '/hsp/',
            {'rounding': str(res.context['form']['rounding'].value()),
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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

    def test_form(self):

        for ftype in (
                ('debit', 'Nový závazek'),
                ('credit', 'Nová splátka'),
                ('balance', 'Nový kontrolní bod'),
                ('fxrate', 'Nový kurs'),
        ):

            res = self.client.get('/hsp/{}form'.format(ftype[0]))
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

            res = self.client.get('/hsp/{}form/'.format(ftype[0]))
            self.assertEqual(res.status_code, HTTPStatus.FOUND)

            res = self.client.get('/hsp/{}form/'.format(ftype[0]), follow=True)
            self.assertTemplateUsed(res, 'login.xhtml')

            self.assertTrue(self.client.login(username='user', password='none'))

            res = self.client.get('/hsp/{}form/'.format(ftype[0]))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
            self.assertTemplateUsed(res, 'hsp_{}form.xhtml'.format(ftype[0]))
            check_html(self, res.content, key=ftype[0])
            soup = BeautifulSoup(res.content, 'html.parser')
            title = soup.select('h1')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0].text, ftype[1])

            self.client.logout()

    def test_debit(self):

        res = self.client.get('/hsp/debitform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/hsp/debitform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/hsp/debitform/', follow=True)
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/hsp/debitform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_debitform.xhtml')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nový závazek')

        res = self.client.post(
            '/hsp/creditform/',
            {'date': '4.9.2015',
             'amount': '800',
             'currency_0': 'CZK',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '10000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '5000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '7.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_annum',
             'pa_rate': '11,42',
             'ydconv': 'ACT/ACT',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_mensem',
             'pm_rate': '1,985',
             'mdconv': 'ACT',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'per_diem',
             'pd_rate': '1',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/debitform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/hsp/debitform/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_debitform.xhtml')
        check_html(self, res.content)

        for idx in range(1, 7):
            res = self.client.get('/hsp/debitform/{:d}/'.format(idx))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_debitform.xhtml')
            check_html(self, res.content, key=idx)

        res = self.client.post(
            '/hsp/debitform/3/',
            {'model': 'per_diem',
             'pd_rate': '3.4',
             'principal_debit': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_debitform.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/1/',
            {'model': 'per_annum',
             'pa_rate': '11,42',
             'ydconv': 'ACT/ACT',
             'principal_debit': '2',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitform.xhtml')
        self.assertEqual(res.context['err_message'], 'Na závazek se váže úrok, vyžaduje pevnou částku')
        check_html(self, res.content)

        res = self.client.get('/hsp/debitdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitdel.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitdel/6/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitdel/6/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_debitdeleted.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/debitdel/6/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        check_html(self, res.content)

        res = self.client.post('/hsp/debitdel/6/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        check_html(self, res.content)

    def test_credit(self):

        res = self.client.get('/hsp/creditform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/hsp/creditform/', follow=True)
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nová splátka')

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '10000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '1.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/creditform/',
            {'date': '5.1.2015',
             'amount': '6200',
             'currency_0': 'CZK',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/creditdel/1/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditdeleted.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/debitform/',
            {'model': 'fixed',
             'fixed_amount': '5000',
             'fixed_currency_0': 'CZK',
             'fixed_date': '7.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/creditform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        check_html(self, res.content)

        res = self.client.get('/hsp/creditform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
        check_html(self, res.content)

        for idx in range(1, 4):
            res = self.client.get('/hsp/creditform/{:d}/'.format(idx))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_creditform.xhtml')
            check_html(self, res.content, key=idx)

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
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_creditdel.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/creditdel/3/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/creditdel/3/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_creditdeleted.xhtml')
        check_html(self, res.content)

        res = self.client.post('/hsp/creditdel/3/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_balance(self):

        res = self.client.get('/hsp/balanceform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/hsp/balanceform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/hsp/balanceform/', follow=True)
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/hsp/balanceform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_balanceform.xhtml')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nový kontrolní bod')

        res = self.client.post('/hsp/balanceform/', {'submit_set_date': 'Dnes'})
        self.assertEqual(res.context['form']['date'].value(), date.today())
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '5.1.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '14.7.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balanceform/',
            {'date': '6.X.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balanceform.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balanceform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/balanceform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/hsp/balanceform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_balanceform.xhtml')
        check_html(self, res.content)

        for idx in range(1, 3):
            res = self.client.get('/hsp/balanceform/{:d}/'.format(idx))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_balanceform.xhtml')
            check_html(self, res.content, key=idx)

        res = self.client.post(
            '/hsp/balanceform/2/',
            {'date': '15.7.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balanceform/100/',
            {'date': '14.10.2015',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/hsp/balancedel/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balancedel.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balancedel/2/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/balancedel/2/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_balancedeleted.xhtml')
        check_html(self, res.content)
        check_html(self, res.content)

        res = self.client.post('/hsp/balancedel/2/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_fxrate(self):

        res = self.client.get('/hsp/fxrateform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/hsp/fxrateform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/hsp/fxrateform/', follow=True)
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/hsp/fxrateform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_fxrateform.xhtml')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nový kurs')

        res = self.client.post(
            '/hsp/fxrateform/',
            {'currency_from': 'EUR',
             'currency_to': 'CZK',
             'rate_from': '1,0',
             'rate_to': '27,415',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/fxrateform/',
            {'currency_from': 'CZK',
             'currency_to': 'EUR',
             'rate_from': '28,3',
             'rate_to': '1',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/fxrateform/',
            {'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_fxrateform.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/fxrateform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.get('/hsp/fxrateform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/hsp/fxrateform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'hsp_fxrateform.xhtml')
        check_html(self, res.content)

        for idx in range(1, 3):
            res = self.client.get('/hsp/fxrateform/{:d}/'.format(idx))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_fxrateform.xhtml')
            check_html(self, res.content, key=idx)

        res = self.client.post(
            '/hsp/fxrateform/2/',
            {'currency_from': 'USD',
             'currency_to': 'CZK',
             'rate_from': '1,0',
             'rate_to': '18,90',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

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
        self.assertTemplateUsed(res, 'hsp_fxratedel.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/fxratedel/2/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/hsp/fxratedel/2/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hsp_fxratedeleted.xhtml')
        check_html(self, res.content)

        res = self.client.post('/hsp/fxratedel/2/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_debt(self):

        req = DummyRequest('test-session')
        debt = views.Debt()
        debt.title = TEST_STRING
        self.assertTrue(views.setdebt(req, debt))
        self.assertEqual(views.getdebt(req).title, TEST_STRING)

    def test_calcint(self):

        cases = (
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             9.999925144097613),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/365',
             },
             10),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/360',
             },
             10.13888888888889),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/364',
             },
             10.027472527472527),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30U/360',
             },
             10),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
             },
             10),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360 ISDA',
             },
             10),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E+/360',
             },
             10),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': 'ACT',
             },
             12),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30U',
             },
             12),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E',
             },
             12),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E ISDA',
             },
             12),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E+',
             },
             12),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             .767123287671233),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/365',
             },
             .767123287671233),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/360',
             },
             .7777777777777777),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/364',
             },
             .7692307692307692),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30U/360',
             },
             .7777777777777777),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
             },
             .7777777777777777),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360 ISDA',
             },
             .8333333333333331),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E+/360',
             },
             .7777777777777777),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': 'ACT',
             },
             1),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30U',
             },
             .9333333333333332),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E',
             },
             .9333333333333332),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E ISDA',
             },
             1),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_mensem',
             {'rate': 1,
              'day_count_convention': '30E+',
             },
             .9333333333333332),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_diem',
             {'rate': 1},
             36.5),
            (date(2015, 1, 31),
             date(2015, 2, 28),
             date(2015, 1, 31),
             100,
             'per_diem',
             {'rate': 1},
             2.8),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust1',
             {},
             44.33816902462759,
             (date(2001, 7, 1))),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust2',
             {},
             13.607290964892584),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust3',
             {},
             19.427118796317085),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 5, 6),
             100,
             'cust3',
             {},
             16.626813384235344),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust4',
             {},
             106.5),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust5',
             {},
             20.59391271801781),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 1, 6),
             100,
             'cust5',
             {},
             17.79360730593607),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust6',
             {},
             18.78538213938169),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 4, 6),
             100,
             'cust6',
             {},
             17.79360730593607),
            (date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0),
            (date(2015, 1, 1),
             date(2016, 1, 10),
             date(2015, 1, 1),
             1000,
             'per_annum',
             {'rate': 10,
              'day_count_convention': '30E/360',
              'date_to': date(2016, 1, 1),
             },
             100),
        )

        err_cases = (
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             0,
             'xxx',
             {},
             'Neznámý model'),
            (date(2001, 12, 14),
             date(2003, 2, 13),
             date(2000, 8, 6),
             100,
             'cust1',
             {},
             'Sazba není k disposici'),
            (date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust2',
             {},
             'Sazba není k disposici'),
            (date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust3',
             {},
             'Sazba není k disposici'),
            (date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust5',
             {},
             'Sazba není k disposici'),
            (date(1999, 12, 14),
             date(2003, 2, 13),
             date(1999, 8, 6),
             100,
             'cust6',
             {},
             'Sazba není k disposici'),
        )

        for test in cases:
            pastdate = test[0]
            presdate = test[1]
            debit = views.Debit()
            debit.default_date = test[2]
            debit.principal_debit = 0
            debit.principal_amount = test[3]
            debit.model = test[4]
            for key, val in test[5].items():
                debit.__setattr__(key, val)
            debt = views.Debt()
            debt.interest = [debit]
            res = views.Result()
            res.mpi = []
            calc = views.calcint(debit, pastdate, presdate, debt, res)
            self.assertIsNotNone(calc)
            self.assertEqual(len(calc), 2)
            self.assertIsNone(calc[1])
            self.assertAlmostEqual(calc[0], test[6])

        for test in err_cases:
            pastdate = test[0]
            presdate = test[1]
            debit = views.Debit()
            debit.default_date = test[2]
            debit.principal_debit = 0
            debit.principal_amount = test[3]
            debit.model = test[4]
            for key, val in test[5].items():  # pragma: no cover
                debit.__setattr__(key, val)
            debt = views.Debt()
            debt.interest = [debit]
            res = views.Result()
            res.mpi = []
            calc = views.calcint(debit, pastdate, presdate, debt, res)
            self.assertIsNotNone(calc)
            self.assertEqual(len(calc), 2)
            self.assertIsNone(calc[0])
            self.assertEqual(calc[1], test[6])

    def test_calc(self):

        idx = 1
        while True:
            try:
                with open(join(TEST_DATA_DIR, 'hsp_err_debt{:d}.xml'.format(idx)), 'rb') as infile:
                    dat = infile.read()
            except:
                self.assertGreater(idx, 1)
                break
            debt, msg = views.from_xml(dat)
            if not msg:
                self.assertIs(type(debt), views.Debt)
                res = views.calc(debt)
                self.assertTrue(res.msg)
            idx += 1

    def test_calculation(self):

        self.assertTrue(self.client.login(username='user', password='none'))

        idx = 1
        while True:
            try:
                infile = open(join(TEST_DATA_DIR, 'hsp_debt{:d}.xml'.format(idx)), 'rb')
            except:
                self.assertGreater(idx, 1)
                break

            res = self.client.post(
                '/hsp/',
                {'rounding': '2',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            infile.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            check_html(self, res.content, key=idx)
            dct = {
                'title': TEST_STRING,
                'note': 'nn',
                'internal_note': 'in',
                'submit_csv': 'Export do CSV',
            }
            soup = BeautifulSoup(res.content, 'html.parser')
            for opt in soup.select('#id_rounding option'):
                if opt.has_attr('selected'):
                    dct['rounding'] = opt['value']
                    break

            res = self.client.post('/hsp/', dct)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            string = res.content.decode('utf-8')
            with open(join(TEST_DATA_DIR, 'hsp_debt{:d}.csv'.format(idx)), 'rb') as infile:
                dat = infile.read().decode('utf-8')
            self.assertEqual(string, dat, msg=str(idx))
            idx += 1

    def test_hjp2hsp(self):

        self.assertTrue(self.client.login(username='user', password='none'))

        for idx in range(1, 14):
            with open(join(TEST_DATA_DIR, 'hsp_debt{:d}.xml'.format(idx)), 'rb') as infile:
                res = self.client.post(
                    '/hsp/',
                    {'rounding': '2',
                     'submit_load': 'Načíst',
                     'load': infile},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hsp_mainpage.xhtml')
            check_html(self, res.content, key=idx)
            dct = {
                'title': TEST_STRING,
                'note': 'nn',
                'internal_note': 'in',
                'submit_csv': 'Export do CSV',
            }
            soup = BeautifulSoup(res.content, 'html.parser')
            for opt in soup.select('#id_rounding option'):
                if opt.has_attr('selected'):
                    dct['rounding'] = opt['value']
                    break

            res = self.client.post('/hsp/', dct)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            string = res.content.decode('utf-8')
            with open(join(TEST_DATA_DIR, 'hsp_debt{:d}.csv'.format(idx)), 'rb') as infile:
                dat = infile.read().decode('utf-8')
            self.assertEqual(string, dat, msg=str(idx))
