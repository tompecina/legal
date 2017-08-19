# -*- coding: utf-8 -*-
#
# tests/test_sir.py
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
from datetime import datetime
from os.path import join

from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TransactionTestCase, TestCase
from django.contrib.auth.models import User

from legal.settings import TEST_DATA_DIR
from legal.common.glob import LOCAL_DOMAIN
from legal.sir import cron, glob, models

from tests.utils import link_equal, setdl, setpr, getdl, getpr, check_html


APP = __package__.rpartition('.')[2]


class DummyTag:

    def __init__(self, s):
        self.string = s


class TestCron1(SimpleTestCase):

    def test_convdt(self):

        self.assertEqual(
            cron.convdt(DummyTag('2016-01-17T14:16:59.315489')),
            datetime(2016, 1, 17, 14, 16, 59))

    def test_convd(self):

        self.assertEqual(
            cron.convd(DummyTag('2016-01-17T14:16:59.315489')),
            datetime(2016, 1, 17))


def populate():

    setdl(472015)
    cron.cron_gettr()
    setdl(5772013)
    cron.cron_gettr()
    setdl(160462011)
    cron.cron_gettr()
    setdl(191242016)
    cron.cron_gettr()
    cron.cron_proctr()


class TestCron2(TransactionTestCase):

    def test_refresh_link(self):

        populate()
        print(models.Vec.objects.all())
        self.assertEqual(cron.refresh_link(models.Vec.objects.get(bc=16046)), 3)
        self.assertEqual(cron.refresh_link(models.Vec.objects.get(bc=16046)), 4)
        self.assertEqual(cron.refresh_link(models.Vec.objects.get(bc=577)), 1)


class TestCron3(TestCase):

    fixtures = ('sir_test3.json',)

    def test_cron_refresh_links(self):

        cron.REFRESH_BATCH = 1
        cron.cron_refresh_links()
        self.assertTrue(models.Vec.objects.get(pk=1).refreshed)
        self.assertEqual(
            models.Vec.objects.get(pk=1).link,
            'https://isir.justice.cz/isir/ueu/evidence_upadcu_detail.do?id=de4aeeca-801c-4c52-9305-bc7746f532c5')
        self.assertFalse(models.Vec.objects.get(pk=2).refreshed)
        self.assertEqual(
            models.Vec.objects.get(pk=2).link,
            "https://isir.justice.cz/isir/ueu/evidence_upadcu_detail.do?id=7ba95b84-15ae-4a8e-8339-1918eac00c89")
        cron.cron_refresh_links()
        self.assertTrue(models.Vec.objects.get(pk=2).refreshed)
        self.assertEqual(
            models.Vec.objects.get(pk=2).link,
            'https://isir.justice.cz/isir/ueu/evidence_upadcu_detail.do?id=de4aeeca-801c-4c52-9305-bc7746f532c6')
        self.assertTrue(models.Vec.objects.get(pk=2).refreshed)


class TestCron4(TransactionTestCase):

    def test_update(self):

        setdl(472015)
        cron.cron_gettr()
        self.assertEqual(getdl(), 472015)
        self.assertEqual(models.Transaction.objects.count(), 115)

        setpr(-1)
        cron.cron_proctr()
        self.assertEqual(getdl(), 25707639)
        self.assertEqual(getpr(), -1)
        self.assertEqual(models.Vec.objects.count(), 1)
        self.assertEqual(models.Osoba.objects.count(), 11)
        self.assertEqual(models.Role.objects.count(), 11)
        self.assertEqual(models.Adresa.objects.count(), 3)

        cron.cron_deltr()
        self.assertFalse(models.Transaction.objects.exists())

        cron.cron_getws2()
        self.assertGreater(getpr(), 0)
        self.assertEqual(
            models.Vec.objects.first().link,
            'https://isir.justice.cz/isir/ueu/evidence_upadcu_detail.do?id=7ba95b84-15ae-4a8e-8339-1918eac00c84')

        setdl(5772013)
        cron.cron_gettr()
        cron.cron_proctr()
        cron.cron_deltr()
        self.assertEqual(models.Vec.objects.count(), 2)

        cron.cron_delerr()
        self.assertEqual(models.Vec.objects.count(), 1)

        setdl(-1)
        cron.cron_update()
        self.assertEqual(models.DruhAdresy.objects.count(), 3)
        self.assertEqual(models.Adresa.objects.count(), 11)
        self.assertEqual(models.DruhRoleVRizeni.objects.count(), 3)
        self.assertEqual(models.Osoba.objects.count(), 49)
        self.assertEqual(models.Role.objects.count(), 49)
        self.assertEqual(models.DruhStavRizeni.objects.count(), 4)
        self.assertEqual(models.Vec.objects.count(), 37)
        self.assertEqual(models.Transaction.objects.count(), 1)


class TestCron5(TestCase):

    fixtures = ('sir_test1.json',)

    def test_sir_notice(self):

        populate()
        self.assertEqual(models.Tracked.objects.count(), 2)
        self.assertTrue(models.Tracked.objects.filter(desc__contains='47/2015').exists())
        self.assertTrue(models.Tracked.objects.filter(desc__contains='577/2013').exists())
        self.assertEqual(cron.sir_notice(1), '')

        setpr(-1)
        cron.cron_getws2()
        self.assertEqual(
            cron.sir_notice(1),
            'Došlo ke změně v těchto insolvenčních řízeních, která sledujete:\n\n'
            ' - Test 47/2015, sp. zn. KSPA 56 INS 47/2015\n'
            '   https://isir.justice.cz/isir/ueu/evidence_upadcu_detail.do?id=7ba95b84-15ae-4a8e-8339-1918eac00c84\n\n')
        self.assertEqual(models.Tracked.objects.count(), 1)


class TestGlob(SimpleTestCase):

    def test_l2n(self):

        self.assertEqual(len(glob.L2N), len(glob.COURTS))
        self.assertEqual(glob.L2N['KSSCEUL'], 'Krajský soud v Ústí nad Labem')

    def test_l2r(self):

        self.assertEqual(len(glob.L2R), len(glob.COURTS))
        self.assertEqual(glob.L2R['KSSECULP1'], 'KSSCEUL')

    def test_l2s(self):

        self.assertEqual(len(glob.L2S), len(glob.COURTS))
        self.assertEqual(glob.L2S['KSSCEUL'], 'KSUL')

    def test_selist(self):

        self.assertEqual(len(glob.SERVICE_EVENTS), len(glob.SELIST))
        self.assertTrue(642 in glob.SELIST)

    def test_s2d(self):

        self.assertEqual(len(glob.S2D), len(glob.STATES))
        self.assertEqual(glob.S2D['ZRUŠENO VS'], 'Zrušeno vrchním soudem')

    def test_r2i(self):

        self.assertEqual(len(glob.R2I), len(glob.ROLES))
        self.assertEqual(glob.R2I['trustee'], 'SPRÁVCE')

    def test_r2d(self):

        self.assertEqual(len(glob.R2D), len(glob.ROLES))
        self.assertEqual(glob.R2D['SPRÁVCE'], 'správce')

    def test_a2d(self):

        self.assertEqual(len(glob.A2D), len(glob.ADDRESSES))
        self.assertEqual(glob.A2D['POBOČKA'], 'pobočka')


class TestModels(TestCase):

    fixtures = ('sir_test2.json',)

    def test_models(self):

        self.assertEqual(
            str(models.DruhAdresy.objects.first()),
            'SÍDLO ORG.')

        self.assertEqual(
            str(models.Adresa.objects.first()),
            'Plzeň')

        self.assertEqual(
            str(models.DruhRoleVRizeni.objects.first()),
            'DLUŽNÍK')

        self.assertEqual(
            str(models.Osoba.objects.first()),
            'Romské informační centrum')

        self.assertEqual(
            str(models.Role.objects.first()),
            'Romské informační centrum, DLUŽNÍK')

        self.assertEqual(
            str(models.DruhStavRizeni.objects.first()),
            'ÚPADEK')

        self.assertEqual(
            str(models.Vec.objects.first()),
            'KSSEMOS, 8 INS 1/2008')

        self.assertEqual(
            str(models.Counter.objects.first()),
            'DL: 27660755')

        self.assertEqual(
            str(models.Transaction.objects.first()),
            '27660656, INS 20806/2015')

        self.assertEqual(
            str(models.Insolvency.objects.first()),
            'INS 14515/2016')

        self.assertEqual(
            str(models.Tracked.objects.first()),
            'Test')


class TestViews1(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()
    def test_insform(self):

        res = self.client.get('/sir/insform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/insform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/insform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/insform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sir_insform.html')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Nové řízení')

        res = self.client.post(
            '/sir/insform/',
            {'year': '2016',
             'desc': 'Test',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'number': '1',
             'desc': 'Test',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'number': '1',
             'year': '2016',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'number': '0',
             'year': '2016',
             'desc': 'Test',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'number': '1',
             'year': '2007',
             'desc': 'Test',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insform.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'submit_back': 'Zpět bez uložení'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insform/',
            {'number': '1',
             'year': '2016',
             'desc': 'Test',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        ins_id = models.Insolvency.objects.create(
            uid=self.user,
            number=1,
            year=2016,
            desc='Test 2').id

        res = self.client.get('/sir/insform/{:d}/'.format(ins_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sir_insform.html')
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select('h1')
        self.assertEqual(len(title), 1)
        self.assertEqual(title[0].text, 'Úprava řízení')

        res = self.client.post(
            '/sir/insform/{:d}/'.format(ins_id),
            {'number': '8',
             'year': '2011',
             'desc': 'Test 8',
             'detailed': 'on',
             'submit': 'Uložit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        ins = models.Insolvency.objects.get(pk=ins_id)
        self.assertEqual(ins.number, 8)
        self.assertEqual(ins.year, 2011)
        self.assertEqual(ins.desc, 'Test 8')
        self.assertTrue(ins.detailed)

    def test_insdel(self):

        ins_id = models.Insolvency.objects.create(
            uid=self.user,
            number=1,
            year=2016,
            desc='Test').id

        res = self.client.get('/sir/insdel/{:d}'.format(ins_id))
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/insdel/{:d}/'.format(ins_id))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/insdel/{:d}/'.format(ins_id), follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/insdel/{:d}/'.format(ins_id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insdel.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insdel/{:d}/'.format(ins_id),
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insdel/{:d}/'.format(ins_id),
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insdeleted.html')
        self.assertFalse(models.Insolvency.objects.filter(pk=ins_id).exists())
        check_html(self, res.content)

        res = self.client.post('/sir/insdel/{:d}/'.format(ins_id))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_insdelall(self):

        models.Insolvency.objects.create(
            uid=self.user,
            number=1,
            year=2016,
            desc='Test 1')

        models.Insolvency.objects.create(
            uid=self.user,
            number=2,
            year=2016,
            desc='Test 2')

        self.assertEqual(models.Insolvency.objects.count(), 2)

        res = self.client.get('/sir/insdelall')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/insdelall/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/insdelall/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/insdelall/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insdelall.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insdelall/',
            {'submit_no': 'Ne'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insdelall/',
            {'submit_yes': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)
        self.assertEqual(models.Insolvency.objects.count(), 2)

        res = self.client.post(
            '/sir/insdelall/',
            {'submit_yes': 'Ano',
             'conf': 'ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)
        self.assertEqual(models.Insolvency.objects.count(), 2)

        res = self.client.post(
            '/sir/insdelall/',
            {'submit_yes': 'Ano',
             'conf': 'Ano'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)
        self.assertFalse(models.Insolvency.objects.exists())

    def test_insbatchform(self):

        models.Insolvency.objects.create(
            uid=self.user,
            number=1,
            year=2016,
            desc='Test 1')

        models.Insolvency.objects.create(
            uid=self.user,
            number=4,
            year=2011,
            desc='Test 4')

        models.Insolvency.objects.create(
            uid=self.user,
            number=5,
            year=2012,
            desc='Test 4')

        res = self.client.get('/sir/insbatchform')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/insbatchform/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/insbatchform/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/insbatchform/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insbatchform.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/insbatchform/',
            {'submit_load': 'Načíst'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insbatchform.html')
        self.assertContains(res, 'Nejprve zvolte soubor k načtení')
        check_html(self, res.content)

        with open(join(TEST_DATA_DIR, 'sir_import.csv'), 'rb') as infile:
            res = self.client.post(
                '/sir/insbatchform/',
                {'submit_load': 'Načíst',
                 'load': infile},
                follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_insbatchresult.html')
        self.assertEqual(models.Insolvency.objects.count(), 6)
        self.assertEqual(res.context['count'], 4)
        self.assertEqual(
            res.context['errors'],
            [(3, 'Chybné běžné číslo'),
             (4, 'Chybný ročník'),
             (6, 'Chybný údaj pro pole Vše'),
             (7, 'Prázdný popis'),
             (8, 'Popisu "Test 4" odpovídá více než jedno řízení'),
             (11, 'Příliš dlouhý popis')])
        check_html(self, res.content)

        res = self.client.get('/sir/insexport/')
        self.assertEqual(
            res.content.decode('utf-8'),
            '''\
Test 1,3,2010,ne
Test 2,2,2013,ano
Test 3,3,2014,ano
Test 4,4,2011,ne
Test 4,5,2012,ne
{},57,2012,ano
'''.format('T' * 255).replace('\n', '\r\n'))

    def test_insexport(self):

        models.Insolvency.objects.create(
            uid=self.user,
            number=1,
            year=2016,
            desc='Test 1')

        models.Insolvency.objects.create(
            uid=self.user,
            number=2,
            year=2011,
            detailed=True,
            desc='Test 2')

        res = self.client.get('/sir/insexport')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/insexport/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/insexport/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/insexport/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')
        self.assertEqual(res.content.decode('utf-8'), 'Test 1,1,2016,ne\r\nTest 2,2,2011,ano\r\n')


class TestViews2(TransactionTestCase):

    def setUp(self):
        User.objects.create_user('user', 'user@' + LOCAL_DOMAIN, 'none')
        self.user = User.objects.first()

    def tearDown(self):
        self.client.logout()

    def test_mainpage(self):

        res = self.client.get('/sir')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/sir/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/sir/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/',
            {'email': 'xxx',
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertContains(res, 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/sir/',
            {'email': 'alt@' + LOCAL_DOMAIN,
             'submit': 'Změnit'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.user = User.objects.first()
        self.assertEqual(self.user.email, 'alt@' + LOCAL_DOMAIN)
        check_html(self, res.content)

        res = self.client.get('/sir/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertFalse(soup.select('table#list'))
        models.Insolvency(
            uid=self.user,
            number=13287,
            year=2016,
            desc='Test').save()

        res = self.client.get('/sir/')
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(soup.select('table#list tbody tr')), 1)
        for number in range(200, 437):
            models.Insolvency(
                uid=self.user,
                number=number,
                year=2016,
                desc='Test {:d}'.format(number)).save()

        res = self.client.get('/sir/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sir/insform/')
        self.assertTrue(link_equal(links[1]['href'], '/sir/?start=50'))
        self.assertTrue(link_equal(links[2]['href'], '/sir/?start=200'))

        res = self.client.get('/sir/?start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sir/insform/')
        self.assertTrue(link_equal(links[1]['href'], '/sir/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sir/?start=0'))
        self.assertTrue(link_equal(links[3]['href'], '/sir/?start=100'))
        self.assertTrue(link_equal(links[4]['href'], '/sir/?start=200'))

        res = self.client.get('/sir/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 5)
        self.assertEqual(links[0]['href'], '/sir/insform/')
        self.assertTrue(link_equal(links[1]['href'], '/sir/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sir/?start=50'))
        self.assertTrue(link_equal(links[3]['href'], '/sir/?start=150'))
        self.assertTrue(link_equal(links[4]['href'], '/sir/?start=200'))

        res = self.client.get('/sir/?start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 38)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sir/insform/')
        self.assertTrue(link_equal(links[1]['href'], '/sir/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sir/?start=150'))

        res = self.client.get('/sir/?start=500')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'sir_mainpage.html')
        self.assertEqual(len(res.context['rows']), 1)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '/sir/insform/')
        self.assertTrue(link_equal(links[1]['href'], '/sir/?start=0'))
        self.assertTrue(link_equal(links[2]['href'], '/sir/?start=187'))


class TestViews3(TransactionTestCase):

    fixtures = ('sir_test2.json',)

    def test_courts(self):

        res = self.client.get('/sir/courts')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/sir/courts/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'sir_courts.html')
        self.assertEqual(res.context['rows'], [{'name': 'Krajský soud v Ostravě', 'short': 'KSOS'}])
        check_html(self, res.content)
