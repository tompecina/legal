# -*- coding: utf-8 -*-
#
# dvt/tests.py
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

from django.test import SimpleTestCase, Client
from http import HTTPStatus
from bs4 import BeautifulSoup
from . import forms, views

class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '',
             'days': ''})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '10',
             'months': '',
             'days': ''})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '10',
             'days': ''})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '',
             'days': '10'})
        self.assertTrue(f.is_valid())

pp = [
         ['1.7.2016', '1', '', '',
          '1. 7. 2017', '1. 11. 2016', '1. 1. 2017', '1. 3. 2017'],
         ['1. 7. 2016', '1', '', '',
          '1. 7. 2017', '1. 11. 2016', '1. 1. 2017', '1. 3. 2017'],
         ['01.07.2016', '1', '', '',
          '1. 7. 2017', '1. 11. 2016', '1. 1. 2017', '1. 3. 2017'],
         ['12.7.2011', '11', '5', '16',
          '28. 12. 2022', '7. 5. 2015', '4. 4. 2017', '4. 3. 2019'],
         ['7.7.2011', '', '1', '',
          '7. 8. 2011', '17. 7. 2011', '22. 7. 2011', '27. 7. 2011'],
     ]

ee = [
         ['1.7.2016', '', '', ''],
         ['XXX', '1', '', ''],
         ['1.7.2016', 'XXX', '', ''],
         ['1.7.2016', '', 'XXX', ''],
         ['1.7.2016', '', '', 'XXX'],
         ['1.7.2016', '1', 'XXX', ''],
         ['1.7.2016', '0', '', ''],
         ['1.7.2016', '-1', '', ''],
     ]
       
class TestViews(SimpleTestCase):

    def test_main(self):
        res = self.client.get('/dvt')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dvt/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'dvt_main.html')
        for p in pp:
            res = self.client.post(
                '/dvt/',
                {'beg_date': p[0],
                 'years': p[1],
                 'months': p[2],
                 'days': p[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'dvt_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            l = len(msg)
            self.assertEqual(l, 4)
            self.assertEqual(msg[0].text, 'Trest skončí: ' + p[4])
            self.assertEqual(msg[1].text, 'Třetina trestu: ' + p[5])
            self.assertEqual(msg[2].text, 'Polovina trestu: ' + p[6])
            self.assertEqual(msg[3].text, 'Dvě třetiny trestu: ' + p[7])
        for p in ee:
            res = self.client.post(
                '/dvt/',
                {'beg_date': p[0],
                 'years': p[1],
                 'months': p[2],
                 'days': p[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'dvt_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            self.assertEqual(msg[0].text, 'Chybné zadání')
