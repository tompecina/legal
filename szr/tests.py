# -*- coding: utf-8 -*-
#
# szr/tests.py
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
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.core import mail
from http import HTTPStatus
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from re import compile
from .models import Court, Proceedings
from . import cron, forms, glob, views

class TestCron(TestCase):
    fixtures = ['szr_test.json']
    
    def setUp(self):
        self.req = HttpRequest()
        self.req.method = 'GET'
        
    def test_courts(self):
        cron.cron_courts(self.req)
        c = Court.objects.all()
        self.assertEqual(len(c), 98)
        c = Court.objects.exclude(reports=None)
        self.assertEqual(len(c), 86)
        
    def test_update(self):
        self.assertEqual(Proceedings.objects.filter(court_id='NSS', auxid=0) \
                         .count(), 2)
        st = datetime.now()
        for i in range(6):
            cron.cron_update(self.req)
        self.assertFalse(Proceedings.objects.filter(court_id='NSS', auxid=0))
        ch6 = Proceedings.objects.get(pk=6).changed
        self.assertGreaterEqual(ch6, st)
        p = Proceedings.objects.all().order_by('pk')
        self.assertEqual(
            tuple(p.values_list('pk', 'changed', 'hash', 'notify')),
            ((1,
              datetime(2016, 7, 8, 12, 25, 19),
              '487dba55ef6843d7a99c75799563e50a',
              False),
             (2,
              datetime(2016, 5, 21, 6, 12, 33),
              '42408bc2325387d17c0946c4fa2f2fd1',
              True),
             (3,
              datetime(2016, 6, 28, 9, 18, 55),
              '5b40f8705599e6f2dada0af88aa759bb',
              True),
             (4,
              None,
              '9dd13c91a9eb4795c1ac3a1c0678d482',
              False),
             (5,
              None,
              'b8096f084f58c5ae4bec1cf5effdaf6b',
              False),
             (6,
              ch6,
              '7091c453e984b1e4180442964e023b2e',
              True),
            ))

    def test_notify(self):
        for i in range(6):
            cron.cron_update(self.req)
        cron.cron_notify(self.req)
        m = mail.outbox
        self.assertEqual(len(m), 1)
        m = m[0]
        self.assertEqual(m.from_email, 'Server legal.pecina.cz <legal@pecina.cz>')
        self.assertEqual(m.to, ['tomas@pecina.cz'])
        self.assertEqual(m.subject, 'Zmeny ve sledovanych rizenich')
        self.assertEqual(
            m.body,
            'V těchto soudních řízeních, která sledujete, došlo ke změně:\n' \
            ' - Městský soud Praha, sp. zn. 10 T 8/2014 (Opencard)\n' \
            ' - http://infosoud.justice.cz/InfoSoud/public/search.do?' \
            'org=MSPHAAB&cisloSenatu=10&druhVec=T&bcVec=8&rocnik=2014' \
            '&typSoudu=os&autoFill=true&type=spzn\n' \
            ' - Městský soud Praha, sp. zn. 41 T 3/2016 (Igor Ševcov)\n' \
            ' - http://infosoud.justice.cz/InfoSoud/public/search.do?' \
            'org=MSPHAAB&cisloSenatu=41&druhVec=T&bcVec=3&rocnik=2016' \
            '&typSoudu=os&autoFill=true&type=spzn\n' \
            ' - Nejvyšší správní soud, sp. zn. 11 Kss 6/2015 ' \
            '(Miloš Zbránek)\n' \
            ' - http://www.nssoud.cz/mainc.aspx?cls=InfoSoud&' \
            'kau_id=173442\n\n' \
            'Server legal.pecina.cz (https://legal.pecina.cz)\n')

class TestGlob(SimpleTestCase):

    def test_register_regex(self):
        rr = compile(glob.register_regex)
        for p in glob.registers:
            self.assertIsNotNone(rr.match(p), msg=p)
        for p in ['X', '']:
            self.assertIsNone(rr.match(p), msg=p)

class TestViews(TestCase):
    fixtures = ['szr_test.json']
    
    def setUp(self):
        User.objects.create_user('user', 'user@pecina.cz', 'none')

    def tearDown(self):
        User.objects.all().delete()
        
    def test_mainpage(self):
        res = self.client.get('/szr')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/szr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'szr_mainpage.html')
        res = self.client.post('/szr/',
                               {'email': 'alt@pecina.cz',
                                'submit': 'Změnit'},
                               follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(User.objects.get(username='user').email,
                         'alt@pecina.cz')
        res = self.client.get('/szr/')
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
        self.assertFalse(soup.select('table#list'))
        self.client.force_login(User.objects.get(pk=1))
        res = self.client.get('/szr/')
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
        self.assertEqual(len(soup.select('table#list tbody tr')), 6)

    def test_procform(self):
        res = self.client.get('/szr/procform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/szr/procform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/szr/procform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.client.force_login(User.objects.get(pk=1))
        res = self.client.get('/szr/procform/1/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'szr_procform.html')
        try:
            soup = BeautifulSoup(res.content, 'html.parser')
        except:
            self.fail()
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Úprava řízení')
        self.client.logout()
