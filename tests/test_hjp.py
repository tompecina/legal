# -*- coding: utf-8 -*-
#
# tests/test_hjp.py
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

from legal.settings import TEST_DATA_DIR
from legal.common.utils import p2c
from legal.hjp import forms, views

from tests.glob import TEST_STRING
from tests.utils import DummyRequest, strip_xml, check_html


APP = __package__.rpartition('.')[2]


class TestForms(SimpleTestCase):

    def test_trans_form(self):

        form = forms.TransForm(
            {'transaction_type': 'balance',
             'repayment_preference': 'principal'})
        self.assertFalse(form.is_valid())

        form = forms.TransForm(
            {'transaction_type': 'balance',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertTrue(form.is_valid())

        form = forms.TransForm(
            {'transaction_type': 'debit',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertFalse(form.is_valid())

        form = forms.TransForm(
            {'transaction_type': 'debit',
             'date': '1.7.2016',
             'repayment_preference': 'principal',
             'amount': '2000'})
        self.assertTrue(form.is_valid())

        form = forms.TransForm(
            {'transaction_type': 'credit',
             'date': '1.7.2016',
             'repayment_preference': 'principal'})
        self.assertFalse(form.is_valid())

        form = forms.TransForm(
            {'transaction_type': 'credit',
             'date': '1.7.2016',
             'repayment_preference': 'principal',
             'amount': '2000'})
        self.assertTrue(form.is_valid())

    def test_main_form(self):

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'none'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'none',
             'note': 'n\rn',
             'internal_note': 'i\rn'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['note'], 'nn')
        self.assertEqual(form.cleaned_data['internal_note'], 'in')

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'fixed'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'fixed',
             'fixed_amount': '8000'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_annum'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_annum',
             'pa_rate': '13.65'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_mensem'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_mensem',
             'pm_rate': '0.94'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_diem'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'rounding': '0',
             'model': 'per_diem',
             'pd_rate': '0.125'})
        self.assertTrue(form.is_valid())


class TestViews1(SimpleTestCase):

    def test_xml(self):

        idx = 1
        while True:
            try:
                with open(join(TEST_DATA_DIR, 'hjp_debt{:d}.xml'.format(idx)), 'rb') as infile:
                    dat = infile.read()
            except:
                self.assertGreater(idx, 1)
                break
            res = views.from_xml(dat)
            self.assertIsNone(res[1])
            self.assertIs(type(res[0]), views.Debt)
            err = views.to_xml(res[0])
            self.assertXMLEqual(strip_xml(dat), strip_xml(err), msg=str(idx))
            idx += 1
        self.assertEqual(views.from_xml(b'XXX'), (None, 'Chybný formát souboru'))

    def test_getrows(self):

        self.assertEqual(views.getrows(views.Debt()), [])

    def test_getrows4(self):

        self.assertEqual(views.getrows4(views.Debt()), [])


class TestViews2(TestCase):

    fixtures = ('hjp_test.json',)

    def setUp(self):
        User.objects.create_user('user', 'user@pecina.cz', 'none')

    # def tearDown(self):
    #     self.client.logout()

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
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'fixed',
             'fixed_amount': 'XXX',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/',
            {'rounding': '0',
             'model': 'none',
             'title': 'test',
             'note': 'n',
             'internal_note': 'in',
             'submit_empty': 'Vyprázdnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
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
            with open(join(TEST_DATA_DIR, 'hjp_debt1.{}'.format(suf[0])), 'rb') as infile:
                res = self.client.post(
                    '/hjp/',
                    {'currency_0': 'EUR',
                     'rounding': '2',
                     'model': 'none',
                     'submit_load': 'Načíst',
                     'load': infile},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
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
                 'submit_' + suf[0]: suf[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suf[2])

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
            currency_0 = soup.select('#id_currency_0 option[value=OTH]')
            self.assertEqual(len(currency_0), 1)
            self.assertTrue(currency_0[0].has_attr('selected'))
            currency_1 = soup.select('#id_currency_1')
            self.assertEqual(len(currency_1), 1)
            self.assertEqual(currency_1[0]['value'], 'AUD')
            rounding = soup.select('#id_rounding option[value=2]')
            self.assertEqual(len(rounding), 1)
            self.assertTrue(rounding[0].has_attr('selected'))

        with open(join(TEST_DATA_DIR, 'hjp_debt1.xml'), 'rb') as infile:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

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
        string = res.content.decode('utf-8')
        with open(join(TEST_DATA_DIR, 'hjp_debt1.csv'), 'rb') as infile:
            dat = infile.read().decode('utf-8')
        self.assertEqual(string, dat)

        with open(join(TEST_DATA_DIR, 'hjp_err_debt1.xml'), 'rb') as infile:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        button = soup.select('input[name=submit_csv]')
        self.assertEqual(len(button), 1)
        self.assertTrue(button[0].has_attr('disabled'))
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
        self.assertEqual(res.context['err_message'], 'Nejprve zvolte soubor k načtení')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'hjp_err_debt2.xml'), 'rb') as infile:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        self.assertEqual(res.context['err_message'], 'Chyba při načtení souboru')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'hjp_err_debt3.xml'), 'rb') as infile:
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'CZK',
                 'rounding': '0',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        self.assertEqual(res.context['err_message'], 'Chyba při načtení souboru')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/',
            {'currency_0': 'EUR',
             'rounding': '2',
             'model': 'none',
             'next': '/hjp/'})
        self.assertRedirects(res, '/hjp/')

        idx = 1
        while True:
            try:
                infile = open(join(TEST_DATA_DIR, 'hjp_debt{:d}.xml'.format(idx)), 'rb')
            except:
                self.assertGreater(idx, 1)
                break
            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            infile.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            dct = {'submit_pdf': 'Export do PDF'}
            form = res.context['form']
            for key in form.fields:
                val = form[key].value()
                if val:
                    dct[key] = p2c(str(val))
            soup = BeautifulSoup(res.content, 'html.parser')
            dct['currency_0'] = soup.select('#id_currency_0 option[selected]')[0]['value']
            dct['currency_1'] = dct['currency']

            res = self.client.post('/hjp/', dct)
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
            idx += 1

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
        self.assertEqual(res.context['form']['date'].value(), today)

        res = self.client.get('/hjp/transform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hjp_transform.html')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nová transakce')

        res = self.client.post(
            '/hjp/transform/',
            {'date': '5.8.2014',
             'transaction_type': 'debit',
             'amount': '5000',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

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
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/transform/',
            {'date': '25.10.2015',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/transform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

        res = self.client.get('/hjp/transform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/hjp/transform/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'hjp_transform.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/transform/3/',
            {'date': '25.10.2015',
             'transaction_type': 'balance',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

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
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.get('/hjp/transdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_transdel.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/transdel/3/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/hjp/transdel/3/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'hjp_transdeleted.html')
        check_html(self, res.content)

        res = self.client.get('/hjp/transdel/3/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.post('/hjp/transdel/3/', follow=True)
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
             'none',
             {},
             0),
            (date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'none',
             {},
             0),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             0),
            (date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             0),
            (None,
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'fixed',
             {'fixed_amount': 300},
             300),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             9.999925144097613),
            (date(2014, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             10.027322404371585),
            (date(2014, 1, 1),
             date(2015, 1, 1),
             date(2016, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             0),
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
            (date(2006, 12, 14),
             date(2008, 2, 13),
             date(2002, 2, 6),
             100,
             'cust3',
             {},
             17.618588217680962),
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
            (date(2006, 12, 14),
             date(2008, 2, 13),
             date(2002, 2, 6),
             100,
             'cust5',
             {},
             18.78538213938169),
            (date(2002, 12, 14),
             date(2004, 2, 13),
             date(2001, 8, 6),
             100,
             'cust6',
             {},
             18.78538213938169),
            (date(2007, 6, 14),
             date(2008, 10, 13),
             date(2006, 2, 6),
             100,
             'cust6',
             {},
             13.320982109439328),
        )

        err_cases = (
            (date(2016, 1, 1),
             date(2015, 1, 1),
             date(2015, 1, 1),
             100,
             'per_annum',
             {'rate': 10,
              'day_count_convention': 'ACT/ACT',
             },
             'Chybný interval'),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(2015, 1, 1),
             0,
             'xxx',
             {},
             'Neznámý model'),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust1',
             {},
             'Chybné datum, data nejsou k disposici'),
            (date(1980, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust2',
             {},
             'Chybné datum, data nejsou k disposici'),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust3',
             {},
             'Chybné datum, data nejsou k disposici'),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust5',
             {},
             'Chybné datum, data nejsou k disposici'),
            (date(2015, 1, 1),
             date(2016, 1, 1),
             date(1980, 1, 1),
             0,
             'cust6',
             {},
             'Chybné datum, data nejsou k disposici'),
        )

        for test in cases:
            pastdate = test[0]
            presdate = test[1]
            default_date = test[2]
            principal = test[3]
            interest = views.Interest()
            interest.model = test[4]
            for key, val in test[5].items():
                interest.__setattr__(key, val)
            debt = views.Debt()
            debt.interest = interest
            calc = views.calcint(pastdate, presdate, principal, debt, default_date)
            self.assertIsNotNone(calc)
            self.assertEqual(len(calc), 2)
            self.assertIsNone(calc[1])
            self.assertAlmostEqual(calc[0], test[6])

        for test in err_cases:
            pastdate = test[0]
            presdate = test[1]
            default_date = test[2]
            principal = test[3]
            interest = views.Interest()
            interest.model = test[4]
            for key, val in test[5].items():
                interest.__setattr__(key, val)
            debt = views.Debt()
            debt.interest = interest
            calc = views.calcint(pastdate, presdate, principal, debt, default_date)
            self.assertIsNotNone(calc)
            self.assertEqual(len(calc), 2)
            self.assertIsNone(calc[0])
            self.assertEqual(calc[1], test[6])

    def test_calculation(self):

        self.assertTrue(self.client.login(username='user', password='none'))

        idx = 1
        while True:
            try:
                infile = open(join(TEST_DATA_DIR, 'hjp_debt{:d}.xml'.format(idx)), 'rb')
            except:
                self.assertGreater(idx, 1)
                break

            res = self.client.post(
                '/hjp/',
                {'currency_0': 'EUR',
                 'rounding': '2',
                 'model': 'none',
                 'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
            infile.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'hjp_mainpage.html')
            dct = {
                'title': TEST_STRING,
                'note': 'nn',
                'internal_note': 'in',
                'submit_csv': 'Export do CSV'}
            soup = BeautifulSoup(res.content, 'html.parser')
            for key in ('currency_0', 'rounding', 'ydconv', 'mdconv'):
                for opt in soup.select('#id_{} option'.format(key)):
                    if opt.has_attr('selected'):
                        dct[key] = opt['value']
                        break
            for key in ('currency_1', 'fixed_amount', 'pa_rate', 'pm_rate', 'pd_rate'):
                try:
                    dct[key] = soup.select('#id_{}'.format(key))[0]['value']
                except:
                    pass
            for key in ('model',):
                for opt in soup.select('input[name={}]'.format(key)):
                    if opt.has_attr('checked'):
                        dct[key] = opt['value']
                        break

            res = self.client.post('/hjp/', dct)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
            string = res.content.decode('utf-8')
            with open(join(TEST_DATA_DIR, 'hjp_debt{:d}.csv'.format(idx)), 'rb') as infile:
                dat = infile.read().decode('utf-8')
            self.assertEqual(string, dat, msg=str(idx))
            idx += 1
