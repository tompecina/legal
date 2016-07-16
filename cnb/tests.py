# -*- coding: utf-8 -*-
#
# cnb/tests.py
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
from http import HTTPStatus
from datetime import date, timedelta
from bs4 import BeautifulSoup
from cache.models import Cache
from . import main, models, views

class TestMain(TestCase):
    fixtures = ['cnb_test.json']

    def test_getFXrate(self):
        self.assertEqual(
            main.getFXrate('USD', date(1990, 12, 31)),
            (None, None, None, 'Chybné datum, data nejsou k disposici'))
        self.assertEqual(
            main.getFXrate('USD', (date.today() + timedelta(1))),
            (None, None, None, 'Chybné datum, data nejsou k disposici'))
        self.assertEqual(
            main.getFXrate('CHF', date(2016, 4, 2)),
            (None, None, None, 'Chyba spojení se serverem ČNB'))
        self.assertEqual(
            main.getFXrate('USD', date(2016, 4, 1)),
            (None, None, None, 'Chyba struktury kursové tabulky'))
        self.assertEqual(
            main.getFXrate('XXX', date(2016, 7, 1)),
            (None, None, date(2016, 7, 1), 'Kurs není v kursové tabulce'))
        self.assertEqual(
            main.getFXrate('VAL', date(1999, 1, 1)),
            (None, None, date(1999, 1, 1), 'Kurs není v kursové tabulce'))
        self.assertEqual(
            main.getFXrate('PLZ', date(1999, 1, 1), use_fixed=True),
            (None, None, date(1999, 1, 1), 'Kurs není v kursové tabulce'))
        self.assertEqual(
            main.getFXrate('EUR', date(2015, 7, 1)),
            (None, None, date(2015, 7, 1), 'Chyba řádku kursové tabulky'))
        log = []
        r = main.getFXrate('USD', date(2016, 7, 1), log=log)
        self.assertAlmostEqual(r[0], 34.335)
        self.assertEqual(r[1:], (1, date(2016, 7, 1), None))
        self.assertEqual(
            log,
            [{'date': date(2016, 7, 1),
              'date_required': date(2016, 7, 1),
              'quantity': 1,
              'rate': 34.335,
              'currency': 'USD'}])
        r = main.getFXrate('EUR', date(2016, 7, 1))
        self.assertAlmostEqual(r[0], 17.095)
        self.assertEqual(r[1:], (1, date(2016, 7, 1), None))
        r = main.getFXrate('THB', date(2016, 7, 1))
        self.assertAlmostEqual(r[0], 99.430)
        self.assertEqual(r[1:], (100, date(2016, 7, 1), None))
        r = main.getFXrate('BEF', date(2001, 5, 13))
        self.assertAlmostEqual(r[0], 55.275)
        self.assertEqual(r[1:], (100, date(2001, 5, 11), None))
        log = []
        r = main.getFXrate(
            'VAL',
            date(1999, 1, 1),
            use_fixed=True,
            log_fixed=log)
        self.assertAlmostEqual(r[0], 0.005730089295397853)
        self.assertEqual(r[1:], (1, date(1999, 1, 1), None))
        self.assertEqual(
            log,
            [{'date_from': date(1998, 12, 31),
              'currency_to': 'EUR',
              'rate': 1936.27,
              'currency_from': 'VAL'}])
        r = main.getFXrate('AUD', date(2001, 5, 13))
        self.assertAlmostEqual(r[0], 16.383)
        self.assertEqual(r[1:], (1, date(2001, 5, 11), None))

    def test_getMPIrate1(self):
        self.assertEqual(
            main.getMPIrate('XXXX', date(2016, 7, 1)),
            (None, 'Chybný druh sazby'))
        self.assertEqual(
            main.getMPIrate('DISC', date(1989, 12, 31)),
            (None, 'Chybné datum, data nejsou k disposici'))
        self.assertEqual(
            main.getMPIrate(
                'DISC',
                (date.today() + timedelta(1))),
            (None, 'Chybné datum, data nejsou k disposici'))
        self.assertEqual(
            main.getMPIrate('LOMB', date(1990, 1, 1)),
            (None, 'Sazba není k disposici'))
        self.assertEqual(
            main.getMPIrate('REPO', date(1990, 1, 1)),
            (None, 'Chyba spojení se serverem ČNB'))
        r = main.getMPIrate('DISC', date(2008, 5, 1))
        self.assertAlmostEqual(r[0], 2.75)
        self.assertIsNone(r[1])
        r = main.getMPIrate('DISC', date(2014, 11, 19))
        self.assertAlmostEqual(r[0], 0.06)
        self.assertIsNone(r[1])
        r = main.getMPIrate('LOMB', date(1997, 3, 31))
        self.assertAlmostEqual(r[0], 4.00)
        self.assertIsNone(r[1])
        r = main.getMPIrate('LOMB', date(1996, 6, 20))
        self.assertAlmostEqual(r[0], 22.50)
        self.assertIsNone(r[1])
        r = main.getMPIrate('LOMB', date(1996, 6, 21))
        self.assertAlmostEqual(r[0], 4.00)
        self.assertIsNone(r[1])
        r = main.getMPIrate('LOMB', date(1997, 5, 15))
        self.assertAlmostEqual(r[0], 4.00)
        self.assertIsNone(r[1])
        r = main.getMPIrate('LOMB', date(1997, 5, 16))
        self.assertAlmostEqual(r[0], 51.00)
        self.assertIsNone(r[1])

    def test_getMPIrate2(self):
        Cache.objects.filter(pk=2).update(text='XXX')
        self.assertEqual(
            main.getMPIrate('LOMB', date(1997, 5, 16)),
            (None, 'Chyba tabulky sazeb (1)'))
        Cache.objects.filter(pk=1).delete()
        self.assertEqual(
            main.getMPIrate('DISC', date(1997, 5, 16)),
            (None, 'Chyba spojení se serverem ČNB'))
        
    def test_getMPIrate3(self):
        c = Cache.objects.filter(pk=2)
        c.update(text=c[0].text.replace(',', 'x'))
        self.assertEqual(
            main.getMPIrate('LOMB', date(1997, 5, 16)),
            (None, 'Chyba tabulky sazeb (2)'))
        
bn = ['submit_show_fx',
      'submit_conv_from',
      'submit_conv_to',
      'submit_DISC',
      'submit_LOMB',
      'submit_REPO'
]

bv = ['Zobrazit kurs',
      'Převod cizí měna → CZK',
      'Převod CZK → cizí měna',
      'Diskontní sazba',
      'Lombardní sazba',
      '2T repo sazba'
]

pp = [
         ['EUR', '', '1.7.2016', '', '', 0,
          ['1 EUR = 17,095 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '', '', 0,
          ['1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'THB', '1.7.2016', '', '', 0,
          ['100 THB = 99,430 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'VAL', '1.7.2016', '', '', 0,
          ['Kurs není v kursové tabulce']],
         ['OTH', '', '1.7.2016', '', '', 0,
          ['Chybné zadání']],
         ['EUR', '', '1.17.2016', '', '', 0,
          ['Chybné zadání']],
         ['EUR', '', '1.7.2016', '516', '', 1,
          ['516,00 EUR = 8.821,02 CZK',
           '1 EUR = 17,095 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '179.500', '', 1,
          ['179.500,00 USD = 6.163.132,50 CZK',
           '1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '179 500', '', 1,
          ['179.500,00 USD = 6.163.132,50 CZK',
           '1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '179 500,00', '', 1,
          ['179.500,00 USD = 6.163.132,50 CZK',
           '1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '0.179 500,00', '', 1,
          ['179.500,00 USD = 6.163.132,50 CZK',
           '1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'THB', '1.7.2016', '116', '', 1,
          ['116,00 THB = 115,34 CZK',
           '100 THB = 99,430 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'VAL', '1.7.2016', '4000', '', 1,
          ['Kurs není v kursové tabulce']],
         ['OTH', '', '1.7.2016', '515', '', 1,
          ['Chybné zadání']],
         ['EUR', '', '1.17.2016', '968,50', '', 1,
          ['Chybné zadání']],
         ['OTH', 'USD', '1.7.2016', '0', '', 1,
          ['Chybné zadání']],
         ['OTH', 'USD', '1.7.2016', '-515', '', 1,
          ['Chybné zadání']],
         ['EUR', '', '1.7.2016', '516', '', 2,
          ['516,00 CZK = 30,18 EUR',
           '1 EUR = 17,095 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['USD', '', '1.7.2016', '179.500', '', 2,
          ['179.500,00 CZK = 5.227,90 USD',
           '1 USD = 34,335 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'THB', '1.7.2016', '116', '', 2,
          ['116,00 CZK = 116,66 THB',
           '100 THB = 99,430 CZK',
           '(Kurs vyhlášený ke dni: 1. 7. 2016)']],
         ['OTH', 'VAL', '1.7.2016', '4000', '', 2,
          ['Kurs není v kursové tabulce']],
         ['OTH', '', '1.7.2016', '515', '', 2,
          ['Chybné zadání']],
         ['EUR', '', '1.17.2016', '968,50', '', 2,
          ['Chybné zadání']],
         ['OTH', 'USD', '1.7.2016', '0', '', 2,
          ['Chybné zadání']],
         ['OTH', 'USD', '1.7.2016', '-515', '', 2,
          ['Chybné zadání']],
         ['EUR', '', '', '', '19.11.2014', 3,
          ['Diskontní sazba platná ke dni 19. 11. 2014:',
           '0,06 %']],
         ['EUR', '', '', '', '21.6.1996', 4,
          ['Lombardní sazba platná ke dni 21. 6. 1996:',
           '4,00 %']],
         ['EUR', '', '', '', '1.5.2008', 5,
          ['Chyba spojení se serverem ČNB']],
         ['OTH', 'USD', '', '', '29.2.2014', 3,
          ['Chybné zadání']],
         ['OTH', 'USD', '', '', '29.2.2014', 4,
          ['Chybné zadání']],
         ['OTH', 'USD', '', '', '29.2.2014', 5,
          ['Chybné zadání']],
     ]

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

class TestViews(TestCase):
    fixtures = ['cnb_test.json']

    def test_main(self):
        res = self.client.get('/cnb')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/cnb/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'cnb_main.html')
        today = date.today()
        for f in ['fx_date', 'mpi_date']:
            res = self.client.post('/cnb/', {'submit_set_' + f: True})
            self.assertEqual(res.context['f'][f].value(), today)
        for p in pp:
            res = self.client.post(
                '/cnb/',
                {'curr_0': p[0],
                 'curr_1': p[1],
                 'fx_date': p[2],
                 'basis': p[3],
                 'mpi_date': p[4],
                 bn[p[5]]: bv[p[5]]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'cnb_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            l = len(msg)
            self.assertEqual(l, len(p[6]))
            for i in range(l):
                self.assertEqual(msg[i].text, p[6][i])
