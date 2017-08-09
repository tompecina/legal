# -*- coding: utf-8 -*-
#
# tests/test_cnb.py
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
from datetime import date, timedelta

from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase

from cache.models import Cache
from cnb import models, utils


class TestModels(SimpleTestCase):

    def test_models(self):

        self.assertEqual(
            str(models.FXrate(
                date=date(2000, 5, 14),
                text='test')),
            '2000-05-14')

        self.assertEqual(
            str(models.MPIrate(
                type='LOMB',
                rate=0.45,
                valid=date.today())),
            'LOMB')

        self.assertEqual(
            str(models.MPIstat(
                type='LOMB')),
            'LOMB')




class TestUtils(TestCase):

    def test_get_fx_rate(self):

        self.assertEqual(
            utils.get_fx_rate('USD', date(1990, 12, 31)),
            (None, None, None, 'Chybné datum, data nejsou k disposici'))

        self.assertEqual(
            utils.get_fx_rate('USD', (date.today() + timedelta(1))),
            (None, None, None, 'Chybné datum, data nejsou k disposici'))

        self.assertEqual(
            utils.get_fx_rate('CHF', date(2016, 4, 2)),
            (None, None, None, 'Chyba spojení se serverem ČNB'))

        self.assertEqual(
            utils.get_fx_rate('USD', date(2016, 4, 1)),
            (None, None, None, 'Chyba struktury kursové tabulky'))

        self.assertEqual(
            utils.get_fx_rate('XXX', date(2016, 7, 1)),
            (None, None, date(2016, 7, 1), 'Kurs není v kursové tabulce'))

        self.assertEqual(
            utils.get_fx_rate('VAL', date(1999, 1, 1)),
            (None, None, date(1999, 1, 1), 'Kurs není v kursové tabulce'))

        self.assertEqual(
            utils.get_fx_rate('PLZ', date(1999, 1, 1), use_fixed=True),
            (None, None, date(1999, 1, 1), 'Kurs není v kursové tabulce'))

        self.assertEqual(
            utils.get_fx_rate('EUR', date(2015, 7, 1)),
            (None, None, date(2015, 7, 1), 'Chyba řádku kursové tabulky'))

        log = []
        res = utils.get_fx_rate('USD', date(2016, 7, 1), log=log)
        self.assertAlmostEqual(res[0], 34.335)
        self.assertEqual(res[1:], (1, date(2016, 7, 1), None))
        self.assertEqual(
            log,
            [{'date': date(2016, 7, 1),
              'date_required': date(2016, 7, 1),
              'quantity': 1,
              'rate': 34.335,
              'currency': 'USD'}])
        res = utils.get_fx_rate('EUR', date(2016, 7, 1))
        self.assertAlmostEqual(res[0], 17.095)
        self.assertEqual(res[1:], (1, date(2016, 7, 1), None))

        res = utils.get_fx_rate('THB', date(2016, 7, 1))
        self.assertAlmostEqual(res[0], 99.430)
        self.assertEqual(res[1:], (100, date(2016, 7, 1), None))

        res = utils.get_fx_rate('BEF', date(2001, 5, 13))
        self.assertAlmostEqual(res[0], 55.275)
        self.assertEqual(res[1:], (100, date(2001, 5, 11), None))

        log = []
        res = utils.get_fx_rate(
            'VAL',
            date(1999, 1, 1),
            use_fixed=True,
            log_fixed=log)
        self.assertAlmostEqual(res[0], .005730089295397853)
        self.assertEqual(res[1:], (1, date(1999, 1, 1), None))
        self.assertEqual(
            log,
            [{'date_from': date(1998, 12, 31),
              'currency_to': 'EUR',
              'rate': 1936.27,
              'currency_from': 'VAL'}])

        res = utils.get_fx_rate('AUD', date(2001, 5, 13))
        self.assertAlmostEqual(res[0], 16.383)
        self.assertEqual(res[1:], (1, date(2001, 5, 11), None))

    def test_get_mpi_rate(self):

        self.assertEqual(
            utils.get_mpi_rate('XXXX', date(2016, 7, 1)),
            (None, 'Chybný druh sazby'))

        self.assertEqual(
            utils.get_mpi_rate('DISC', date(1989, 12, 31)),
            (None, 'Chybné datum, data nejsou k disposici'))

        self.assertEqual(
            utils.get_mpi_rate(
                'DISC',
                (date.today() + timedelta(1))),
            (None, 'Chybné datum, data nejsou k disposici'))

        self.assertEqual(
            utils.get_mpi_rate('LOMB', date(1990, 1, 1)),
            (None, 'Sazba není k disposici'))

        self.assertEqual(
            utils.get_mpi_rate('REPO', date(1990, 1, 1)),
            (None, 'Chyba spojení se serverem ČNB'))

        res = utils.get_mpi_rate('DISC', date(2008, 5, 1))
        self.assertAlmostEqual(res[0], 2.75)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('DISC', date(2014, 11, 19))
        self.assertAlmostEqual(res[0], .06)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('LOMB', date(1997, 3, 31))
        self.assertAlmostEqual(res[0], 4.00)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('LOMB', date(1996, 6, 20))
        self.assertAlmostEqual(res[0], 22.50)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('LOMB', date(1996, 6, 21))
        self.assertAlmostEqual(res[0], 4.00)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('LOMB', date(1997, 5, 15))
        self.assertAlmostEqual(res[0], 4.00)
        self.assertIsNone(res[1])

        res = utils.get_mpi_rate('LOMB', date(1997, 5, 16))
        self.assertAlmostEqual(res[0], 51.00)
        self.assertIsNone(res[1])

        models.MPIstat.objects.all().delete()

        Cache.objects.filter(
            url='https://www.cnb.cz/cs/faq/vyvoj_lombard_historie.txt').update(text='XXX')
        self.assertEqual(
            utils.get_mpi_rate('LOMB', date(1997, 5, 16)),
            (None, 'Chyba tabulky sazeb (1)'))

        cache = Cache.objects.filter(
            url='https://www.cnb.cz/cs/faq/vyvoj_diskontni_historie.txt')
        cache.update(text=cache[0].text.replace(',', 'x'))
        self.assertEqual(
            utils.get_mpi_rate('DISC', date(2014, 11, 19)),
            (None, 'Chyba tabulky sazeb (2)'))


class TestViews(TestCase):

    def test_main(self):

        button_names = (
            'submit_show_fx',
            'submit_conv_from',
            'submit_conv_to',
            'submit_DISC',
            'submit_LOMB',
            'submit_REPO',
        )

        button_values = (
            'Zobrazit kurs',
            'Převod cizí měna → CZK',
            'Převod CZK → cizí měna',
            'Diskontní sazba',
            'Lombardní sazba',
            '2T repo sazba',
        )

        cases = (
            ('EUR', '', '1.7.2016', '', '', 0,
             ('1 EUR = 17,095 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '', '', 0,
             ('1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'THB', '1.7.2016', '', '', 0,
             ('100 THB = 99,430 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'VAL', '1.7.2016', '', '', 0,
             ('Kurs není v kursové tabulce',)),
            ('OTH', '', '1.7.2016', '', '', 0,
             ('Chybné zadání',)),
            ('EUR', '', '1.17.2016', '', '', 0,
             ('Chybné zadání',)),
            ('EUR', '', '1.7.2016', '516', '', 1,
             ('516,00 EUR = 8.821,02 CZK',
              '1 EUR = 17,095 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '179.500', '', 1,
             ('179.500,00 USD = 6.163.132,50 CZK',
              '1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '179 500', '', 1,
             ('179.500,00 USD = 6.163.132,50 CZK',
              '1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '179 500,00', '', 1,
             ('179.500,00 USD = 6.163.132,50 CZK',
              '1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '0.179 500,00', '', 1,
             ('179.500,00 USD = 6.163.132,50 CZK',
              '1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'THB', '1.7.2016', '116', '', 1,
             ('116,00 THB = 115,34 CZK',
              '100 THB = 99,430 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'VAL', '1.7.2016', '4000', '', 1,
             ('Kurs není v kursové tabulce',)),
            ('OTH', '', '1.7.2016', '515', '', 1,
             ('Chybné zadání',)),
            ('EUR', '', '1.17.2016', '968,50', '', 1,
             ('Chybné zadání',)),
            ('OTH', 'USD', '1.7.2016', '0', '', 1,
             ('Chybné zadání',)),
            ('OTH', 'USD', '1.7.2016', '-515', '', 1,
             ('Chybné zadání',)),
            ('EUR', '', '1.7.2016', '516', '', 2,
             ('516,00 CZK = 30,18 EUR',
              '1 EUR = 17,095 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('USD', '', '1.7.2016', '179.500', '', 2,
             ('179.500,00 CZK = 5.227,90 USD',
              '1 USD = 34,335 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'THB', '1.7.2016', '116', '', 2,
             ('116,00 CZK = 116,66 THB',
              '100 THB = 99,430 CZK',
              '(Kurs vyhlášený ke dni: 01.07.2016)')),
            ('OTH', 'VAL', '1.7.2016', '4000', '', 2,
             ('Kurs není v kursové tabulce',)),
            ('OTH', '', '1.7.2016', '515', '', 2,
             ('Chybné zadání',)),
            ('EUR', '', '1.17.2016', '968,50', '', 2,
             ('Chybné zadání',)),
            ('OTH', 'USD', '1.7.2016', '0', '', 2,
             ('Chybné zadání',)),
            ('OTH', 'USD', '1.7.2016', '-515', '', 2,
             ('Chybné zadání',)),
            ('EUR', '', '', '', '19.11.2014', 3,
             ('Diskontní sazba platná ke dni 19.11.2014:',
              '0,06 %')),
            ('EUR', '', '', '', '21.6.1996', 4,
             ('Lombardní sazba platná ke dni 21.06.1996:',
              '4,00 %')),
            ('EUR', '', '', '', '1.5.2008', 5,
             ('Chyba spojení se serverem ČNB',)),
            ('OTH', 'USD', '', '', '29.2.2014', 3,
             ('Chybné zadání',)),
            ('OTH', 'USD', '', '', '29.2.2014', 4,
             ('Chybné zadání',)),
            ('OTH', 'USD', '', '', '29.2.2014', 5,
             ('Chybné zadání',)),
        )

        res = self.client.get('/cnb')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/cnb/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'cnb_main.html')

        today = date.today()

        for button in ['fx_date', 'mpi_date']:
            res = self.client.post('/cnb/', {'submit_set_' + button: True})
            self.assertEqual(res.context['form'][button].value(), today)

        for test in cases:
            res = self.client.post(
                '/cnb/',
                {'curr_0': test[0],
                 'curr_1': test[1],
                 'fx_date': test[2],
                 'basis': test[3],
                 'mpi_date': test[4],
                 button_names[test[5]]: button_values[test[5]]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'cnb_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            length = len(msg)
            self.assertEqual(length, len(test[6]))
            for idx in range(length):
                self.assertEqual(msg[idx].text, test[6][idx])
