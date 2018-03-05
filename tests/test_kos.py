# -*- coding: utf-8 -*-
#
# tests/test_kos.py
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

from django.test import SimpleTestCase, TestCase

from legal.settings import FULL_CONTENT_TYPE
from legal.kos import forms

from tests.utils import check_html


class TestForms(SimpleTestCase):

    def test_main_form(self):

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'netincome': '-1',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'netincome': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'netincome': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '-1',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'netincome2': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'netincome2': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '-1',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'deps': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'deps': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '-1',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'deps2': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'deps2': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '-1',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'subs': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'subs': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '-1',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'apt': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'apt': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '-1',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'fee': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'fee': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '-1',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'fee2': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'fee2': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '-1',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'exp': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp2': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'exp': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '-1',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'exp2': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'vatrate': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'exp2': ['Toto pole je třeba vyplnit.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0',
             'vatrate': '-1'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'vatrate': ['Hodnota musí být větší nebo rovna 0.']})

        form = forms.MainForm(
            {'netincome': '0',
             'netincome2': '0',
             'deps': '0',
             'deps2': '0',
             'subs': '0',
             'apt': '0',
             'fee': '0',
             'fee2': '0',
             'exp': '0',
             'exp2': '0'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'vatrate': ['Toto pole je třeba vyplnit.']})


class TestViews(TestCase):

    fixtures = ('kos_test.json',)

    def test_mainpage(self):

        cases = (
            ('0', '0',
             False,
             '0', '0',
             '0',
             '0',
             '0', '0',
             '0', '0',
             False,
             '0,0',
             False,
             '0', '0',
             '0', '0', '0', '0', '0',
             '0'),
            ('0', '0',
             False,
             '0', '0',
             '0',
             '0',
             '0', '0',
             '0', '0',
             False,
             '0,0',
             True,
             '0', '0', '0',
             '0', '0', '0', '0', '0',
             '0'),
            ('10000', '0',
             False,
             '0', '0',
             '0',
             '0',
             '0', '0',
             '0', '0',
             False,
             '0,0',
             False,
             '0', '0',
             '10.000', '0', '0', '10.000', '600.000',
             '2.000.000'),
            ('10000', '10000',
             False,
             '0', '0',
             '0',
             '0',
             '0', '0',
             '0', '0',
             False,
             '0,0',
             True,
             '0', '0', '0',
             '20.000', '0', '0', '20.000', '1.200.000',
             '4.000.000'),
            ('10000', '0',
             False,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             False,
             '21,0',
             False,
             '6.179', '6.179',
             '2.546', '7.454', '900', '1.646', '98.760',
             '329.200'),
            ('10000', '0',
             False,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             True,
             '21,0',
             False,
             '6.179', '6.179',
             '2.546', '7.454', '1.089', '1.457', '87.420',
             '291.400'),
            ('10000', '12000',
             False,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             False,
             '21,0',
             True,
             '6.179', '7.724', '7.724',
             '4.366', '17.634', '1.350', '3.016', '180.960',
             '603.200'),
            ('10000', '12000',
             True,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             False,
             '21,0',
             True,
             '6.179', '7.724', '7.724',
             '4.366', '17.634', '1.350', '3.016', '180.960',
             '603.200'),
            ('10000', '12000',
             False,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             True,
             '21,0',
             True,
             '6.179', '7.724', '7.724',
             '4.366', '17.634', '1.634', '2.732', '163.950',
             '546.500'),
            ('17000', '0',
             True,
             '0', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             True,
             '21,0',
             False,
             '6.179', '7.724',
             '6.186', '10.814', '1.089', '5.097', '305.820',
             '1.019.400'),
            ('17000', '0',
             False,
             '1', '0',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             True,
             '21,0',
             False,
             '6.179', '7.724',
             '6.186', '10.814', '1.089', '5.097', '305.820',
             '1.019.400'),
            ('17000', '23000',
             False,
             '2', '5',
             '3410',
             '5858',
             '750', '1125',
             '150', '225',
             True,
             '21,0',
             True,
             '6.179', '10.813', '15.447',
             '9.158', '30.842', '1.634', '7.524', '451.470',
             '1.504.900'),
        )

        res = self.client.get('/kos')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/kos/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'kos_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post('/kos/', {'submit_single': 'Vypočítat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'kos_mainpage.xhtml')
        self.assertEqual(res.context['messages'], [('Chybné zadání', None)])
        check_html(self, res.content)

        num = 1
        for test in cases:
            query = {
                'netincome': test[0],
                'netincome2': test[1],
                'deps': test[3],
                'deps2': test[4],
                'subs': test[5],
                'apt': test[6],
                'fee': test[7],
                'fee2': test[8],
                'exp': test[9],
                'exp2': test[10],
                'vatrate': test[12],
            }
            if test[2]:
                query['partner'] = 'on'
            if test[11]:
                query['vat'] = 'on'
            query['submit_{}'.format('dual' if test[13] else 'single')] = 'Vypočítat'
            res = self.client.post('/kos/', query)
            con = res.context['messages']
            self.assertEqual(
                con[0][0],
                'Kalkulace pro společný návrh manželů' if test[13] else 'Kalkulace pro samostatného dlužníka')
            lines = 8 if test[13] else 7
            for idx in range(lines):
                self.assertEqual(con[idx + 1][0].split()[-2], test[idx + 14])
            self.assertEqual(con[-1][0].split()[-2], test[-1])
            check_html(self, res.content, key=num)
            num += 1
