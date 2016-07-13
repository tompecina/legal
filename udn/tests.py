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
from .models import Decision
from . import cron, forms, glob, utils, views

class TestCron(TestCase):
    fixtures = ['udn_test.json']
    
    def setUp(self):
        self.req = HttpRequest()
        self.req.method = 'GET'
        self.client = Client()

    def checkpdf(self, ll):
        for l in ll:
            fn = join(BASE_DIR, 'test', l)
            fl = []
            try:
                with open(fn) as fi:
                    fc = fi.read()
                unlink(fn)
            except:
                fl.append('E: ' + l)
            if not fc[:-1].endswith('/' + l):
                fl.append('C: ' + l)
        self.assertFalse(fl, msg=fl)
        
    def test_update(self):
        cron.cron_update(self.req)
        d = Decision.objects.all()
        self.assertEqual(len(d), 18)
        self.checkpdf([
            '0002_8As__1600055S.pdf',
            '0022_4As__1600037S.pdf',
            '0025_8As__1600041S.pdf',
            '0037_4Afs_1600033S.pdf',
            '003810Ads_1600040S.pdf',
            '0065_4Afs_1600032S.pdf',
            '0066_4Afs_1600033S.pdf',
            '007410Ads_1600027S.pdf',
            '007710As__1600038S.pdf',
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
        d = Decision.objects.filter(senate='8',
                                    register='As',
                                    number='158',
                                    year='2015',
                                    page='33')
        self.assertEqual(len(d), 1)
        self.assertTrue(d[0].anonfilename)
        self.checkpdf(['0046_3As__1600114_20160622142215_prevedeno.pdf'])

class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm({'party_opt': 'icontains'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm({'party_opt': 'icontains',
                            'date_from': '2.3.2005',
                            'date_to': '2.6.2001'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm({'party_opt': 'icontains',
                            'date_from': '2.3.2005',
                            'date_to': '3.3.2005'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm({'party_opt': 'icontains',
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

class TestUtils(SimpleTestCase):

    def test_ref(self):
        pp = ['3 As 12/2015-8',
              '12 Azs 4/2009-118',
              'Konf 1/2011-221',
              '3 As 12/2015',
              '12 Azs 4/2009',
              'Konf 1/2011',
        ]
        for p in pp:
            self.assertEqual(utils.composeref(*utils.decomposeref(p)), p)
            self.assertEqual(utils.composeref(*utils.decomposeref( \
                p.replace('-', ' - '))), p)

class TestViews(TestCase):
    fixtures = ['udn_test.json']
    
    def setUp(self):
        self.client = Client()

    def test_main(self):
        res = self.client.get('/udn')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/udn/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'udn_mainpage.html')
        res = self.client.post('/udn/',
                               {'party_opt': 'icontains',
                                'submit_update': 'Aktualisovat'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')
