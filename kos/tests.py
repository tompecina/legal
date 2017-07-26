# -*- coding: utf-8 -*-
#
# kos/tests.py
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
from django.test import SimpleTestCase
from kos import forms


class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm(
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
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'netincome': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'netincome': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'netincome2': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'netincome2': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'deps': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'deps': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'deps2': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'deps2': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'subs': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'subs': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'apt': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'apt': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'fee': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'fee': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'fee2': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'fee2': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'exp': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'exp': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'exp2': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'exp2': ['Toto pole je třeba vyplnit.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'vatrate': ['Hodnota musí být větší nebo rovna 0.']})
        f = forms.MainForm(
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
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors,
            {'vatrate': ['Toto pole je třeba vyplnit.']})


pp = [
    ['0', '0',
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
     '0'],
    ['0', '0',
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
     '0'],
    ['10000', '0',
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
     '2.000.000'],
    ['10000', '10000',
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
     '4.000.000'],
    ['10000', '0',
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
     '329.200'],
    ['10000', '0',
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
     '291.400'],
    ['10000', '12000',
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
     '603.200'],
    ['10000', '12000',
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
     '603.200'],
    ['10000', '12000',
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
     '546.500'],
    ['17000', '0',
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
     '1.019.400'],
    ['17000', '0',
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
     '1.019.400'],
    ['17000', '23000',
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
     '1.504.900'],
]


class TestViews(SimpleTestCase):

    def test_mainpage(self):
        res = self.client.get('/kos')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/kos/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'kos_mainpage.html')
        res = self.client.post('/kos/', {'submit_single': 'Vypočítat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'kos_mainpage.html')
        self.assertEqual(res.context['messages'], [['Chybné zadání', None]])
        for p in pp:
            q = {'netincome': p[0],
                 'netincome2': p[1],
                 'deps': p[3],
                 'deps2': p[4],
                 'subs': p[5],
                 'apt': p[6],
                 'fee': p[7],
                 'fee2': p[8],
                 'exp': p[9],
                 'exp2': p[10],
                 'vatrate': p[12]}
            if p[2]:
                q['partner'] = 'on'
            if p[11]:
                q['vat'] = 'on'
            q['submit_{}'.format('dual' if p[13] else 'single')] = 'Vypočítat'
            res = self.client.post('/kos/', q)
            c = res.context['messages']
            self.assertEqual(
                c[0][0],
                ('Kalkulace pro společný návrh manželů' \
                 if p[13] else 'Kalkulace pro samostatného dlužníka'))
            l = (8 if p[13] else 7)
            for i in range(l):
                self.assertEqual(c[i + 1][0].split()[-2], p[i + 14])
            self.assertEqual(c[-1][0].split()[-2], p[-1])
