# -*- coding: utf-8 -*-
#
# dir/tests.py
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

from django.test import SimpleTestCase, TransactionTestCase, TestCase
from django.contrib.auth.models import User
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from common.settings import BASE_DIR
from common.glob import localdomain
from common.tests import link_equal, setdl
from sir.cron import cron_gettr, cron_proctr
from sir.models import Vec
from . import cron, forms, models, views

class TestCron(TransactionTestCase):
    fixtures = ['dir_test.json']

    def test_dir_notice(self):
        setdl(-1)
        cron_gettr()
        cron_proctr()
        self.assertEqual(models.Discovered.objects.count(), 15)
        self.assertEqual(cron.dir_notice(1), '')
        Vec.objects.update(link="https://legal.pecina.cz/link")
        self.assertEqual(
            cron.dir_notice(1),
            'Byli nově zaznamenáni tito dlužníci, které sledujete:\n\n' \
            ' - Test 02, sp. zn. KSBR 0 INS 4/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 03, sp. zn. KSOS 0 INS 7/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 04, sp. zn. KSOS 0 INS 36/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 05, sp. zn. KSOS 0 INS 35/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 07, sp. zn. KSOS 0 INS 18/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 08, sp. zn. KSPL 0 INS 31/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 09, sp. zn. KSOS 0 INS 2/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 11, sp. zn. KSUL 0 INS 22/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 12, sp. zn. KSPH 0 INS 32/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 13, sp. zn. KSHK 0 INS 19/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 14, sp. zn. MSPH 0 INS 20/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 15, sp. zn. KSPH 0 INS 8/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 15, sp. zn. KSOS 0 INS 11/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 15, sp. zn. KSCB 0 INS 27/2008\n' \
            '   https://legal.pecina.cz/link\n\n' \
            ' - Test 15, sp. zn. KSCB 0 INS 28/2008\n' \
            '   https://legal.pecina.cz/link\n\n')
        self.assertFalse(models.Discovered.objects.exists())
        
class TestForms(SimpleTestCase):

    def test_DebtorForm(self):
        f = forms.DebtorForm(
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1964'})
        self.assertFalse(f.is_valid())
        f = forms.DebtorForm(
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1965'})
        self.assertTrue(f.is_valid())
        f = forms.DebtorForm(
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1966'})
        self.assertTrue(f.is_valid())

class TestModels(TransactionTestCase):
    fixtures = ['dir_test.json']

    def test_models(self):
        setdl(-1)
        cron_gettr()
        cron_proctr()
        Vec.objects.update(link="https://legal.pecina.cz/link")
        self.assertEqual(
            str(models.Debtor.objects.first()),
            'Error 01')
        self.assertEqual(
            str(models.Discovered.objects.first()),
            'Test 02')

class TestViews1(TestCase):
    
    def setUp(self):
        User.objects.create_user('user', 'user@' + localdomain, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()
        
    def test_mainpage(self):
        res = self.client.get('/dir')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/dir/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        res = self.client.post(
            '/dir/',
            {'email': 'xxx',
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/',
            {'email': 'alt@' + localdomain,
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.user = User.objects.first()
        self.assertEqual(self.user.email, 'alt@' + localdomain)
        res = self.client.get('/dir/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertFalse(soup.select('table#list'))
        models.Debtor(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test').save()
        res = self.client.get('/dir/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(soup.select('table#list tbody tr')), 1)
        for number in range(200, 437):
            models.Debtor(
                uid=self.user,
                name_opt=0,
                first_name_opt=0,
                desc=('Test %d' % number)).save()
        res = self.client.get('/dir/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/dir/debtorform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/dir/?start=50'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/dir/?start=200'))
        res = self.client.get('/dir/?start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/dir/debtorform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/dir/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/dir/?start=0'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/dir/?start=100'))
        self.assertTrue(link_equal(
            links[4]['href'],
            '/dir/?start=200'))
        res = self.client.get('/dir/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/dir/debtorform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/dir/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/dir/?start=50'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/dir/?start=150'))
        self.assertTrue(link_equal(
            links[4]['href'],
            '/dir/?start=200'))
        res = self.client.get('/dir/?start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 38)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/dir/debtorform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/dir/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/dir/?start=150'))
        res = self.client.get('/dir/?start=500')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 1)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/dir/debtorform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/dir/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/dir/?start=187'))

    def test_debtorform(self):
        res = self.client.get('/dir/debtorform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/debtorform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/dir/debtorform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/debtorform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový dlužník')
        res = self.client.post(
            '/dir/debtorform/',
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'XXX',
             'first_name_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'genid': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'birthid': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'date_birth': '1970-X-01',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': '1899',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_to': '1899',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_to': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1964',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/dir/debtorform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        res = self.client.post(
            '/dir/debtorform/',
            {'desc': 'Test',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        debtor_id = models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            birthid='7001011234',
            desc='Test 2').id
        res = self.client.get('/dir/debtorform/%d/' % debtor_id)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'dir_debtorform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Úprava dlužníka')
        res = self.client.post(
            ('/dir/debtorform/%d/' % debtor_id),
            {'desc': 'Test 8',
             'court': 'MSPHAAB',
             'name': 'Název',
             'name_opt': 'icontains',
             'first_name': 'Jméno',
             'first_name_opt': 'icontains',
             'genid': '12345678',
             'taxid': '001-12345678',
             'birthid': '700101/1234',
             'date_birth': '15.1.1970',
             'year_birth_from': '1965',
             'year_birth_to': '1966',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        debtor = models.Debtor.objects.get(pk=debtor_id)
        self.assertEqual(debtor.desc, 'Test 8')
        self.assertEqual(debtor.court, 'MSPHAAB')
        self.assertEqual(debtor.name, 'Název')
        self.assertEqual(debtor.first_name, 'Jméno')
        self.assertEqual(debtor.genid, '12345678')
        self.assertEqual(debtor.taxid, '001-12345678')
        self.assertEqual(debtor.birthid, '7001011234')
        self.assertEqual(debtor.date_birth, date(1970, 1, 15))
        self.assertEqual(debtor.year_birth_from, 1965)
        self.assertEqual(debtor.year_birth_to, 1966)
        
class TestViews2(TestCase):
    
    def setUp(self):
        User.objects.create_user('user', 'user@' + localdomain, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()
        
    def test_debtordel(self):
        debtor_id = models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test').id
        res = self.client.get('/dir/debtordel/%d' % debtor_id)
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/debtordel/%d/' % debtor_id)
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get(('/dir/debtordel/%d/' % debtor_id), follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/debtordel/%d/' % debtor_id)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtordel.html')
        res = self.client.post(
            '/dir/debtordel/%d/' % debtor_id,
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        res = self.client.post(
            '/dir/debtordel/%d/' % debtor_id,
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtordeleted.html')
        self.assertFalse(models.Debtor.objects.filter(pk=debtor_id).exists())
        res = self.client.post('/dir/debtordel/%d/' % debtor_id)
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_debtordelall(self):
        models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test 1')
        models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test 2')
        self.assertEqual(models.Debtor.objects.count(), 2)
        res = self.client.get('/dir/debtordelall')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/debtordelall/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/dir/debtordelall/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/debtordelall/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtordelall.html')
        res = self.client.post(
            '/dir/debtordelall/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        res = self.client.post(
            '/dir/debtordelall/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(models.Debtor.objects.count(), 2)
        res = self.client.post(
            '/dir/debtordelall/',
            {'submit_yes': 'Ano',
             'conf': 'ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertEqual(models.Debtor.objects.count(), 2)
        res = self.client.post(
            '/dir/debtordelall/',
            {'submit_yes': 'Ano',
             'conf': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_mainpage.html')
        self.assertFalse(models.Debtor.objects.exists())

    def test_debtorbatchform(self):
        models.Debtor.objects.create(
            uid=self.user,
            name='Název 1',
            name_opt=0,
            first_name_opt=0,
            desc='Test 1')
        models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test 21')
        models.Debtor.objects.create(
            uid=self.user,
            name_opt=0,
            first_name_opt=0,
            desc='Test 21')
        res = self.client.get('/dir/debtorbatchform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/debtorbatchform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/dir/debtorbatchform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/debtorbatchform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorbatchform.html')
        res = self.client.post(
            '/dir/debtorbatchform/',
            {'submit_load': 'Načíst'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorbatchform.html')
        self.assertContains(res, 'Nejprve zvolte soubor k načtení')
        res = self.client.post(
            '/dir/debtorbatchform/',
            {'submit_xxx': 'XXX'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorbatchform.html')
        self.assertEquals(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        with open(BASE_DIR + '/dir/testdata/import.csv', 'rb') as fi:
            res = self.client.post(
                '/dir/debtorbatchform/',
                {'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'dir_debtorbatchresult.html')
        self.assertEqual(models.Debtor.objects.count(), 9)
        self.assertEqual(res.context['count'], 7)
        self.assertEqual(
            res.context['errors'],
            [[3, 'Prázdný popis'],
             [4, 'Chybný formát'],
             [5, 'Chybná zkratka pro posici v poli <q>název</q>'],
             [6, 'Příliš dlouhé pole <q>název</q>'],
             [7, 'Chybná zkratka pro posici v poli <q>jméno</q>'],
             [8, 'Příliš dlouhé pole <q>jméno</q>'],
             [9, 'Chybná hodnota pro IČO'],
             [10, 'Chybná hodnota pro IČO'],
             [11, 'Chybná hodnota pro DIČ'],
             [12, 'Chybná hodnota pro rodné číslo'],
             [13, 'Chybná hodnota pro datum narození'],
             [14, 'Chybná hodnota pro pole <q>rokNarozeníOd</q>'],
             [15, 'Chybná hodnota pro pole <q>rokNarozeníOd</q>'],
             [16, 'Chybná hodnota pro pole <q>rokNarozeníDo</q>'],
             [17, 'Chybná hodnota pro pole <q>rokNarozeníDo</q>'],
             [18, 'Chybný interval pro rok narození'],
             [19, 'Chybný formát'],
             [20, 'Chybný parametr: "xxx"'],
             [21, 'Popisu "Test 21" odpovídá více než jeden dlužník'],
             [28, 'Příliš dlouhý popis']])
        res = self.client.get('/dir/debtorexport/')
        self.assertEqual(
            res.content.decode('utf-8'),
            'Test 1,název=Název 2:*\r\n' \
            'Test 21\r\n' \
            'Test 21\r\n' \
            'Test 22,soud=KSOS,název=Název:*,jméno=Jméno:<,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=01.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' \
            'Test 23,soud=KSOS,název=Název:<,jméno=Jméno:>,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=01.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' \
            'Test 24,soud=KSOS,název=Název:>,jméno=Jméno:=,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=01.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' \
            'Test 25,soud=KSOS,název=Název:=,jméno=Jméno:*,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=01.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' \
            'Test 26,soud=KSOS,název=Název:*,jméno=Jméno:*,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=01.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' + \
            ('T' * 255) + '\r\n')
        
class TestViews3(TransactionTestCase):
    
    def setUp(self):
        User.objects.create_user('user', 'user@' + localdomain, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()
        
    def test_debtorexport(self):
        models.Debtor.objects.create(
            uid=self.user,
            desc='Test 1',
            court='MSPHAAB',
            name='Název',
            name_opt=0,
            first_name='Jméno',
            first_name_opt=1,
            genid='12345678',
            taxid='001-12345678',
            birthid='7001011234',
            date_birth=date(1970, 1, 15),
            year_birth_from=1965,
            year_birth_to=1966)
        models.Debtor.objects.create(
            uid=self.user,
            desc='Test 2',
            name='Název',
            name_opt=2,
            first_name='Jméno',
            first_name_opt=3)
        models.Debtor.objects.create(
            uid=self.user,
            desc='Test 3',
            name_opt=0,
            first_name_opt=0)
        res = self.client.get('/dir/debtorexport')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/dir/debtorexport/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/dir/debtorexport/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/dir/debtorexport/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
        self.assertEqual(
            res.content.decode('utf-8'),
            'Test 1,soud=MSPH,název=Název:*,jméno=Jméno:<,IČO=12345678,' \
            'DIČ=001-12345678,RČ=700101/1234,datumNarození=15.01.1970,' \
            'rokNarozeníOd=1965,rokNarozeníDo=1966\r\n' \
            'Test 2,název=Název:>,jméno=Jméno:=\r\n' \
            'Test 3\r\n')
