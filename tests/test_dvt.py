# -*- coding: utf-8 -*-
#
# tests/test_dvt.py
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

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from tests.utils import check_html
from dvt import forms


class TestForms(SimpleTestCase):

    def test_main_form(self):

        form = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '',
             'days': ''})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '10',
             'months': '',
             'days': ''})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '10',
             'days': ''})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'beg_date': '6.7.2016',
             'years': '',
             'months': '',
             'days': '10'})
        self.assertTrue(form.is_valid())


class TestViews(SimpleTestCase):

    def test_main(self):

        cases = (
            ('1.7.2016', '1', '', '', '01.07.2017', '01.11.2016', '01.01.2017', '01.03.2017'),
            ('1. 7. 2016', '1', '', '', '01.07.2017', '01.11.2016', '01.01.2017', '01.03.2017'),
            ('01.07.2016', '1', '', '', '01.07.2017', '01.11.2016', '01.01.2017', '01.03.2017'),
            ('12.7.2011', '11', '5', '16', '28.12.2022', '07.05.2015', '04.04.2017', '04.03.2019'),
            ('7.7.2011', '', '1', '', '07.08.2011', '17.07.2011', '22.07.2011', '27.07.2011'),
        )

        err_cases = (
            ('1.7.2016', '', '', ''),
            ('XXX', '1', '', ''),
            ('1.7.2016', 'XXX', '', ''),
            ('1.7.2016', '', 'XXX', ''),
            ('1.7.2016', '', '', 'XXX'),
            ('1.7.2016', '1', 'XXX', ''),
            ('1.7.2016', '0', '', ''),
            ('1.7.2016', '-1', '', ''),
        )

        res = self.client.get('/dvt')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/dvt/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'dvt_main.html')
        check_html(self, res.content)

        num = 1
        for test in cases:
            res = self.client.post(
                '/dvt/',
                {'beg_date': test[0],
                 'years': test[1],
                 'months': test[2],
                 'days': test[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'dvt_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            self.assertEqual(len(msg), 4)
            self.assertEqual(msg[0].text, 'Trest skončí: {}'.format(test[4]))
            self.assertEqual(msg[1].text, 'Třetina trestu: {}'.format(test[5]))
            self.assertEqual(msg[2].text, 'Polovina trestu: {}'.format(test[6]))
            self.assertEqual(msg[3].text, 'Dvě třetiny trestu: {}'.format(test[7]))
            check_html(self, res.content, key=num)
            num += 1

        num = 1
        for test in err_cases:
            res = self.client.post(
                '/dvt/',
                {'beg_date': test[0],
                 'years': test[1],
                 'months': test[2],
                 'days': test[3]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'dvt_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            self.assertEqual(msg[0].text, 'Chybné zadání')
            check_html(self, res.content, key=num)
            num += 1
