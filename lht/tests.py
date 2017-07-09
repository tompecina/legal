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
from . import forms

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

pp = [
         ['1.7.2016', 'd3', '', 'd',
          ['Po 4. 7. 2016']],
         ['1. 7. 2016', 'd3', '', 'd',
          ['Po 4. 7. 2016']],
         ['01.07.2016', 'd3', '', 'd',
          ['Po 4. 7. 2016']],
         ['1.7.2016', 'w1', '', 'd',
          ['Pá 8. 7. 2016']],
         ['1.7.2016', 'd8', '', 'd',
          ['9. 7. 2016 není pracovní den', 'Po 11. 7. 2016']],
         ['1.7.2016', 'w2', '', 'd',
          ['Pá 15. 7. 2016']],
         ['1.7.2016', 'd15', '', 'd',
          ['16. 7. 2016 není pracovní den', 'Po 18. 7. 2016']],
         ['1.7.2016', 'd30', '', 'd',
          ['31. 7. 2016 není pracovní den', 'Po 1. 8. 2016']],
         ['1.7.2016', 'm1', '', 'd',
          ['Po 1. 8. 2016']],
         ['1.7.2016', 'd60', '', 'd',
          ['Út 30. 8. 2016']],
         ['1.7.2016', 'm2', '', 'd',
          ['Čt 1. 9. 2016']],
         ['1.7.2016', 'm3', '', 'd',
          ['1. 10. 2016 není pracovní den', 'Po 3. 10. 2016']],
         ['1.7.2016', 'm6', '', 'd',
          ['1. 1. 2017 není pracovní den', 'Po 2. 1. 2017']],
         ['1.7.2016', 'y1', '', 'd',
          ['1. 7. 2017 není pracovní den', 'Po 3. 7. 2017']],
         ['1.7.2016', 'none', '1', 'd',
          ['2. 7. 2016 není pracovní den', 'Po 4. 7. 2016']],
         ['1.7.2016', 'none', '5', 'd',
          ['6. 7. 2016 není pracovní den', 'Čt 7. 7. 2016']],
         ['1.7.2016', 'none', '365', 'd',
          ['1. 7. 2017 není pracovní den', 'Po 3. 7. 2017']],
         ['1.7.2016', 'none', '-1', 'd',
          ['Čt 30. 6. 2016']],
         ['1.7.2016', 'none', '-6', 'd',
          ['25. 6. 2016 není pracovní den', 'Pá 24. 6. 2016']],
         ['1.7.2016', 'none', '-5', 'd',
          ['26. 6. 2016 není pracovní den', 'Pá 24. 6. 2016']],
         ['1.7.2016', 'none', '-366', 'd',
          ['St 1. 7. 2015']],
         ['1.7.2016', 'none', '1', 'w',
          ['Pá 8. 7. 2016']],
         ['1.7.2016', 'none', '100', 'w',
          ['Pá 1. 6. 2018']],
         ['1.7.2016', 'none', '-1', 'w',
          ['Pá 24. 6. 2016']],
         ['1.7.2016', 'none', '-100', 'w',
          ['Pá 1. 8. 2014']],
         ['1.7.2016', 'none', '1', 'm',
          ['Po 1. 8. 2016']],
         ['1.7.2016', 'none', '100', 'm',
          ['Pá 1. 11. 2024']],
         ['1.7.2016', 'none', '-1', 'm',
          ['St 1. 6. 2016']],
         ['1.7.2016', 'none', '-100', 'm',
          ['1. 3. 2008 není pracovní den', 'Pá 29. 2. 2008']],
         ['1.7.2016', 'none', '1', 'y',
          ['1. 7. 2017 není pracovní den', 'Po 3. 7. 2017']],
         ['1.7.2016', 'none', '100', 'y',
          ['St 1. 7. 2116']],
         ['1.7.2016', 'none', '-1', 'y',
          ['St 1. 7. 2015']],
         ['1.7.2016', 'none', '-100', 'y',
          ['1. 7. 1916 není pracovní den',
           'Pá 30. 6. 1916',
           '(evidence pracovních dnů v tomto období není úplná)']],
         ['1.7.2016', 'none', '1', 'b',
          ['Po 4. 7. 2016']],
         ['1.7.2016', 'none', '2', 'b',
          ['Čt 7. 7. 2016']],
         ['1.7.2016', 'none', '100', 'b',
          ['Pá 25. 11. 2016']],
         ['1.7.2016', 'none', '-1', 'b',
          ['Čt 30. 6. 2016']],
         ['1.7.2016', 'none', '-5', 'b',
          ['Pá 24. 6. 2016']],
         ['1.7.2016', 'none', '-100', 'b',
          ['St 10. 2. 2016']],
         ['31.5.2016', 'm1', '', 'd',
          ['Čt 30. 6. 2016']],
     ]

ee = [
         ['', 'd3', '', 'd'],
         ['xxx', 'd3', '', 'd'],
         ['1.7.2016', 'none', 'xxx', 'd'],
         ['1.7.2016', 'none', '', 'd'],
         ['1.7.2016', 'none', '0', 'd'],
         ['1.7.2016', 'none', '0', 'b'],
         ['31.12.1990', 'none', '5', 'b'],
     ]

class TestViews(SimpleTestCase):

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
