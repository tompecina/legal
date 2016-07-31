# -*- coding: utf-8 -*-
#
# udn/tests.py
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
from django.http import HttpRequest
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from re import compile
from os.path import join
from os import unlink
from common.settings import BASE_DIR
from . import cron, forms, glob, models, views

class TestCron1(TestCase):
    fixtures = ['udn_test1.json']
    
    def setUp(self):
        self.req = HttpRequest()
        self.req.method = 'GET'

    def checkpdf(self, ll):
        fl = []
        for l in ll:
            fn = join(BASE_DIR, 'test', l)
            try:
                with open(fn) as fi:
                    fc = fi.read()
                unlink(fn)
            except:  # pragma: no cover
                fl.append('E: ' + l)
            if not fc[:-1].endswith('/' + l):  # pragma: no cover
                fl.append('C: ' + l)
        self.assertFalse(fl, msg=fl)
        
    def test_update(self):
        cron.cron_update(self.req)
        d = models.Decision.objects.all()
        self.assertEqual(len(d), 15)
        self.checkpdf([
            '0002_8As__1600055S.pdf',
            '0022_4As__1600037S.pdf',
            '0025_8As__1600041S.pdf',
            '0037_4Afs_1600033S.pdf',
            '0065_4Afs_1600032S.pdf',
            '0066_4Afs_1600033S.pdf',
            '0079_8As__1600023S.pdf',
            '008110As__1600026S.pdf',
            '0095_4Afs_1600035S.pdf',
            '0108_5As__1600008S.pdf',
            '0152_4Ads_1500027S.pdf',
            '019110As__1500030S.pdf',
            '0208_4Ads_1500082S.pdf',
            '0233_5As__1500046S.pdf',
            ])
        
    def test_find(self):
        cron.cron_find(self.req)
        d = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=158,
            year=2015,
            page=33)
        self.assertEqual(len(d), 1)
        self.assertTrue(d[0].anonfilename)
        self.checkpdf(['0046_3As__1600114_20160622142215_prevedeno.pdf'])
        cron.cron_find(self.req)

class TestCron2(TestCase):
    fixtures = ['udn_test2.json']
    
    def setUp(self):
        self.req = HttpRequest()
        self.req.method = 'GET'

    def test_find(self):
        cron.cron_find(self.req)
        d = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=158,
            year=2015,
            page=33)
        self.assertEqual(len(d), 1)
        self.assertFalse(d[0].anonfilename)

class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm(
            {'party_opt': 'icontains'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.6.2001'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '3.3.2005'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.3.2005'})
        self.assertTrue(f.is_valid())

class TestGlob(SimpleTestCase):

    def test_filename_regex(self):
        fr = compile(glob.filename_regex)
        pp = ['test.pdf',
              '9.pdf',
              'a_b.pdf',
              '0185_6Afs_1500040S.pdf',
              '0067_5As__1500054_20151119130217_prevedeno.pdf',
        ]
        ee = ['a b.pdf',
              'a+b.pdf',
              'a-b.pdf',
              'a/b.pdf',
              'a%b.pdf',
              'a#b.pdf',
              '.pdf',
        ]
        for p in pp:
            self.assertIsNotNone(fr.match(p), msg=p)
        for p in ee:
            self.assertIsNone(fr.match(p), msg=p)

class TestModels(SimpleTestCase):

    def test_models(self):
        self.assertEqual(
            str(models.Agenda(
                desc='test_agenda')),
            'test_agenda')
        self.assertEqual(
            str(models.Party(
                name='test_party')),
            'test_party')
        self.assertEqual(
            str(models.Decision(
                senate=4,
                register='As',
                number=26,
                year=2015,
                page=88,
                agenda_id=1,
                date=date.today(),
                filename='test_fn.pdf')),
            '4 As 26/2015-88')

def link_equal(a, b):
    a = a.split('?')
    b = b.split('?')
    if a[0] != b[0]:  # pragma: no cover
        return False
    a = a[1].split('&')
    a.sort()
    b = b[1].split('&')
    b.sort()
    if len(a) != len(b):  # pragma: no cover
        return False
    for i in range(len(a)):
        if a[i] != b[i]:  # pragma: no cover
            return False
    return True
            
class TestViews(TestCase):
    fixtures = ['udn_test1.json']
    
    def test_main(self):
        res = self.client.get('/udn')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/udn/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'udn_mainpage.html')
        res = self.client.post(
            '/udn/',
            {'date_from': '1.1.2015',
             'date_to': '1.7.2016',
             'register': 'As',
             'agenda': '1',
             'party_opt': 'icontains',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        res = self.client.post(
            '/udn/',
            {'party': 'Ing',
             'party_opt': 'icontains',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.redirect_chain[0][1], HTTPStatus.FOUND)
        self.assertTrue(link_equal(
            res.redirect_chain[0][0],
            '/udn/list/?party=Ing&party_opt=icontains&start=0'))
        res = self.client.post(
            '/udn/',
            {'date_from': 'XXX',
             'party_opt': 'icontains',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/udn/',
            {'date_from': '1.1.2015',
             'date_to': '1.7.2014',
             'register': 'As',
             'agenda': '1',
             'party_opt': 'icontains',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

    def test_declist(self):
        res = self.client.get('/udn/list')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.post('/udn/list/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)
        res = self.client.get('/udn/list/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'udn_list.html')
        res = self.client.get('/udn/list/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get( '/udn/list/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?start=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get(
            '/udn/list/?date_from=2015-01-01&date_to=2199-07-01&register=As&' \
            'agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 1)
        res = self.client.get('/udn/list/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 1)
        res = self.client.get('/udn/list/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 0)
        res = self.client.get('/udn/list/?date_from=2199-07-01')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 1)
        res = self.client.get('/udn/list/?date_from=2199-07-02')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 0)
        res = self.client.get('/udn/list/?date_to=2199-07-01')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 1)
        res = self.client.get('/udn/list/?date_to=2199-06-30')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(res.context['total'], 0)
        d = models.Decision.objects.get().__dict__
        del d['id'], d['_state']
        for page in range(200, 437):
            d['page'] = page
            models.Decision(**d).save()
        res = self.client.get('/udn/list/?senate=8')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/udn/list/?senate=8&start=50'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/udn/list/?senate=8&start=200'))
        res = self.client.get('/udn/list/?senate=8&start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 4)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/udn/list/?senate=8&start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/udn/list/?senate=8&start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/udn/list/?senate=8&start=100'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/udn/list/?senate=8&start=200'))
        res = self.client.get('/udn/list/?senate=8&start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 4)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/udn/list/?senate=8&start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/udn/list/?senate=8&start=50'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/udn/list/?senate=8&start=150'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/udn/list/?senate=8&start=200'))
        res = self.client.get('/udn/list/?senate=8&start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
        self.assertEqual(len(res.context['rows']), 38)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/udn/list/?senate=8&start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/udn/list/?senate=8&start=150'))
