# -*- coding: utf-8 -*-
#
# tests/test_sur.py
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
from os.path import join

from bs4 import BeautifulSoup
from django.test import TransactionTestCase, TestCase
from django.contrib.auth.models import User

from common.glob import LOCAL_DOMAIN
from common.settings import TEST_DATA_DIR
from tests.utils import link_equal, check_html
from psj.cron import cron_schedule, cron_update as psj_update
from psj.models import Task, Hearing
from udn.cron import cron_update as udn_update
from udn.models import Decision
from sur import cron, models


APP = __package__


class TestCron(TestCase):

    fixtures = ('sur_test.json',)

    def test_sur_notice(self):

        cases = (
            ('Jč', 0, 261, 166, 166, 166, 234),
            ('jČ', 0, 261, 166, 166, 166, 234),
            ('B', 1, 134, 158, 38, 108),
            ('b', 1, 134, 158, 38, 108),
            ('ová', 2, 261, 166, 166, 363, 485, 234, 38, 152, 233),
            ('OVÁ', 2, 261, 166, 166, 363, 485, 234, 38, 152, 233),
            ('Luděk Legner', 3, 234),
            ('LUDĚK legner', 3, 234),
            ('Mgr. Ivana Rychnovská', 3, 1784),
            ('MGR. IVANA RYCHNOVSKÁ', 3, 1784),
            ('Huis', 1, 2, 2),
            ('hUIS', 1, 2, 2),
        )

        self.assertEqual(cron.sur_notice(1), '')

        for test in cases:
            Hearing.objects.all().delete()
            models.Found.objects.all().delete()
            models.Party.objects.all().delete()
            models.Party(uid_id=1, party=test[0], party_opt=test[1]).save()
            cron_schedule('1.12.2016')
            while Task.objects.exists():
                psj_update()
            Decision.objects.all().delete()
            udn_update()
            self.assertEqual(tuple(models.Found.objects.values_list('number', flat=True)), test[2:])

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
            '''\
Byli nově zaznamenáni tito účastníci řízení, které sledujete:

 - Anna Krayemová, Krajský soud Brno, sp. zn. 27 Co 363/2014
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27&register=Co&number=363&year=2014&date_from=2016-12-01\
&date_to=2016-12-01

 - Dana Lauerová, Krajský soud Brno, sp. zn. 7 To 485/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=7&register=To&number=485&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

 - Hana Brychtová, Nejvyšší správní soud, sp. zn. 5 As 233/2015
   https://legal.pecina.cz/udn/list/?senate=5&register=As&number=233&year=2015&page=46

 - Helena Polášková, Krajský soud Brno, sp. zn. 18 Co 234/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=18&register=Co&number=234&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

 - Jana Krebsová, Nejvyšší správní soud, sp. zn. 4 Ads 152/2015
   https://legal.pecina.cz/udn/list/?senate=4&register=Ads&number=152&year=2015&page=27

 - Jitka Krejčová, Krajský soud Brno, sp. zn. 27 Co 166/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27&register=Co&number=166&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

 - Lenka Krejčová, Krajský soud Brno, sp. zn. 27 Co 166/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27&register=Co&number=166&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

 - Mateřská škola a Základní škola, Ostopovice, okres Brno - venkov, příspěvková organizace, Nejvyšší správní soud, \
sp. zn. 10 As 81/2016
   https://legal.pecina.cz/udn/list/?senate=10&register=As&number=81&year=2016&page=26

 - Milada Krajčová, Krajský soud Brno, sp. zn. 27 Co 261/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=27&register=Co&number=261&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

 - Odborová organizace ochrany práv zaměstnanců, Nejvyšší správní soud, sp. zn. 4 Ads 208/2015
   https://legal.pecina.cz/udn/list/?senate=4&register=Ads&number=208&year=2015&page=82

 - Vladimíra Foukalová, Krajský soud Brno, sp. zn. 18 Co 38/2016
   https://legal.pecina.cz/psj/list/?court=KSJIMBM&senate=18&register=Co&number=38&year=2016&date_from=2016-12-01\
&date_to=2016-12-01

''')
        self.assertEqual(cron.sur_notice(1), '')


class TestModels(TransactionTestCase):

    fixtures = ('sur_test.json',)

    def test_models(self):

        models.Party(uid_id=1, party='ová', party_opt=0).save()
        udn_update()
        self.assertEqual(str(models.Party.objects.first()), 'ová')
        self.assertEqual(str(models.Found.objects.first()), 'Nejvyšší správní soud, 4 Ads 208/2015')


class TestViews1(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
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
        check_html(self, res.content)

        res = self.client.post(
            '/sur/',
            {'email': 'xxx',
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/',
            {'email': 'alt@' + LOCAL_DOMAIN,
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.user = User.objects.first()
        self.assertEqual(self.user.email, 'alt@' + LOCAL_DOMAIN)
        check_html(self, res.content)

        res = self.client.get('/sur/')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertFalse(soup.select('table#list'))
        models.Party(uid=self.user, party_opt=0, party='Test').save()

        res = self.client.get('/sur/')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(soup.select('table#list tbody tr')), 1)
        for number in range(200, 437):
            models.Party(uid=self.user, party_opt=0, party='Test {:d}'.format(number)).save()

        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=50'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[3]['href'], '/sur/?start=100'))
        self.assertTrue(link_equal(links[4]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=50'))
        self.assertTrue(link_equal(links[3]['href'], '/sur/?start=150'))
        self.assertTrue(link_equal(links[4]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 38)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=150'))

        res = self.client.get('/sur/?start=500')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        self.assertEqual(len(res.context['rows']), 1)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=187'))


class TestViews2(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

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
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nový účastník')

        res = self.client.post(
            '/sur/partyform/',
            {'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)

        party_id = models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 2').id

        res = self.client.get('/sur/partyform/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sur_partyform.html')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Úprava účastníka')

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
        check_html(self, res.content)


class TestViews3(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

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
        check_html(self, res.content)

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydel.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydeleted.html')
        self.assertFalse(models.Party.objects.filter(pk=party_id).exists())
        check_html(self, res.content)

        res = self.client.post('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)


class TestViews4(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

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
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)
        self.assertEqual(models.Party.objects.count(), 2)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)
        self.assertEqual(models.Party.objects.count(), 2)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.html')
        check_html(self, res.content)
        self.assertFalse(models.Party.objects.exists())


class TestViews5(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

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
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_load': 'Načíst'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.html')
        self.assertContains(res, 'Nejprve zvolte soubor k načtení')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_xxx': 'XXX'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.html')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'sur_import.csv'), 'rb') as infile:
            res = self.client.post(
                '/sur/partybatchform/',
                {'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchresult.html')
        self.assertEqual(models.Party.objects.count(), 9)
        self.assertEqual(res.context['count'], 6)
        self.assertEqual(
            res.context['errors'],
            [(1, 'Chybná délka řetězce'),
             (3, 'Chybná délka řetězce'),
             (4, 'Chybná zkratka pro posici'),
             (5, 'Řetězci "Test 05" odpovídá více než jeden účastník')])
        check_html(self, res.content)

        res = self.client.get('/sur/partyexport/')
        self.assertEqual(
            res.content.decode('utf-8'),
            '''\
Test 01:*
Test 05:*
Test 05:*
Test 06:*
Test 07:*
Test 08:<
Test 09:>
Test 10:=
{}:*
'''.format('T' * 80).replace('\n', '\r\n'))


class TestViews5(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

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
            '''\
Test 1:*
Test 2:<
Test 3:>
Test 4:=
'''.replace('\n', '\r\n'))
