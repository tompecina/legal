# -*- coding: utf-8 -*-
#
# sur/tests.py
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

from django.test import TestCase
from django.contrib.auth.models import User
from http import HTTPStatus
from bs4 import BeautifulSoup
from common.settings import BASE_DIR
from common.glob import localdomain
from common.tests import link_equal
from psj.cron import cron_courtrooms, cron_schedule, cron_update as psj_update
from psj.models import Task, Hearing
from udn.cron import cron_update as udn_update
from udn.models import Decision
from . import cron, models, views

pp = [
    ['Jč', 0, 261, 166, 166, 166, 234],
    ['jČ', 0, 261, 166, 166, 166, 234],
    ['B', 1, 134, 158, 38, 108],
    ['b', 1, 134, 158, 38, 108],
    ['ová', 2, 261, 166, 166, 363, 485, 234, 38, 152, 233],
    ['OVÁ', 2, 261, 166, 166, 363, 485, 234, 38, 152, 233],
    ['Luděk Legner', 3, 234],
    ['LUDĚK legner', 3, 234],
    ['Mgr. Ivana Rychnovská', 3, 1784],
    ['MGR. IVANA RYCHNOVSKÁ', 3, 1784],
    ['Huis', 1, 2, 2],
    ['hUIS', 1, 2, 2],
]

class TestCron(TestCase):
    fixtures = ['sur_test.json']

    def test_sur_notice(self):
        self.assertEqual(cron.sur_notice(1), '')
        for p in pp:
            Hearing.objects.all().delete()
            models.Found.objects.all().delete()
            models.Party.objects.all().delete()
            models.Party(uid_id=1, party=p[0], party_opt=p[1]).save()
            cron_schedule('1.12.2016')
            while Task.objects.exists():
                psj_update()
            Decision.objects.all().delete()
            udn_update()
            self.assertEqual(
                list(models.Found.objects.values_list('number', flat=True)),
                p[2:])
        Hearing.objects.all().delete()
        models.Found.objects.all().delete()
        models.Party.objects.all().delete()
        models.Party(uid_id=1, party='ová', party_opt=0).save()
        cron_schedule('1.12.2016')
        while Task.objects.exists():
            psj_update()
        Decision.objects.all().delete()
        udn_update()
        self.assertEqual(
            cron.sur_notice(1),
            'Byli nově zaznamenáni tito účastníci řízení, které ' \
            'sledujete:\n\n' \
            ' - Anna Krayemová, Krajský soud Brno, sp. zn. 27 Co 363/2014\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27' \
            '&register=Co&number=363&year=2014&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Dana Lauerová, Krajský soud Brno, sp. zn. 7 To 485/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=7' \
            '&register=To&number=485&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Hana Brychtová, Nejvyšší správní soud, sp. zn. 5 As ' \
            '233/2015\n' \
            '   https://legal.pecina.cz/udn/list/?senate=5&register=As' \
            '&number=233&year=2015&page=46\n\n' \
            ' - Helena Polášková, Krajský soud Brno, sp. zn. 18 Co 234/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=18' \
            '&register=Co&number=234&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Jana Krebsová, Nejvyšší správní soud, sp. zn. 4 Ads ' \
            '152/2015\n' \
            '   https://legal.pecina.cz/udn/list/?senate=4&register=Ads' \
            '&number=152&year=2015&page=27\n\n'
            ' - Jitka Krejčová, Krajský soud Brno, sp. zn. 27 Co 166/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27' \
            '&register=Co&number=166&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Lenka Krejčová, Krajský soud Brno, sp. zn. 27 Co 166/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27' \
            '&register=Co&number=166&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Mateřská škola a Základní škola, Ostopovice, okres Brno - ' \
            'venkov, příspěvková organizace, Nejvyšší správní soud, ' \
            'sp. zn. 10 As 81/2016\n' \
            '   https://legal.pecina.cz/udn/list/?senate=10&register=As' \
            '&number=81&year=2016&page=26\n\n' \
            ' - Milada Krajčová, Krajský soud Brno, sp. zn. 27 Co 261/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27' \
            '&register=Co&number=261&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n' \
            ' - Odborová organizace ochrany práv zaměstnanců, Nejvyšší ' \
            'správní soud, sp. zn. 4 Ads 208/2015\n' \
            '   https://legal.pecina.cz/udn/list/?senate=4&register=Ads' \
            '&number=208&year=2015&page=82\n\n' \
            ' - Vladimíra Foukalová, Krajský soud Brno, sp. zn. 18 Co ' \
            '38/2016\n' \
            '   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=18' \
            '&register=Co&number=38&year=2016&date_from=2016-12-01' \
            '&date_to=2016-12-01\n\n')
        self.assertEqual(cron.sur_notice(1), '')

class TestModels(TestCase):
    fixtures = ['sur_test.json']

    def test_models(self):
        models.Party(uid_id=1, party='ová', party_opt=0).save()
        udn_update()
        self.assertEqual(
            str(models.Party.objects.first()),
            'ová')
        self.assertEqual(
            str(models.Found.objects.first()),
            'Nejvyšší správní soud, 4 Ads 208/2015')

class TestViews(TestCase):
    
    def setUp(self):
        User.objects.create_user('user', 'user@' + localdomain, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()
        
    def test_mainpage(self):
        res = self.client.get('/sur')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/sur/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        res = self.client.post(
            '/sur/',
            {'email': 'xxx',
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/sur/',
            {'email': 'alt@' + localdomain,
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.user = User.objects.first()
        self.assertEqual(self.user.email, 'alt@' + localdomain)
        res = self.client.get('/sur/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertFalse(soup.select('table#list'))
        models.Party(
            uid=self.user,
            party_opt=0,
            party='Test').save()
        res = self.client.get('/sur/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(soup.select('table#list tbody tr')), 1)
        for number in range(200, 437):
            models.Party(
                uid=self.user,
                party_opt=0,
                party='Test {:d}'.format(number)).save()
        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/sur/?start=50'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/sur/?start=200'))
        res = self.client.get('/sur/?start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/sur/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/sur/?start=0'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/sur/?start=100'))
        self.assertTrue(link_equal(
            links[4]['href'],
            '/sur/?start=200'))
        res = self.client.get('/sur/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/sur/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/sur/?start=50'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/sur/?start=150'))
        self.assertTrue(link_equal(
            links[4]['href'],
            '/sur/?start=200'))
        res = self.client.get('/sur/?start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 38)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/sur/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/sur/?start=150'))
        res = self.client.get('/sur/?start=500')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 1)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(
            links[1]['href'],
            '/sur/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/sur/?start=187'))

    def test_partyform(self):
        res = self.client.get('/sur/partyform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/partyform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/sur/partyform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/partyform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sur_partyform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Nový účastník')
        res = self.client.post(
            '/sur/partyform/',
            {'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/sur/partyform/',
            {'party': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        res = self.client.post(
            '/sur/partyform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        party_id = models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 2').id
        res = self.client.get('/sur/partyform/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sur_partyform.html')
        soup = BeautifulSoup(res.content, 'html.parser')
        p = soup.select('h1')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0].text, 'Úprava účastníka')
        res = self.client.post(
            '/sur/partyform/{:d}/'.format(party_id),
            {'party': 'Test 8',
             'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        party = models.Party.objects.get(pk=party_id)
        self.assertEqual(party.party, 'Test 8')
        
    def test_partydel(self):
        party_id = models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test').id
        res = self.client.get('/sur/partydel/{:d}'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get(
            '/sur/partydel/{:d}/'.format(party_id),
            follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydel.html')
        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydeleted.html')
        self.assertFalse(models.Party.objects.filter(pk=party_id).exists())
        res = self.client.post('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_partydelall(self):
        models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 1')
        models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 2')
        self.assertEqual(models.Party.objects.count(), 2)
        res = self.client.get('/sur/partydelall')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/partydelall/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/sur/partydelall/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/partydelall/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydelall.html')
        res = self.client.post(
            '/sur/partydelall/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(models.Party.objects.count(), 2)
        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(models.Party.objects.count(), 2)
        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertFalse(models.Party.objects.exists())

    def test_partybatchform(self):
        models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 01')
        models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 05')
        models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 05')
        res = self.client.get('/sur/partybatchform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/partybatchform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/sur/partybatchform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/partybatchform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.html')
        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_load': 'Načíst'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.html')
        self.assertContains(res, 'Nejprve zvolte soubor k načtení')
        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_xxx': 'XXX'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')
        with open(BASE_DIR + '/sur/testdata/import.csv', 'rb') as fi:
            res = self.client.post(
                '/sur/partybatchform/',
                {'submit_load': 'Načíst',
                 'load': fi},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchresult.html')
        self.assertEqual(models.Party.objects.count(), 9)
        self.assertEqual(res.context['count'], 6)
        self.assertEqual(
            res.context['errors'],
            [[1, 'Chybná délka řetězce'],
             [3, 'Chybná délka řetězce'],
             [4, 'Chybná zkratka pro posici'],
             [5, 'Řetězci "Test 05" odpovídá více než jeden účastník']])
        res = self.client.get('/sur/partyexport/')
        self.assertEqual(
            res.content.decode('utf-8'),
            'Test 01:*\r\n' \
            'Test 05:*\r\n' \
            'Test 05:*\r\n' \
            'Test 06:*\r\n' \
            'Test 07:*\r\n' \
            'Test 08:<\r\n' \
            'Test 09:>\r\n' \
            'Test 10:=\r\n' + \
            ('T' * 80) + ':*\r\n')

    def test_partyexport(self):
        models.Party.objects.create(
            uid=self.user,
            party='Test 1',
            party_opt=0)
        models.Party.objects.create(
            uid=self.user,
            party='Test 2',
            party_opt=1)
        models.Party.objects.create(
            uid=self.user,
            party='Test 3',
            party_opt=2)
        models.Party.objects.create(
            uid=self.user,
            party='Test 4',
            party_opt=3)
        res = self.client.get('/sur/partyexport')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)
        res = self.client.get('/sur/partyexport/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        res = self.client.get('/sur/partyexport/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.get('/sur/partyexport/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
        self.assertEqual(
            res.content.decode('utf-8'),
            'Test 1:*\r\n' \
            'Test 2:<\r\n' \
            'Test 3:>\r\n' \
            'Test 4:=\r\n')
