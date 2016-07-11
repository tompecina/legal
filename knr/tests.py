# -*- coding: utf-8 -*-
#
# knr/tests.py
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

from django.test import SimpleTestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from http import HTTPStatus
from copy import copy
from bs4 import BeautifulSoup
from io import BytesIO
from common.settings import BASE_DIR
from cache.tests import DummyRequest
from . import forms, views, utils

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
             'multiple_number': '1'}
        f = forms.ServiceForm(s)
        self.assertTrue(f.is_valid())
        d = copy(s)
        d['off10_flag'] = d['off30_flag'] = d['off30limit5000_flag'] = 'on'
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
        d['off30_flag'] = d['off30limit5000_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['off10_flag'] = d['off30limit5000_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())
        d = copy(s)
        d['off10_flag'] = d['off30_flag'] = 'on'
        f = forms.ServiceForm(d)
        self.assertFalse(f.is_valid())

    def test_FlatForm(self):
        f = forms.FlatForm({})
        self.assertFalse(f.is_valid())
        s = {'idx': '1', 'description': 'Popis', 'rate': '1500'}
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

ts = 'Příliš žluťoučký kůň úpěnlivě přepíná ďábelské kódy'
        
class T(views.Calculation, views.Item):
    pass

def stripxml(s):
    try:
        s = s.decode('utf-8')
        s = s.split('<calculation', 1)
        return s[0] + '<calculation>' + s[1].split('>', 1)[1]
    except:
        return ''

class TestUtils(TransactionTestCase):
    fixtures = ['knr_test.json']

    def test_getVAT(self):
        self.assertAlmostEqual(utils.getVAT(), 25)
    
class TestViews(TransactionTestCase):
    fixtures = ['knr_test.json']
    
    def setUp(self):
        self.client = Client()
        User.objects.create_user('user', 'user@pecina.cz', 'none')
        User.objects.create_user('superuser', 'superuser@pecina.cz', 'none')
        
    def tearDown(self):
        User.objects.all().delete()
        
    def test_lim(self):
        self.assertEqual(views.lim(1, 2, 3), 2)
        self.assertEqual(views.lim(1, -2, 3), 1)
        self.assertEqual(views.lim(1, 4, 3), 3)

    def test_findloc(self):
        r = views.findloc('Melantrichova 504/5, Praha 1')
        self.assertEqual(
            r[0],
            'Melantrichova 504/5, 110 00 Praha 1-Staré Město, Česká republika')
        self.assertAlmostEqual(r[1], 51.0852574)
        self.assertAlmostEqual(r[2], 13.4211651)
        
    def test_finddist(self):
        r = views.finddist(50, 15, 51, 16)
        self.assertEqual(r, (182046, 20265))
        
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
        res = self.client.post('/knr/',
                               {'vat_rate': '21,00',
                                'submit_update': 'Aktualisovat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        res = self.client.post('/knr/',
                               {'vat_rate': '21,00',
                                'submit_edit': 'Upravit položky'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_itemlist.html')
        res = self.client.post('/knr/',
                               {'submit_empty': 'Vyprázdnit kalkulaci'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        res = self.client.post('/knr/',
                               {'title': 'test',
                                'calculation_note': 'cn',
                                'internal_note': 'in',
                                'submit_empty': 'Vyprázdnit kalkulaci'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
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
        for suffix in [['xml', 'Uložit kalkulaci', 'text/xml'],
                       ['pdf', 'Export do PDF', 'application/pdf']]:
            with open(BASE_DIR + '/knr/testdata/calc1.' + suffix[0], 'rb') \
                 as fi:
                res = self.client.post('/knr/',
                                       {'submit_load': 'Načíst kalkulaci',
                                        'load': fi},
                                       follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], ts)
            calculation_note = soup.select('#id_calculation_note')
            self.assertEqual(len(calculation_note), 1)
            self.assertEqual(calculation_note[0].text, 'Poznámka')
            internal_note = soup.select('#id_internal_note')
            self.assertEqual(len(internal_note), 1)
            self.assertEqual(internal_note[0].text, 'Interní poznámka')
            vat_rate = soup.select('#id_vat_rate')
            self.assertEqual(len(vat_rate), 1)
            self.assertEqual(vat_rate[0]['value'], '21,00')
            res = self.client.post('/knr/',
                                   {'vat_rate': '21,00',
                                    'title': ts,
                                    'calculation_note': 'cn',
                                    'internal_note': 'in',
                                    'submit_' + suffix[0]: suffix[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertIn('content-type', res)
            self.assertEqual(res['content-type'], suffix[2])
            con = BytesIO(res.content)
            con.seek(0)
            res = self.client.post('/knr/',
                                   {'submit_load': 'Načíst kalkulaci',
                                    'load': con}, follow=True)
            con.close()
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            title = soup.select('#id_title')
            self.assertEqual(len(title), 1)
            self.assertEqual(title[0]['value'], ts)
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
            res = self.client.post('/knr/',
                                   {'vat_rate': '21,00',
                                    'submit_' + b[0]:
                                    'Upravit ' + b[1]},
                                   follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_' + b[0] + 'list.html')
            
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
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
        p = soup.select('h1 + p')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, '(nejsou zadány žádné položky)')
        try:
            pre = soup.select('#id_new')[0].select('option')
        except:
            self.fail()
        self.assertEqual(len(pre), 23)
        for val in [p['value'] for p in pre if p['value']]:
            res = self.client.post('/knr/itemform/',
                                   {'presel': val,
                                    'submit_new':
                                    'Přidat položku:'})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_itemform.html')
        
    def test_list(self):
        for b in [['place', 'zadána žádná místa'],
                  ['car', 'zadána žádná vozidla'],
                  ['formula', 'zadány žádné předpisy']]:
            res = self.client.get('/knr/' + b[0] + 'list')
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/knr/' + b[0] + 'list/')
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/knr/' + b[0] + 'list/', follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/knr/' + b[0] + 'list/')
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_' + b[0] + 'list.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            p = soup.select('h1 + p')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, '(nejsou ' + b[1] + ')')
            self.client.logout()

    def test_form(self):
        for b in [['place', 'Nové místo'],
                  ['car', 'Nové vozidlo'],
                  ['formula', 'Nový předpis']]:
            res = self.client.get('/knr/' + b[0] + 'form')
            self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
            res = self.client.get('/knr/' + b[0] + 'form/')
            self.assertEqual(res.status_code, HTTPStatus.FOUND)
            res = self.client.get('/knr/' + b[0] + 'form/', follow=True)
            self.assertTemplateUsed(res, 'login.html')
            self.assertTrue(self.client.login(username='user', password='none'))
            res = self.client.get('/knr/' + b[0] + 'form/')
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTrue(res.has_header('content-type'))
            self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
            self.assertTemplateUsed(res, 'knr_' + b[0] + 'form.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            p = soup.select('h1')
            self.assertEqual(len(p), 1)
            self.assertEqual(p[0].text, b[1])
            self.client.logout()
            
    def dcomp(self, f, d1, d2):
        for n in f:
            if views.gd[n][0] == 'F':
                self.assertAlmostEqual(d1[n], d2[n])
            else:
                self.assertEqual(d1[n], d2[n])

    def test_conv(self):
        d = {'title': ts,
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
                x = ['false', 'true'][d[n]]
            else:
                x = str(d[n])
            s += '<' + n + '>' + x + '</' + n + '>'
        s += '</calculation>'
        o = T()
        views.s2i(f, BeautifulSoup(s, 'xml'), o)
        l = {}
        views.d2d(f, d, l)
        self.dcomp(f, d, l)
        
    def test_calc(self):
        req = DummyRequest('test-session')
        c = views.Calculation()
        c.title = ts
        self.assertTrue(views.setcalc(req, c))
        self.assertEqual(views.getcalc(req).title, ts)

    def test_xml(self):
        i = 1
        while True:
            try:
                with open(BASE_DIR + '/knr/testdata/calc%d.xml' % i, 'rb') \
                     as fi:
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

    def test_calculation(self):
        self.assertTrue(self.client.login(username='user', password='none'))
        rr = [['1', [17236, 72241, 15171, 104648]],
              ['2', [0, 0, 0, 0]],
              ['3', [1000, 1000, 100, 2100]],
              ['4', [20000, 4200, 420, 24620]],
        ]
        for r in rr:
            with open(BASE_DIR + '/knr/testdata/calc' + r[0] + '.xml', 'rb') \
                 as fi:
                res = self.client.post('/knr/',
                                       {'submit_load': 'Načíst kalkulaci',
                                        'load': fi},
                                       follow=True)
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'knr_mainpage.html')
            try:
                soup = BeautifulSoup(res.content, 'html.parser')
            except:
                self.fail()
            s = soup.select('table.vattbl td')
            self.assertEqual(len(s), 4)
            for i in range(4):
                self.assertEqual(s[i].text, views.convi(r[1][i]) + ' Kč')
