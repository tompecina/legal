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

from django.test import SimpleTestCase, TransactionTestCase, Client
from django.http import HttpRequest
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from re import compile
from .models import Decision
from . import cron, forms, glob, utils, views

class TestCron(TransactionTestCase):
    fixtures = ['udn_test.json']
    
    def setUp(self):
        self.req = HttpRequest()
        self.req.method = 'GET'
        self.client = Client()

    def test_update(self):
        cron.cron_update(self.req)
        d = Decision.objects.all()
        self.assertEqual(len(d), 18)
        
    def test_find(self):
        cron.cron_find(self.req)
        d = Decision.objects.filter(senate='8',
                                    register='As',
                                    number='158',
                                    year='2015',
                                    page='33')
        self.assertEqual(len(d), 1)
        self.assertTrue(d[0].anonfilename)

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

class TestViews(TransactionTestCase):
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
