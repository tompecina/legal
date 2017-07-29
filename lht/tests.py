# -*- coding: utf-8 -*-
#
# lht/tests.py
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
from bs4 import BeautifulSoup
from django.test import SimpleTestCase
from lht import forms, views


class TestForms(SimpleTestCase):

    def test_MainForm(self):

        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'preset': 'none',
             'dur': '',
             'unit': 'd'})
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'dur': ['Duration may not be empty']})

        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'submit_set_beg_date': 'Dnes',
             'preset': 'd3',
             'unit': 'd'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'preset': 'd3',
             'unit': 'd'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'dur': '1',
             'preset': 'd3',
             'unit': 'd'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'beg_date': '31.12.1582',
             'preset': 'none',
             'dur': '1',
             'unit': 'd'})
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'beg_date': ['Hodnota musí být větší nebo rovna 1583-01-01.']})

        f = forms.MainForm(
            {'beg_date': '1.1.1583',
             'preset': 'none',
             'dur': '1',
             'unit': 'd'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'beg_date': '1.1.3000',
             'preset': 'none',
             'dur': '1',
             'unit': 'd'})
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'beg_date': ['Hodnota musí být menší nebo rovna 2999-12-31.']})

        f = forms.MainForm(
            {'beg_date': '31.12.2999',
             'preset': 'none',
             'dur': '1',
             'unit': 'd'})
        self.assertTrue(f.is_valid())


M0 = 'Neznámá jednotka'
M1 = 'Výsledek musí být mezi 01.01.1583 a 31.12.2999'
M2 = 'Počátek musí být mezi 01.01.1583 a 31.12.2999'
M3 = '(evidence pracovních dnů v tomto období není úplná)'

pp = [
    ['1.7.2016', 'd3', '', 'd',
     ['Po 04.07.2016']],
    ['1. 7. 2016', 'd3', '', 'd',
     ['Po 04.07.2016']],
    ['01.07.2016', 'd3', '', 'd',
     ['Po 04.07.2016']],
    ['1.7.2016', 'w1', '', 'd',
     ['Pá 08.07.2016']],
    ['1.7.2016', 'd8', '', 'd',
     ['09.07.2016 není pracovní den', 'Po 11.07.2016']],
    ['1.7.2016', 'w2', '', 'd',
     ['Pá 15.07.2016']],
    ['1.7.2016', 'd15', '', 'd',
     ['16.07.2016 není pracovní den', 'Po 18.07.2016']],
    ['1.7.2016', 'd30', '', 'd',
     ['31.07.2016 není pracovní den', 'Po 01.08.2016']],
    ['1.7.2016', 'm1', '', 'd',
     ['Po 01.08.2016']],
    ['1.7.2016', 'd60', '', 'd',
     ['Út 30.08.2016']],
    ['1.7.2016', 'm2', '', 'd',
     ['Čt 01.09.2016']],
    ['1.7.2016', 'm3', '', 'd',
     ['01.10.2016 není pracovní den', 'Po 03.10.2016']],
    ['1.7.2016', 'm6', '', 'd',
     ['01.01.2017 není pracovní den', 'Po 02.01.2017']],
    ['1.7.2016', 'y1', '', 'd',
     ['01.07.2017 není pracovní den', 'Po 03.07.2017']],
    ['1.7.2016', 'none', '1', 'd',
     ['02.07.2016 není pracovní den', 'Po 04.07.2016']],
    ['1.7.2016', 'none', '5', 'd',
     ['06.07.2016 není pracovní den', 'Čt 07.07.2016']],
    ['1.7.2016', 'none', '365', 'd',
     ['01.07.2017 není pracovní den', 'Po 03.07.2017']],
    ['1.7.2016', 'none', '-1', 'd',
     ['Čt 30.06.2016']],
    ['1.7.2016', 'none', '-6', 'd',
     ['25.06.2016 není pracovní den', 'Pá 24.06.2016']],
    ['1.7.2016', 'none', '-5', 'd',
     ['26.06.2016 není pracovní den', 'Pá 24.06.2016']],
    ['1.7.2016', 'none', '-366', 'd',
     ['St 01.07.2015']],
    ['1.7.2016', 'none', '1', 'w',
     ['Pá 08.07.2016']],
    ['1.7.2016', 'none', '100', 'w',
     ['Pá 01.06.2018']],
    ['1.7.2016', 'none', '-1', 'w',
     ['Pá 24.06.2016']],
    ['1.7.2016', 'none', '-100', 'w',
     ['Pá 01.08.2014']],
    ['1.7.2016', 'none', '1', 'm',
     ['Po 01.08.2016']],
    ['1.7.2016', 'none', '100', 'm',
     ['Pá 01.11.2024']],
    ['1.7.2016', 'none', '-1', 'm',
     ['St 01.06.2016']],
    ['1.7.2016', 'none', '-100', 'm',
     ['01.03.2008 není pracovní den', 'Pá 29.02.2008']],
    ['1.7.2016', 'none', '1', 'y',
     ['01.07.2017 není pracovní den', 'Po 03.07.2017']],
    ['1.7.2016', 'none', '100', 'y',
     ['St 01.07.2116']],
    ['1.7.2016', 'none', '-1', 'y',
     ['St 01.07.2015']],
    ['1.7.2016', 'none', '-100', 'y',
     ['01.07.1916 není pracovní den',
      'Pá 30.06.1916', M3]],
    ['1.7.2016', 'none', '1', 'b',
     ['Po 04.07.2016']],
    ['1.7.2016', 'none', '2', 'b',
     ['Čt 07.07.2016']],
    ['1.7.2016', 'none', '100', 'b',
     ['Pá 25.11.2016']],
    ['1.7.2016', 'none', '-1', 'b',
     ['Čt 30.06.2016']],
    ['1.7.2016', 'none', '-5', 'b',
     ['Pá 24.06.2016']],
    ['1.7.2016', 'none', '-100', 'b',
     ['St 10.02.2016']],
    ['31.5.2016', 'm1', '', 'd',
     ['Čt 30.06.2016']],
    ['31.12.1990', 'none', '1', 'd',
     ['01.01.1991 není pracovní den',
      'St 02.01.1991']],
    ['31.12.1990', 'none', '1', 'b',
     ['St 02.01.1991', M3]],
    ['02.01.1991', 'none', '-1', 'd',
     ['01.01.1991 není pracovní den',
      'Po 31.12.1990', M3]],
    ['03.01.1991', 'none', '-1', 'd',
     ['St 02.01.1991']],
    ['01.01.1583', 'none', '-1', 'd', [M1]],
    ['02.01.1583', 'none', '-1', 'd', [M1]],
    ['03.01.1583', 'none', '-1', 'd', [M1]],
    ['04.01.1583', 'none', '-1', 'd',
     ['Po 03.01.1583', M3]],
    ['31.12.2999', 'none', '1', 'd', [M1]],
    ['30.12.2999', 'none', '1', 'd',
     ['Út 31.12.2999']],
]

ee = [
    ['', 'd3', '', 'd'],
    ['xxx', 'd3', '', 'd'],
    ['1.7.2016', 'none', 'xxx', 'd'],
    ['1.7.2016', 'none', '', 'd'],
    ['1.7.2016', 'none', '0', 'd'],
    ['1.7.2016', 'none', '0', 'b'],
    ['31.12.1582', 'none', '5', 'b'],
    ['1.1.3000', 'none', '5', 'b'],
]


class TestViews(SimpleTestCase):

    def test_period(self):
        pp = [
            [date(2016, 7, 1), 0, 'd',
             None, date(2016, 7, 1), date(2016, 7, 1), False],
            [date(2016, 7, 9), 0, 'd',
             None, date(2016, 7, 9), date(2016, 7, 11), False],
            [date(2016, 7, 1), 0, 'b',
             None, date(2016, 7, 1), date(2016, 7, 1), False],
            [date(2016, 7, 9), 0, 'b',
             None, date(2016, 7, 11), date(2016, 7, 11), False],
            [date(2016, 7, 1), 3, 'd',
             None, date(2016, 7, 4), date(2016, 7, 4), False],
            [date(2016, 7, 1), 1, 'w',
             None, date(2016, 7, 8), date(2016, 7, 8), False],
            [date(2016, 7, 1), 8, 'd',
             None, date(2016, 7, 9), date(2016, 7, 11), False],
            [date(2016, 7, 1), 2, 'w',
             None, date(2016, 7, 15), date(2016, 7, 15), False],
            [date(2016, 7, 1), 15, 'd',
             None, date(2016, 7, 16), date(2016, 7, 18), False],
            [date(2016, 7, 1), 30, 'd',
             None, date(2016, 7, 31), date(2016, 8, 1), False],
            [date(2016, 7, 1), 1, 'm',
             None, date(2016, 8, 1), date(2016, 8, 1), False],
            [date(2016, 7, 1), 60, 'd',
             None, date(2016, 8, 30), date(2016, 8, 30), False],
            [date(2016, 7, 1), 2, 'm',
             None, date(2016, 9, 1), date(2016, 9, 1), False],
            [date(2016, 7, 1), 3, 'm',
             None, date(2016, 10, 1), date(2016, 10, 3), False],
            [date(2016, 7, 1), 6, 'm',
             None, date(2017, 1, 1), date(2017, 1, 2), False],
            [date(2016, 7, 1), 1, 'y',
             None, date(2017, 7, 1), date(2017, 7, 3), False],
            [date(2016, 7, 1), 1, 'd',
             None, date(2016, 7, 2), date(2016, 7, 4), False],
            [date(2016, 7, 1), 5, 'd',
             None, date(2016, 7, 6), date(2016, 7, 7), False],
            [date(2016, 7, 1), 365, 'd',
             None, date(2017, 7, 1), date(2017, 7, 3), False],
            [date(2016, 7, 1), -1, 'd',
             None, date(2016, 6, 30), date(2016, 6, 30), False],
            [date(2016, 7, 1), -6, 'd',
             None, date(2016, 6, 25), date(2016, 6, 24), False],
            [date(2016, 7, 1), -5, 'd',
             None, date(2016, 6, 26), date(2016, 6, 24), False],
            [date(2016, 7, 1), -366, 'd',
             None, date(2015, 7, 1), date(2015, 7, 1), False],
            [date(2016, 7, 1), 100, 'w',
             None, date(2018, 6, 1), date(2018, 6, 1), False],
            [date(2016, 7, 1), -1, 'w',
             None, date(2016, 6, 24), date(2016, 6, 24), False],
            [date(2016, 7, 1), -100, 'w',
             None, date(2014, 8, 1), date(2014, 8, 1), False],
            [date(2016, 7, 1), 100, 'm',
             None, date(2024, 11, 1), date(2024, 11, 1), False],
            [date(2016, 7, 1), -1, 'm',
             None, date(2016, 6, 1), date(2016, 6, 1), False],
            [date(2016, 7, 1), -100, 'm',
             None, date(2008, 3, 1), date(2008, 2, 29), False],
            [date(2016, 7, 1), 1, 'y',
             None, date(2017, 7, 1), date(2017, 7, 3), False],
            [date(2016, 7, 1), 100, 'y',
             None, date(2116, 7, 1), date(2116, 7, 1), False],
            [date(2016, 7, 1), -1, 'y',
             None, date(2015, 7, 1), date(2015, 7, 1), False],
            [date(2016, 7, 1), -100, 'y',
             None, date(1916, 7, 1), date(1916, 6, 30), True],
            [date(2016, 7, 1), 1, 'b',
             None, date(2016, 7, 4), date(2016, 7, 4), False],
            [date(2016, 7, 1), 2, 'b',
             None, date(2016, 7, 7), date(2016, 7, 7), False],
            [date(2016, 7, 1), 100, 'b',
             None, date(2016, 11, 25), date(2016, 11, 25), False],
            [date(2016, 7, 1), -1, 'b',
             None, date(2016, 6, 30), date(2016, 6, 30), False],
            [date(2016, 7, 1), -5, 'b',
             None, date(2016, 6, 24), date(2016, 6, 24), False],
            [date(2016, 7, 1), -100, 'b',
             None, date(2016, 2, 10), date(2016, 2, 10), False],
            [date(2016, 5, 31), 1, 'm',
             None, date(2016, 6, 30), date(2016, 6, 30), False],
            [date(1990, 12, 31), 1, 'd',
             None, date(1991, 1, 1), date(1991, 1, 2), False],
            [date(1990, 12, 31), 1, 'b',
             None, date(1991, 1, 2), date(1991, 1, 2), True],
            [date(1991, 1, 2), -1, 'd',
             None, date(1991, 1, 1), date(1990, 12, 31), True],
            [date(1991, 1, 3), -1, 'd',
             None, date(1991, 1, 2), date(1991, 1, 2), False],
            [date(1583, 1, 1), -1, 'd', M1, None, None, None],
            [date(1583, 1, 2), -1, 'd', M1, None, None, None],
            [date(1583, 1, 3), -1, 'd', M1, None, None, None],
            [date(1583, 1, 4), -1, 'd',
             None, date(1583, 1, 3), date(1583, 1, 3), True],
            [date(2999, 12, 31), 1, 'd', M1, None, None, None],
            [date(2999, 12, 30), 1, 'd',
             None, date(2999, 12, 31), date(2999, 12, 31), False],
            [date(2016, 7, 1), 1, 'xxx', M0, None, None, None],
            [date(1582, 12, 31), 1, 'd', M2, None, None, None],
            [date(3000, 1, 1), 1, 'd', M2, None, None, None],
        ]
        for p in pp:
            per = views.Period(*p[:3])
            self.assertIsInstance(per.error, bool)
            self.assertNotEqual(per.error, not per.msg) 
            self.assertEqual([per.msg, per.res, per.bus, per.unc], p[3:])
            
    def test_main(self):
        res = self.client.get('/lht')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/lht/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'lht_main.html')
        for p in pp:
            res = self.client.post(
                '/lht/',
                {'beg_date': p[0],
                 'preset': p[1],
                 'dur': p[2],
                 'unit': p[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'lht_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            l = len(msg)
            self.assertEqual(l, len(p[4]))
            for i in range(l):
                self.assertEqual(msg[i].text, p[4][i])
        for p in ee:
            res = self.client.post(
                '/lht/',
                {'beg_date': p[0],
                 'preset': p[1],
                 'dur': p[2],
                 'unit': p[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'lht_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            self.assertTrue(msg[0].text)
        res = self.client.post(
            '/lht/',
            {'submit_set_beg_date': 'Dnes'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.context['f']['beg_date'].value(), date.today())
