# -*- coding: utf-8 -*-
#
# knr/tests.py
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
from copy import copy
from io import BytesIO
from os.path import join
from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from common.settings import BASE_DIR
from common.utils import newXML, p2c, xmlbool
from common.tests import TEST_STRING, stripxml
from cache.tests import DummyRequest
from knr import forms, models, views, utils


APP = __package__

TEST_DIR = join(BASE_DIR, APP, 'testdata')


class TestForms(SimpleTestCase):

    def test_CalcForm(self):
        f = forms.CalcForm({})
        self.assertFalse(f.is_valid())
        f = forms.CalcForm({'vat_rate': '21'})
        self.assertTrue(f.is_valid())
        f = forms.CalcForm({'vat_rate': '21',
                            'calculation_note': 'c\rn',
                            'internal_note': 'i\rn'})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['calculation_note'], 'cn')
        self.assertEqual(f.cleaned_data['internal_note'], 'in')

    def test_ServiceForm(self):
        f = forms.ServiceForm({})
        self.assertFalse(f.is_valid())
        s = {'idx': '1',
             'description': 'Popis',
             'major_number': '1',
             'rate': '1500',
             'minor_number': '2',
             'multiple_number': '1',
             'numerator': '2',
             'denominator': '3'}
        f = forms.ServiceForm(s)
        self.assertTrue(f.is_valid())
        d = copy(s)
        for t in ['off10_flag', 'off30_flag', 'off30limit5000_flag',
            'off20limit5000_flag']:
            d[t] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['off10_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['off30_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['off30limit5000_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['off20limit5000_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        for t in ['off30_flag', 'off30limit5000_flag', 'off20limit5000_flag']:
            d[t] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        for t in ['off10_flag', 'off30limit5000_flag', 'off20limit5000_flag']:
            d[t] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['off10_flag'] = d['off30_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())

    def test_FlatForm(self):
        f = forms.FlatForm({})
        self.assertFalse(f.is_valid())
        s = {'idx': '1',
             'description': 'Popis',
             'rate': '1500',
             'numerator': '2',
             'denominator': '3'}
        f = forms.FlatForm(s)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['halved_flag'] = d['halved_appeal_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['halved_appeal_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['halved_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['multiple_flag'] = d['multiple50_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['multiple50_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['multiple_flag'] = 'on'
        f = forms.FlatForm(d)
        self.assertTrue(f.is_valid())


class TestModels(SimpleTestCase):

    def test_models(self):
        self.assertEqual(
            str(models.Place(
                uid_id=1,
                abbr='test_abbr',
                name='test_name',
                addr='test_addr',
                lat=50,
                lon=15)),
            'test_abbr')
        self.assertEqual(
            str(models.Car(
                uid_id=1,
                abbr='test_abbr',
                name='test_name',
                fuel='test_fuel',
                cons1=8,
                cons2=9,
                cons3=10)),
            'test_abbr')
        formula = models.Formula(
            uid_id=1,
            abbr='test_abbr',
            name='test_name',
            flat=3.70)
        self.assertEqual(
            str(formula),
            'test_abbr')
        self.assertEqual(
            str(models.Rate(
                formula=formula,
                fuel='test_fuel',
                rate=34.90)),
            'test_abbr/test_fuel')


class T(views.Calculation, views.Item):

    pass


class TestUtils(TestCase):

    fixtures = ['knr_test.json']

    def test_getVAT(self):
        self.assertAlmostEqual(utils.getVAT(), 25)


class TestViews1(SimpleTestCase):

    def test_convi(self):
        self.assertEqual(views.convi(0), '0')
        self.assertEqual(views.convi(1), '1')
        self.assertEqual(views.convi(-1), '-1')
        self.assertEqual(views.convi(1.4), '1')
        self.assertEqual(views.convi(-1.4), '-1')
        self.assertEqual(views.convi(1.689), '1')
        self.assertEqual(views.convi(-1.689), '-1')
        self.assertEqual(views.convi(537), '537')
        self.assertEqual(views.convi(-537), '-537')
        self.assertEqual(views.convi(1537), '1.537')
        self.assertEqual(views.convi(-1537), '-1.537')
        self.assertEqual(views.convi(68562515458), '68.562.515.458')
        self.assertEqual(views.convi(-68562515458), '-68.562.515.458')
        self.assertEqual(views.convi(68562515458.716), '68.562.515.458')
        self.assertEqual(views.convi(-68562515458.716), '-68.562.515.458')
        self.assertEqual(views.convi(968562515458.716), '968.562.515.458')
        self.assertEqual(views.convi(-968562515458.716), '-968.562.515.458')

    def test_convf(self):
        self.assertEqual(views.convf(5458.7101589, 0), '5459')
        self.assertEqual(views.convf(5458.7101589, 1), '5458,7')
        self.assertEqual(views.convf(5458.7101589, 2), '5458,71')
        self.assertEqual(views.convf(5458.7101589, 3), '5458,710')
        self.assertEqual(views.convf(5458.7101589, 4), '5458,7102')
        self.assertEqual(views.convf(5458.7101589, 5), '5458,71016')
        self.assertEqual(views.convf(5458.7101589, 6), '5458,710159')
        self.assertEqual(views.convf(5458.7101589, 7), '5458,7101589')
        self.assertEqual(views.convf(-5458.7101589, 0), '-5459')
        self.assertEqual(views.convf(-5458.7101589, 1), '-5458,7')
        self.assertEqual(views.convf(-5458.7101589, 2), '-5458,71')
        self.assertEqual(views.convf(-5458.7101589, 3), '-5458,710')
        self.assertEqual(views.convf(-5458.7101589, 4), '-5458,7102')
        self.assertEqual(views.convf(-5458.7101589, 5), '-5458,71016')
        self.assertEqual(views.convf(-5458.7101589, 6), '-5458,710159')
        self.assertEqual(views.convf(-5458.7101589, 7), '-5458,7101589')

    def dcomp(self, f, d1, d2):
        for n in f:
            if views.gd[n][0] == 'F':
                self.assertAlmostEqual(d1[n], d2[n])
            else:
                self.assertEqual(d1[n], d2[n])

    def test_conv(self):
        d = {'title': TEST_STRING,
             'calculation_note': 'cn',
             'internal_note': 'in',
             'vat_rate': 26.50,
             'type': 'Typ',
             'description': 'Popis',
             'amount': 50,
             'vat': True,
             'item_note': 'itn',
             'major_number': 5,
             'rate': 450,
             'minor_number': 4,
             'multiple_number': 2,
             'multiple_flag': True,
             'multiple50_flag': True,
             'single_flag': True,
             'halved_flag': True,
             'halved_appeal_flag': True,
             'collection_flag': True,
             'off10_flag': True,
             'off30_flag': True,
             'off30limit5000_flag': True,
             'off20limit5000_flag': True,
             'basis': 6500,
             'number': 16,
             'from_name': 'Z jméno',
             'from_address': 'Z adresa',
             'from_lat': 50.1234567,
             'from_lon': 15.1234567,
             'to_name': 'Do jméno',
             'to_address': 'Do adresa',
             'to_lat': 51.1234567,
             'to_lon': 16.1234567,
             'trip_number': 2,
             'trip_distance': 45,
             'time_rate': 250,
             'time_number': 8,
             'car_name': 'Vozidlo',
             'fuel_name': 'NM',
             'cons1': 5.1,
             'cons2': 6.1,
             'cons3': 7.1,
             'formula_name': 'Předpis',
             'flat_rate': 4.12,
             'fuel_price': 14.12}
        f = d.keys()
        o = T()
        views.d2i(f, d, o)
        e = {}
        views.i2d(f, o, e)
        self.dcomp(f, d, e)
        g = {n: str(d[n]) for n in f}
        o = T()
        views.d2i(g, d, o)
        h = {}
        views.i2d(f, o, h)
        self.dcomp(f, d, h)
        k = {}
        views.d2d(f, d, k)
        self.dcomp(f, d, k)
        s = '<?xml version="1.0" encoding="utf-8"?><calculation>'
        for n in f:
            if views.gd[n] == views.B:
                x = xmlbool(d[n])
            else:
                x = str(d[n])
            s += '<{0}>{1}</{0}>'.format(n, x)
        s += '</calculation>'
        o = T()
        views.s2i(f, BeautifulSoup(s, 'xml'), o)
        l = {}
        views.d2d(f, d, l)
        self.dcomp(f, d, l)

    def test_d2d(self):
        v = {}
        views.d2d(['amount'], {'amount': 'XXX'}, v)
        self.assertEqual(v, {'amount': 'XXX'})
        v = {}
        views.d2d(['vat_rate'], {'vat_rate': 'XXX'}, v)
        self.assertEqual(v, {'vat_rate': 'XXX'})

    def test_s2i(self):
        s = newXML(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<vat_rate>22.0</vat_rate>\n')
        c = views.Calculation()
        views.s2i(['vat_rate'], s, c)
        self.assertAlmostEqual(c.vat_rate, 22)
        s = newXML(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<vat_rate>XXX</vat_rate>\n')
        c = views.Calculation()
        o = c.vat_rate
        views.s2i(['vat_rate'], s, c)
        self.assertAlmostEqual(c.vat_rate, o)

    def test_xml(self):
        i = 1
        while True:
            try:
                with open('{}/knr/testdata/calc{:d}.xml'
                    .format(BASE_DIR, i), 'rb') as fi:
                    d = fi.read()
            except:
                self.assertGreater(i, 1)
                break
            c = views.fromxml(d)
            self.assertIsNone(c[1])
            self.assertIs(type(c[0]), views.Calculation)
            e = views.toxml(c[0])
            self.assertXMLEqual(stripxml(d), stripxml(e))
            i += 1
        i = 1
        while True:
            try:
                with open('{}/knr/testdata/err_calc{:d}.xml'
                    .format(BASE_DIR, i), 'rb') as fi:
                    d = fi.read()
            except:
                self.assertGreater(i, 1)
                break
            c, m = views.fromxml(d)
            self.assertTrue(m)
            i += 1


class TestViews2(TestCase):

    fixtures = ['knr_test.json']

    def setUp(self):
        User.objects.create_user('user', 'user@pecina.cz', 'none')
        User.objects.create_superuser('superuser', 'suser@pecina.cz', 'none')
        User.objects.create_user('anotheruser', 'auser@pecina.cz', 'none')
        self.user = User.objects.get(username='user').pk
        models.Place.objects.exclude(uid=None).update(uid=self.user)
        models.Car.objects.all().update(uid=self.user)
        models.Formula.objects.exclude(uid=None).update(uid=self.user)

    def tearDown(self):
        self.client.logout()

    def test_findloc(self):
        r = views.findloc('Melantrichova 504/5, Praha 1')
        self.assertEqual(
            r[0],
            'Melantrichova 504/5, 110 00 Praha 1-Staré Město, Česká republika')
        self.assertAlmostEqual(r[1], 51.0852574)
        self.assertAlmostEqual(r[2], 13.4211651)
        self.assertFalse(views.findloc(''))
        self.assertFalse(views.findloc('XXX'))
        self.assertFalse(views.findloc('Melantrichova 504/6, Praha 1'))

    def test_finddist(self):
        r = views.finddist(50, 15, 51, 16)
        self.assertEqual(r, (182046, 20265))
        self.assertEqual(views.finddist(50, 15, 51, 17), (False, False))
        self.assertEqual(views.finddist(50, 15, 51, 18), (False, False))
        self.assertEqual(views.finddist(50, 15, 51, 19), (False, False))

    def test_main(self):
        res = self.client.get('/knr')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        res = self.client.post(
            '/knr/',
            {'vat_rate': '21,00',
             'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        res = self.client.post(
            '/knr/',
            {'vat_rate': '21,00',
             'submit_edit': 'Upravit položky'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/',
            {'submit_empty': 'Vyprázdnit kalkulaci'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        res = self.client.post(
            '/knr/',
            {'title': 'test',
             'calculation_note': 'cn',
             'internal_note': 'in',
             'submit_empty': 'Vyprázdnit kalkulaci'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('#id_title')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0]['value'], '')
        calculation_note = soup.select('#id_calculation_note')
        self.assertEqual(len(calculation_note), 1)
        self.assertEqual(calculation_note[0].text, '')
        internal_note = soup.select('#id_internal_note')
        self.assertEqual(len(internal_note), 1)
        self.assertEqual(internal_note[0].text, '')
        vat_rate = soup.select('#id_vat_rate')
        self.assertEqual(len(vat_rate), 1)
        self.assertEqual(vat_rate[0]['value'], '25,00')
        for suffix in [['xml', 'Uložit kalkulaci', 'text/xml; charset=utf-8'],
                       ['pdf', 'Export do PDF', 'application/pdf']]:
            with open(join(TEST_DIR, 'calc1.' + suffix[0]), 'rb') as fi:
                res = self.client.post(
                    '/knr/',
                    {'submit_load': 'Načíst kalkulaci',
                     'load': fi},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], TEST_STRING)
            calculation_note = soup.select('#id_calculation_note')
            self.assertEqual(len(calculation_note), 1)
            self.assertEqual(calculation_note[0].text, 'Poznámka')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'Interní poznámka')
            vat_rate = soup.select('#id_vat_rate')
            self.assertEqual(len(vat_rate), 1)
            self.assertEqual(vat_rate[0]['value'], '21,00')
            res = self.client.post(
                '/knr/',
                {'vat_rate': '21,00',
                 'title': TEST_STRING,
                 'calculation_note': 'cn',
                 'internal_note': 'in',
                 'submit_' + suffix[0]: suffix[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suffix[2])
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post(
                '/knr/',
                {'submit_load': 'Načíst kalkulaci',
                 'load': con}, follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], TEST_STRING)
            calculation_note = soup.select('#id_calculation_note')
            self.assertEqual(len(calculation_note), 1)
            self.assertEqual(calculation_note[0].text, 'cn')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'in')
            vat_rate = soup.select('#id_vat_rate')
            self.assertEqual(len(vat_rate), 1)
            self.assertEqual(vat_rate[0]['value'], '21,00')
        for b in [['place', 'místa'],
                  ['car', 'vozidla'],
                  ['formula', 'předpisy']]:
            res = self.client.post(
                '/knr/',
                {'vat_rate': '21,00',
                 'submit_' + b[0]:
                 'Upravit ' + b[1]},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_{}list.html'.format(b[0]))
        res = self.client.post(
            '/knr/',
            {'vat_rate': '22,00',
             'submit_load': 'Načíst',
             'load': None},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Nejprve zvolte soubor k načtení')
        with open(join(TEST_DIR, 'err_calc1.xml'), 'rb') as fi:
            res = self.client.post(
                '/knr/',
                {'submit_load': 'Načíst kalkulaci',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybný formát souboru')
        i = 1
        while True:
            try:
                fi = open('{}/knr/testdata/calc{:d}.xml'
                    .format(BASE_DIR, i), 'rb')
            except:
                self.assertGreater(i, 1)
                break
            res = self.client.post(
                '/knr/',
                {'vat_rate': '26',
                 'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
            fi.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            res = self.client.post(
                '/knr/',
                {'title': res.context['title'],
                 'calculation_note': res.context['calculation_note'],
                 'internal_note': res.context['internal_note'],
                 'vat_rate': p2c(str(res.context['vat_rate'])),
                 'submit_pdf': 'Export do PDF'})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], 'application/pdf')
            i += 1
        res = self.client.post(
            '/knr/',
            {'vat_rate': 'XXX',
             'submit_update': 'Aktualisovat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        self.assertEqual(res.context['errors'], True)

    def test_itemlist(self):
        res = self.client.get('/knr/itemlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/itemlist/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/itemlist/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/itemlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1 + p')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, '(nejsou zadány žádné položky)')
        pre = soup.select('#id_new')[0].select('option')
        self.assertEqual(len(pre), 23)
        for val in [p['value'] for p in pre if p['value']]:
            res = self.client.post(
                '/knr/itemform/',
                {'presel': val,
                 'submit_new': 'Přidat položku:'})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_itemform.html')
        res = self.client.post(
            '/knr/itemform/',
            {'submit_new': 'Přidat položku:'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')

    def test_list(self):
        models.Place.objects.all().delete()
        models.Car.objects.all().delete()
        models.Formula.objects.all().delete()
        for b in [['place', 'zadána žádná místa'],
                  ['car', 'zadána žádná vozidla'],
                  ['formula', 'zadány žádné předpisy']]:
            res = self.client.get('/knr/{}list'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/knr/{}list/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/knr/{}list/'.format(b[0]), follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/knr/{}list/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_{}list.html'.format(b[0]))
            soup = BeautifulSoup(res.content, 'html.parser')
            p = soup.select('h1 + p')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, '(nejsou {})'.format(b[1]))
            self.client.logout()

    def test_form(self):
        for b in [['place', 'Nové místo'],
                  ['car', 'Nové vozidlo'],
                  ['formula', 'Nový předpis']]:
            res = self.client.get('/knr/{}form'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/knr/{}form/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/knr/{}form/'.format(b[0]), follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/knr/{}form/'.format(b[0]))
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_{}form.html'.format(b[0]))
            soup = BeautifulSoup(res.content, 'html.parser')
            p = soup.select('h1')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, b[1])
            self.client.logout()

    def test_place(self):
        res = self.client.get('/knr/placeform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/placeform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/placeform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/placeform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_placeform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nové místo')
        res = self.client.post(
            '/knr/placeform/',
            {'addr': 'Melantrichova 504/5, Praha 1',
             'submit_search': 'Vyhledat'})
        self.assertAlmostEqual(res.context['f']['lat'].value(), 51.0852574)
        self.assertAlmostEqual(res.context['f']['lon'].value(), 13.4211651)
        res = self.client.post(
            '/knr/placeform/',
            {'addr': 'Melantrichova 504/7, Praha 1',
             'submit_search': 'Vyhledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placeform.html')
        self.assertEqual(
            res.context['err_message'],
            'Hledání neúspěšné, prosím, upřesněte adresu')
        res = self.client.post(
            '/knr/placeform/',
            {'abbr': 'test_abbr1',
             'name': TEST_STRING,
             'addr': 'test_addr1',
             'lat': '50',
             'lon': '15',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placelist.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        pk = soup.select('table.list a')[1]['href'].split('/')[-2]
        res = self.client.post(
            '/knr/placeform/',
            {'abbr': 'test_abbr2',
             'name': TEST_STRING,
             'addr': 'test_addr2',
             'lat': '50',
             'lon': '15',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placelist.html')
        res = self.client.post(
            '/knr/placeform/',
            {'abbr': 'test_abbr3',
             'name': TEST_STRING,
             'addr': 'test_addr3',
             'lat': 'XXX',
             'lon': '15',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placeform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/knr/placeform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placelist.html')
        res = self.client.get('/knr/placeform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/placeform/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_placeform.html')
        res = self.client.post(
            '/knr/placeform/{}/'.format(pk),
            {'abbr': 'test_abbr4',
             'name': TEST_STRING,
             'addr': 'test_addr4',
             'lat': '50',
             'lon': '15',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placelist.html')
        res = self.client.post(
            '/knr/placeform/100/',
            {'abbr': 'test_abbr5',
             'name': TEST_STRING,
             'addr': 'test_addr5',
             'lat': '50',
             'lon': '15',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/placedel/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placedel.html')
        res = self.client.post(
            '/knr/placedel/{}/'.format(pk),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placelist.html')
        res = self.client.post(
            '/knr/placedel/{}/'.format(pk),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_placedeleted.html')
        res = self.client.post('/knr/placedel/{}/'.format(pk), follow=True)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_car(self):
        res = self.client.get('/knr/carform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/carform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/carform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/carform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_carform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nové vozidlo')
        res = self.client.post(
            '/knr/carform/',
            {'abbr': 'test_abbr1',
             'name': TEST_STRING,
             'fuel': 'NM',
             'cons1': '5,0',
             'cons2': '8,5',
             'cons3': '9,7',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carlist.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        pk = soup.select('table.list a')[1]['href'].split('/')[-2]
        res = self.client.post(
            '/knr/carform/',
            {'abbr': 'test_abbr2',
             'name': TEST_STRING,
             'fuel': 'NM',
             'cons1': '5,0',
             'cons2': '8,5',
             'cons3': '9,7',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carlist.html')
        res = self.client.post(
            '/knr/carform/',
            {'abbr': 'test_abbr3',
             'name': TEST_STRING,
             'fuel': 'NM',
             'cons1': '5,0',
             'cons2': 'XXX',
             'cons3': '9,7',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/knr/carform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carlist.html')
        res = self.client.get('/knr/carform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/carform/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_carform.html')
        res = self.client.post(
            '/knr/carform/{}/'.format(pk),
            {'abbr': 'test_abbr4',
             'name': TEST_STRING,
             'fuel': 'NM',
             'cons1': '5,0',
             'cons2': '8,5',
             'cons3': '9,7',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carlist.html')
        res = self.client.post(
            '/knr/carform/100/',
            {'abbr': 'test_abbr5',
             'name': TEST_STRING,
             'fuel': 'NM',
             'cons1': '5,0',
             'cons2': '8,5',
             'cons3': '9,7',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/cardel/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_cardel.html')
        res = self.client.post(
            '/knr/cardel/{}/'.format(pk),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_carlist.html')
        res = self.client.post(
            '/knr/cardel/{}/'.format(pk),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_cardeleted.html')
        res = self.client.post('/knr/cardel/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_formula(self):
        res = self.client.get('/knr/formulaform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/formulaform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/formulaform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/formulaform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_formulaform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový předpis')
        res = self.client.post(
            '/knr/formulaform/',
            {'abbr': 'test_abbr1',
             'name': TEST_STRING,
             'flat': '34,50',
             'rate_NM': '27,80',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulalist.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        pk = soup.select('table.list a')[1]['href'].split('/')[-2]
        res = self.client.post(
            '/knr/formulaform/',
            {'abbr': 'test_abbr2',
             'name': TEST_STRING,
             'flat': '34,50',
             'rate_NM': '27,80',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulalist.html')
        res = self.client.post(
            '/knr/formulaform/',
            {'abbr': 'test_abbr2',
             'name': TEST_STRING,
             'flat': 'XXX',
             'rate_NM': '27,80',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulaform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/knr/formulaform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulalist.html')
        res = self.client.get('/knr/formulaform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/formulaform/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_formulaform.html')
        res = self.client.post(
            '/knr/formulaform/{}/'.format(pk),
            {'abbr': 'test_abbr4',
             'name': TEST_STRING,
             'flat': '34,50',
             'rate_NM': '27,80',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulalist.html')
        res = self.client.post(
            '/knr/formulaform/100/',
            {'abbr': 'test_abbr5',
             'name': TEST_STRING,
             'flat': '34,50',
             'rate_NM': '27,80',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/formuladel/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formuladel.html')
        res = self.client.post(
            '/knr/formuladel/{}/'.format(pk),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formulalist.html')
        res = self.client.post(
            '/knr/formuladel/{}/'.format(pk),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_formuladeleted.html')
        res = self.client.post('/knr/formuladel/{}/'.format(pk))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_item(self):
        res = self.client.get('/knr/itemform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/itemform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/itemform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/itemform/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'general',
             'submit': 'new'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['page_title'], 'Nová položka')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'description': 'Description 1',
             'rate': '1000',
             'major_number': '8',
             'minor_number': '2',
             'multiple_number': '1',
             'off10_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'description': 'Description 2',
             'rate': '5400',
             'major_number': '1',
             'minor_number': '0',
             'multiple_number': '2',
             'off30_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '300',
             'major_number': '0',
             'minor_number': '1',
             'multiple_number': '1',
             'off30limit5000_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '300',
             'major_number': '0',
             'minor_number': '1',
             'multiple_number': '1',
             'off20limit5000_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        pp = [[[500, 250],
               [1000, 500],
               [5000, 750],
               [10000, 1000],
               [200000, 5750],
               [10000000, 30250],
               [20000000, 32750],
              ],
              [[500, 300],
               [1000, 500],
               [5000, 1000],
               [10000, 1500],
               [200000, 9100],
               [10000000, 48300],
               [20000000, 52300],
              ]]
        for i in [1, 2]:
            for p, r in pp[i - 1]:
                res = self.client.post(
                    '/knr/itemform/',
                    {'type': 'service',
                     'idx': '0',
                     'basis': str(p),
                     'numerator': '2',
                     'denominator': '3',
                     'submit_calc{:d}'.format(i): 'on'},
                    follow=True)
                self.assertEqual(res.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(res, 'knr_itemform.html')
                self.assertFalse(res.context['errors'])
                self.assertEqual(res.context['rate'], r)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '1',
             'basis': '2000',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertFalse(res.context['errors'])
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'service',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '-1000',
             'major_number': '8',
             'minor_number': '2',
             'multiple_number': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '1000',
             'multiple_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '5400',
             'multiple50_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '300',
             'single_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '2600',
             'halved_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '800',
             'halved_appeal_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '1900',
             'collection_flag': 'on',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        pp = [[[500, 1500],
               [1000, 3000],
               [5000, 4500],
               [10000, 6000],
               [200000, 34500],
               [10000000, 181500],
               [20000000, 183000],
              ],
              [[1000, 4500],
               [5000, 6000],
               [10000, 9000],
               [200000, 41300],
               [10000000, 237300],
               [20000000, 252300],
              ],
              [[100, 1000],
               [500, 1500],
               [1000, 2500],
               [2000, 3750],
               [5000, 4800],
               [10000, 7500],
               [200000, 39800],
               [10000000, 235800],
               [20000000, 250800],
              ]]
        for i in range(1, 4):
            for p, r in pp[i - 1]:
                res = self.client.post(
                    '/knr/itemform/',
                    {'type': 'flat',
                     'idx': '0',
                     'basis': str(p),
                     'numerator': '2',
                     'denominator': '3',
                     'submit_calc{:d}'.format(i): 'on'},
                    follow=True)
                self.assertEqual(res.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(res, 'knr_itemform.html')
                self.assertFalse(res.context['errors'])
                self.assertEqual(res.context['rate'], r)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '1',
             'basis': '2000',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertFalse(res.context['errors'])
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '-1000',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'administrative',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '300',
             'number': '8',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'administrative',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '75',
             'number': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        pp = [75, 300]
        for i in [1, 2]:
            r = pp[i - 1]
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'administrative',
                 'idx': '0',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_calc{:d}'.format(i): 'on'},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_itemform.html')
            self.assertFalse(res.context['errors'])
            self.assertEqual(res.context['rate'], r)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'administrative',
             'idx': '1',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertFalse(res.context['errors'])
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'administrative',
             'idx': '0',
             'description': TEST_STRING,
             'rate': '-100',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '0',
             'description': TEST_STRING,
             'time_rate': '100',
             'time_number': '8',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '0',
             'description': TEST_STRING,
             'time_rate': '50',
             'time_number': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        pp = [50, 100]
        for i in [1, 2]:
            r = pp[i - 1]
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'time',
                 'idx': '0',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_calc{:d}'.format(i): 'on'},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_itemform.html')
            self.assertFalse(res.context['errors'])
            self.assertEqual(res.context['time_rate'], r)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '1',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertFalse(res.context['errors'])
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '0',
             'description': TEST_STRING,
             'time_rate': '-100',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'trip_distance': '180',
             'time_number': '7',
             'time_rate': '100',
             'trip_number': '2',
             'car_name': 'Test car',
             'fuel_name': 'NM',
             'cons1': '5,6',
             'cons2': '7,1',
             'cons3': '8,0',
             'formula_name': 'Test formula',
             'flat_rate': '3,90',
             'fuel_price': '24,50',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'trip_distance': '145',
             'time_number': '1',
             'time_rate': '50',
             'trip_number': '12',
             'car_name': 'Test car',
             'fuel_name': 'NM',
             'cons1': '6,6',
             'cons2': '8,1',
             'cons3': '12,3',
             'formula_name': 'Test formula',
             'flat_rate': '4,90',
             'fuel_price': '34,50',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'trip_distance': '295',
             'time_number': '18',
             'time_rate': '150',
             'trip_number': '2',
             'car_name': 'Test car',
             'fuel_name': 'NM',
             'cons1': '4,6',
             'cons2': '5,1',
             'cons3': '10,3',
             'formula_name': 'Test formula',
             'flat_rate': '5,90',
             'fuel_price': '14,00',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        for t in ['from', 'to']:
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'travel',
                 'idx': '0',
                 '{}_address'.format(t): 'Melantrichova 504/5, Praha 1',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_{}_search'.format(t): 'Vyhledat'})
            self.assertAlmostEqual(res.context['{}_lat'.format(t)], 51.0852574)
            self.assertAlmostEqual(res.context['{}_lon'.format(t)], 13.4211651)
            self.assertIn(
                'Česká republika',
                res.context['{}_address'.format(t)])
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'travel',
                 'idx': '0',
                 '{}_sel'.format(t): '1',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_{}_apply'.format(t): 'Použít'})
            self.assertEqual(res.context['{}_name'.format(t)], 'Test name')
            self.assertEqual(
                res.context['{}_address'.format(t)],
                'Test address')
            self.assertAlmostEqual(res.context['{}_lat'.format(t)], 49.1975999)
            self.assertAlmostEqual(res.context['{}_lon'.format(t)], 16.6044449)
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'travel',
                 'idx': '0',
                 '{}_address'.format(t): 'XXX',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_{}_search'.format(t): 'Vyhledat'})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_itemform.html')
            self.assertEqual(
                res.context['err_message'],
                'Hledání neúspěšné, prosím, upřesněte adresu.')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'from_lat': '50',
             'from_lon': '15',
             'to_lat': '51',
             'to_lon': '16',
             'numerator': '2',
             'denominator': '3',
             'submit_calc': 'Vypočítat'})
        self.assertAlmostEqual(res.context['trip_distance'], 183)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'car_sel': '1',
             'numerator': '2',
             'denominator': '3',
             'submit_car_apply': 'Použít'})
        self.assertEqual(res.context['car_name'], 'Test car')
        self.assertEqual(res.context['fuel_name'], 'BA95')
        self.assertAlmostEqual(res.context['cons1'], 9.0)
        self.assertAlmostEqual(res.context['cons2'], 10.1)
        self.assertAlmostEqual(res.context['cons3'], 8.5)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'formula_sel': '1',
             'fuel_name': 'NM',
             'numerator': '2',
             'denominator': '3',
             'submit_formula_apply': 'Použít'})
        self.assertEqual(res.context['formula_name'], 'Test formula')
        self.assertAlmostEqual(res.context['flat_rate'], 3.70)
        self.assertAlmostEqual(res.context['fuel_price'], 32.00)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'formula_sel': '1',
             'fuel_name': 'BA91',
             'numerator': '2',
             'denominator': '3',
             'submit_formula_apply': 'Použít'})
        self.assertEqual(res.context['formula_name'], 'Test formula')
        self.assertAlmostEqual(res.context['flat_rate'], 3.70)
        self.assertEqual(res.context['fuel_price'], '')
        pp = [50, 100]
        for i in [1, 2]:
            r = pp[i - 1]
            res = self.client.post(
                '/knr/itemform/',
                {'type': 'travel',
                 'idx': '0',
                 'numerator': '2',
                 'denominator': '3',
                 'submit_calc{:d}'.format(i): 'on'},
                follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_itemform.html')
            self.assertFalse(res.context['errors'])
            self.assertEqual(res.context['time_rate'], r)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '1',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertFalse(res.context['errors'])
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'general',
             'numerator': '2',
             'denominator': '3',
             'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.get('/knr/itemform/100/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/itemform/14/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'knr_itemform.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'XXX',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'description': TEST_STRING,
             'from_sel': '1',
             'to_sel': '1',
             'car_sel': '1',
             'formula_sel': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'car_sel': '1',
             'formula_sel': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '1',
             'description': TEST_STRING,
             'from_sel': '1',
             'to_sel': '1',
             'car_sel': '1',
             'formula_sel': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '100',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'trip_distance': '295',
             'time_number': '18',
             'time_rate': '150',
             'trip_number': '2',
             'car_name': 'Test car',
             'fuel_name': 'NM',
             'cons1': '4,6',
             'cons2': '5,1',
             'cons3': '10,3',
             'formula_name': 'Test formula',
             'flat_rate': '5,90',
             'fuel_price': '14,00',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '1',
             'description': TEST_STRING,
             'from_name': 'A',
             'from_address': 'Address A',
             'from_lat': '50',
             'from_lon': '15',
             'to_name': 'B',
             'to_address': 'Address B',
             'to_lat': '51',
             'to_lon': '16',
             'trip_distance': '295',
             'time_number': '18',
             'time_rate': '150',
             'trip_number': '2',
             'car_name': 'Test car',
             'fuel_name': 'NM',
             'cons1': '4,6',
             'cons2': '5,1',
             'cons3': '10,3',
             'formula_name': 'Test formula',
             'flat_rate': '5,90',
             'fuel_price': '14,00',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '0',
             'fuel_price': 'XXX',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        self.assertEqual(res.context['page_title'], 'Nová položka')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'idx': '1',
             'fuel_price': 'XXX',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'travel',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '1',
             'description': TEST_STRING,
             'time_rate': '50',
             'time_number': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'time',
             'idx': '100',
             'description': TEST_STRING,
             'time_rate': '50',
             'time_number': '1',
             'numerator': '2',
             'denominator': '3',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'flat',
             'idx': '1',
             'basis': '-5',
             'numerator': '2',
             'denominator': '3',
             'submit_calc1': 'Do 31.08.2006'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.post(
            '/knr/itemform/',
            {'type': 'general',
             'idx': '1',
             'submit': 'Uložit'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemform.html')
        self.assertEqual(res.context['errors'], True)
        self.assertEqual(res.context['page_title'], 'Úprava položky')
        res = self.client.get('/knr/itemdel/2/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemdel.html')
        last = 17
        res = self.client.post(
            '/knr/itemdel/{:d}/'.format(last),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post(
            '/knr/itemdel/{:d}/'.format(last),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemdeleted.html')
        res = self.client.post('/knr/itemdel/{:d}/'.format(last))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/knr/itemlist/')
        bef = [res.context['rows'][i]['description'] for i in [0, 1]]
        res = self.client.get('/knr/itemdown/1/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        aft = [res.context['rows'][i]['description'] for i in [0, 1]]
        self.assertNotEqual(bef, aft)
        res = self.client.get('/knr/itemdown/1/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        aft = [res.context['rows'][i]['description'] for i in [0, 1]]
        self.assertEqual(bef, aft)
        res = self.client.get('/knr/itemup/1/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_presets(self):
        res = self.client.get('/knr/presets')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/knr/itemform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/knr/presets/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/knr/presets/')
        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTrue(self.client.login(
            username='superuser',
            password='none'))
        res = self.client.get('/knr/presets/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')

    def test_calc(self):
        req = DummyRequest('test_session')
        c = views.Calculation()
        c.title = TEST_STRING
        self.assertTrue(views.setcalc(req, c))
        self.assertEqual(views.getcalc(req).title, TEST_STRING)

    def test_calculation(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        rr = [['1', [17236, 72241, 15171, 104648]],
              ['2', [0, 0, 0, 0]],
              ['3', [1000, 1000, 100, 2100]],
              ['4', [20000, 4200, 420, 24620]],
             ]
        for r in rr:
            with open(join(TEST_DIR, 'calc{}.xml'.format(r[0])), 'rb') as fi:
                res = self.client.post(
                    '/knr/',
                    {'submit_load': 'Načíst kalkulaci',
                     'load': fi},
                    follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            s = soup.select('table.vattbl td')
            self.assertEqual(len(s), 4)
            for i in range(4):
                self.assertEqual(
                    s[i].text,
                    '{} Kč'.format(views.convi(r[1][i])))
