# -*- coding: utf-8 -*-
#
# tests/test_sur.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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
from os import unlink

from bs4 import BeautifulSoup
from django.test import TransactionTestCase, TestCase
from django.contrib.auth.models import User

from legal.settings import TEST_DATA_DIR, TEST_TEMP_DIR, FULL_CONTENT_TYPE
from legal.common.glob import LOCAL_DOMAIN
from legal.psj.cron import cron_schedule, cron_update as psj_update
from legal.psj.models import Task, Hearing
from legal.udn.cron import cron_update as udn_update
from legal.udn.models import Decision
from legal.sur import cron, models

from tests.utils import link_equal, check_html


APP = __package__.rpartition('.')[2]


def cleanup():
    for filename in (
            '0002_8As__1600055S.pdf',
            '0022_4As__1600037S.pdf',
            '0025_8As__1600041S.pdf',
            '0037_4Afs_1600033S.pdf',
            '003810Ads_1600040S.pdf',
            '0065_4Afs_1600032S.pdf',
            '0066_4Afs_1600033S.pdf',
            '0079_8As__1600023S.pdf',
            '008110As__1600026S.pdf',
            '0095_4Afs_1600035S.pdf',
            '0108_5As__1600008S.pdf',
            '0152_4Ads_1500027S.pdf',
            '0158_8As__1500033S.pdf',
            '019110As__1500030S.pdf',
            '0208_4Ads_1500082S.pdf',
            '0233_5As__1500046S.pdf',
    ):
        unlink(join(TEST_TEMP_DIR, filename))


class TestCron(TestCase):

    fixtures = ('sur_test.json',)

    def test_sur_notice(self):

        cases = (
            ('Jč', 0, 166, 166, 166, 234, 261),
            ('jČ', 0, 166, 166, 166, 234, 261),
            ('B', 1, 38, 108, 134, 158),
            ('b', 1, 38, 108, 134, 158),
            ('ová', 2, 38, 152, 166, 166, 233, 234, 261, 363, 485),
            ('OVÁ', 2, 38, 152, 166, 166, 233, 234, 261, 363, 485),
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
            self.assertEqual(tuple(models.Found.objects.order_by('number').values_list('number', flat=True)), test[2:])

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
            '''Byli nově zaznamenáni tito účastníci řízení, které sledujete:

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
        cleanup()


class TestModels(TransactionTestCase):

    fixtures = ('sur_test.json',)

    def test_models(self):

        models.Party(uid_id=1, party='ová', party_opt=0).save()
        udn_update()
        self.assertEqual(str(models.Party.objects.first()), 'ová')
        self.assertEqual(str(models.Found.objects.first()), 'Nejvyšší správní soud, 4 Ads 208/2015')
        cleanup()


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
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/',
            {'email': 'xxx',
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
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
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(soup.select('table#list tbody tr')), 1)
        for number in range(200, 437):
            models.Party(uid=self.user, party_opt=0, party='Test {:d}'.format(number)).save()

        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertEqual(links[1]['href'], '#')
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=50'))
        self.assertTrue(link_equal(links[3]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 6)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=0'))
        self.assertEqual(links[3]['href'], '#')
        self.assertTrue(link_equal(links[4]['href'], '/sur/?start=100'))
        self.assertTrue(link_equal(links[5]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 6)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=50'))
        self.assertEqual(links[3]['href'], '#')
        self.assertTrue(link_equal(links[4]['href'], '/sur/?start=150'))
        self.assertTrue(link_equal(links[5]['href'], '/sur/?start=200'))

        res = self.client.get('/sur/?start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(len(res.context['rows']), 38)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=150'))
        self.assertEqual(links[3]['href'], '#')

        res = self.client.get('/sur/?start=500')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(len(res.context['rows']), 1)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0]['href'], '/sur/partyform/')
        self.assertTrue(link_equal(links[1]['href'], '/sur/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sur/?start=187'))
        self.assertEqual(links[3]['href'], '#')


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
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/partyform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'sur_partyform.xhtml')
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
        self.assertTemplateUsed(res, 'sur_partyform.xhtml')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.xhtml')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'XXX',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partyform.xhtml')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partyform/',
            {'party': 'Test',
             'party_opt': 'icontains',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')

        party_id = models.Party.objects.create(
            uid=self.user,
            party_opt=0,
            party='Test 2').id

        res = self.client.get('/sur/partyform/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'sur_partyform.xhtml')
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
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        party = models.Party.objects.get(pk=party_id)
        self.assertEqual(party.party, 'Test 8')


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
        self.assertTemplateUsed(res, 'login.xhtml')
        check_html(self, res.content)

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/partydel/{:d}/'.format(party_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydel.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')

        res = self.client.post(
            '/sur/partydel/{:d}/'.format(party_id),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydeleted.xhtml')
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
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/partydelall/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partydelall.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(models.Party.objects.count(), 2)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        self.assertEqual(models.Party.objects.count(), 2)

        res = self.client.post(
            '/sur/partydelall/',
            {'submit_yes': 'Ano',
             'conf': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
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
        self.assertTemplateUsed(res, 'login.xhtml')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sur/partybatchform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_load': 'Načíst'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.xhtml')
        self.assertContains(res, 'Nejprve zvolte soubor k načtení')
        check_html(self, res.content)

        res = self.client.post(
            '/sur/partybatchform/',
            {'submit_xxx': 'XXX'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchform.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'sur_import.csv'), 'rb') as infile:
            res = self.client.post(
                '/sur/partybatchform/',
                {'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_partybatchresult.xhtml')
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


class TestViews6(TransactionTestCase):

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
        self.assertTemplateUsed(res, 'login.xhtml')

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


class TestViews7(TransactionTestCase):

    fixtures = ('sur_test.json',)

    def test_highlight(self):

        models.Party.objects.create(
            uid_id=1,
            party='Test 1',
            party_opt=0)

        models.Party.objects.create(
            uid_id=1,
            party='Test 2',
            party_opt=1)

        models.Party.objects.create(
            uid_id=1,
            party='Test 3',
            party_opt=2)

        models.Party.objects.create(
            uid_id=1,
            party='Test 4',
            party_opt=3)

        self.client.force_login(User.objects.get(pk=1))
        models.Party.objects.filter(party='Test 3').update(notify=True)
        res = self.client.get('/sur/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sur_mainpage.xhtml')
        soup = BeautifulSoup(res.content, 'html.parser')
        highlight = soup.find_all('td', 'highlight')
        self.assertEqual(len(highlight), 1)
        self.assertEqual(highlight[0].text, 'Test 3')
