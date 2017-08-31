# -*- coding: utf-8 -*-
#
# tests/test_uds.py
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
from datetime import date, datetime
from re import compile
from os.path import join
from os import unlink

from bs4 import BeautifulSoup
from django.apps import apps
from django.test import SimpleTestCase, TransactionTestCase, TestCase

from legal.settings import TEST_TEMP_DIR, BASE_DIR, FULL_CONTENT_TYPE
from legal.common.glob import LOCAL_SUBDOMAIN, LOCAL_URL, REPO_URL
from legal.uds import cron, forms, glob, models, views

from tests.utils import strip_xml, validate_xml, link_equal, check_html


APP = __file__.rpartition('_')[2].partition('.')[0]
APPVERSION = apps.get_app_config(APP).version
with open(join(BASE_DIR, 'legal', APP, 'static', '{}-{}.xsd'.format(APP, APPVERSION)), 'rb') as xsdfile:
    XSD = xsdfile.read()


class TestCron1(TestCase):

    def setUp(self):
        cron.cron_publishers()

    def test_publishers_courts(self):
        cases = (
            'Nejvyšší soud',
            'Vrchní soud v Olomouci',
            'Městský soud Praha',
            'Krajský soud Ostrava',
            'Krajský soud České Budějovice, pobočka Tábor',
            'Obvodní soud Praha 10',
            'Okresní soud Šumperk',
            'Okresní soud Bruntál, pobočka Krnov',
        )

        self.assertEqual(models.Publisher.objects.filter(name__in=cases).count(), len(cases))
        for case, flag in zip(cases, (True, True, False, False, False, False, False, False)):
            self.assertEqual(models.Publisher.objects.get(name=case).high, flag)
        for case, flag in zip(cases, (False, False, False, False, True, True, True, True)):
            self.assertEqual(bool(models.Publisher.objects.get(name=case).reports), flag)
        self.assertEqual(
            models.Publisher.objects.get(name=cases[5]).reports.pubid,
            models.Publisher.objects.get(name=cases[2]).pubid)
        for case, flag in zip(cases, (False, False, False, False, True, False, False, False)):
            self.assertEqual(models.Publisher.objects.get(name=case).subsidiary_region, flag)
        for case, flag in zip(cases, (False, False, False, False, False, False, False, True)):
            self.assertEqual(models.Publisher.objects.get(name=case).subsidiary_county, flag)

    def test_publishers_attorneys(self):

        cases = (
            'Nejvyšší státní zastupitelství',
            'Vrchní státní zastupitelství v Olomouci',
            'Městské státní zastupitelství Praha',
            'Krajské státní zastupitelství Ostrava',
            'Krajské státní zastupitelství České Budějovice, pobočka Tábor',
            'Obvodní státní zastupitelství Praha 10',
            'Okresní státní zastupitelství Šumperk',
        )

        self.assertEqual(models.Publisher.objects.filter(name__in=cases).count(), len(cases))
        for case, flag in zip(cases, (True, True, False, False, False, False, False)):
            self.assertEqual(models.Publisher.objects.get(name=case).high, flag)
        for case, flag in zip(cases, (False, False, False, False, True, True, True)):
            self.assertEqual(bool(models.Publisher.objects.get(name=case).reports), flag)
        self.assertEqual(
            models.Publisher.objects.get(name=cases[5]).reports.pubid,
            models.Publisher.objects.get(name=cases[2]).pubid)
        for case, flag in zip(cases, (False, False, False, False, True, False, False)):
            self.assertEqual(models.Publisher.objects.get(name=case).subsidiary_region, flag)
        for case in cases:
            self.assertFalse(models.Publisher.objects.get(name=case).subsidiary_county)


class TestCron2(SimpleTestCase):

    def test_split_numbers(self):

        cases = (
            (' aj 032 817 -5 eE4,15', [32, 817, 5, 4, 15]),
            ('xxx', []),
            ('', []),
        )

        for case in cases:
            self.assertEqual(cron.split_numbers(case[0]), case[1])

    def test_split_strings(self):

        cases = (
            (' 25přípis.89 Eu265/2015-11text55 ', ['přípis', 'Eu', 'text']),
            ('52 11-?26', []),
            ('', []),
        )

        for case in cases:
            self.assertEqual(cron.split_strings(case[0]), case[1])

    def test_parse_ref(self):

        empty = (None,) * 5
        cases = (
            ('', empty),
            (' 13 C 64 2015-9 ', empty),
            ('/', empty),
            ('1 C 24 e15/2016-17', empty),
            ('21 C 415/2016-17-32', (21, 'C', 415, 2016, 17)),
            ('22 C 415/2016-17', (22, 'C', 415, 2016, 17)),
            ('23 C 415/2016', (23, 'C', 415, 2016, None)),
            ('24 C 415/2016/170', (24, 'C', 415, 2016, 170)),
            ('25 C 415/2016/0', (25, 'C', 415, 2016, None)),
            ('26fj 415/2016/0', (26, 'FJ', 415, 2016, None)),
            ('28přípis C 415/2016-9', (28, 'C', 415, 2016, 9)),
            ('28přípis 415/2016-9', (28, 'PŘÍPIS', 415, 2016, 9)),
            ('usn.29přípis C 415/2016-9', (29, 'C', 415, 2016, 9)),
            ('usn.30přípis P A NC415/2016-9', (30, 'P A NC', 415, 2016, 9)),
            ('1 2415/2016-17', empty),
            ('1 TO 0/2016-17', empty),
            ('1 TO 90/1949-17', empty),
        )

        for case in cases:
            self.assertEqual(cron.parse_ref(case[0]), case[1])


def populate():
    cron.cron_publishers()
    models.Publisher.objects.exclude(pubid=203040).delete()
    cron.cron_update('28.8.2017')


class TestCron3(TestCase):

    def test_update(self):

        populate()
        self.assertEqual(models.Publisher.objects.count(), 1)
        self.assertEqual(models.Agenda.objects.count(), 1)
        self.assertEqual(models.Agenda.objects.first().desc, 'Správa soudu')
        self.assertEqual(models.Document.objects.count(), 1)
        self.assertEqual(
            dict(models.Document.objects.values(
                'docid',
                'publisher',
                'desc',
                'ref',
                'senate',
                'register',
                'number',
                'year',
                'page',
                'agenda',
                'posted',
            )[0]),
            {
                'docid': 82464,
                'publisher': models.Publisher.objects.first().id,
                'desc': 'Rozvrh práce, změna č. 1',
                'ref': '0 SPR 653/2009',
                'senate': 0,
                'register': 'SPR',
                'number': 653,
                'year': 2009,
                'page': None,
                'agenda': models.Agenda.objects.first().id,
                'posted': datetime(2009, 7, 29, 8, 10),
            })
        self.assertEqual(models.File.objects.count(), 1)
        self.assertEqual(
            dict(models.File.objects.values(
                'fileid',
                'document',
                'name',
                'ocr',
            )[0]),
            {
                'fileid': 82788,
                'document': models.Document.objects.first().id,
                'name': 'změna_č._1_RP_.pdf',
                'ocr': False,
            })
        self.assertEqual(models.File.objects.first().text.strip(), 'test pdf')
        
        cron.cron_publishers()
        models.Publisher.objects.exclude(pubid__in=(203040, 203060)).delete()
        cron.cron_update('28.8.2017')
        self.assertEqual(models.Document.objects.count(), 1)
        self.assertEqual(models.File.objects.count(), 1)

        cron.cron_publishers()
        models.Publisher.objects.exclude(pubid=203050).delete()
        cron.cron_update('28.8.2017')
        self.assertEqual(models.Document.objects.count(), 1)
        self.assertEqual(models.File.objects.count(), 1)
        fil = models.File.objects.first()
        self.assertTrue(fil.ocr)
        self.assertEqual(fil.text.strip(), 'test pdf')


class TestForms(SimpleTestCase):

    def test_main_form(self):

        form = forms.MainForm(
            {'desc_opt': 'icontains',
             'date_posted_from': '1.5.2017',
             'date_posted_to': '30.4.2017',
             'format': 'html'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'desc_opt': 'icontains',
             'date_posted_from': '1.5.2017',
             'date_posted_to': '1.5.2017',
             'format': 'html'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'desc_opt': 'icontains',
             'date_posted_from': '1.5.2017',
             'date_posted_to': '2.5.2017',
             'format': 'html'})
        self.assertTrue(form.is_valid())


class TestModels(TestCase):

    def test_models(self):

        populate()
        self.assertEqual(str(models.Publisher.objects.first()), 'Okresní soud Pelhřimov')
        self.assertEqual(str(models.Agenda.objects.first()), 'Správa soudu')
        self.assertEqual(str(models.Document.objects.first()), 'Okresní soud Pelhřimov, 0 SPR 653/2009')
        self.assertEqual(
            str(models.File.objects.first()),
            'Okresní soud Pelhřimov, Rozvrh práce, změna č. 1, změna_č._1_RP_.pdf')


class TestViews1(TestCase):

    def test_mainpage(self):

        res = self.client.get('/uds')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/uds/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'uds_mainpage.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/uds/',
            {'date_posted_from': '1.1.2015',
             'date_posted_to': '1.7.2016',
             'desc_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        check_html(self, res.content)

        res = self.client.post(
            '/uds/',
            {'desc': 'rozvrh',
             'desc_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.redirect_chain[0][1], HTTPStatus.FOUND)
        check_html(self, res.content)
        self.assertTrue(link_equal(res.redirect_chain[0][0], '/uds/list/?desc=rozvrh&desc_opt=icontains&start=0'))

        res = self.client.post(
            '/uds/',
            {'date_posted_from': 'XXX',
             'desc_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_mainpage.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)

        res = self.client.post(
            '/uds/',
            {'date_posted_from': '1.1.2015',
             'date_posted_to': '1.7.2014',
             'desc_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_mainpage.xhtml')
        self.assertEqual(res.context['err_message'], 'Chybné zadání, prosím, opravte údaje')
        check_html(self, res.content)


class TestViews2(TransactionTestCase):

    def test_htmllist(self):

        populate()

        res = self.client.get('/uds/list')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/uds/list/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/uds/list/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], FULL_CONTENT_TYPE)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        check_html(self, res.content)

        res = self.client.get('/uds/list/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?year=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?page=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?date_posted_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?date_posted_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?desc_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/list/?start=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get(
            '/uds/list/?date_posted_from=2005-01-01&date_posted_to=2199-07-01&register=SPR&desc_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?register=T')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 0)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?date_posted_from=2009-07-29')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?date_posted_from=2009-07-30')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 0)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?date_posted_to=2009-07-29')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?date_posted_to=2009-07-28')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 0)
        check_html(self, res.content)

        pub = models.Publisher.objects.first().id
        res = self.client.get('/uds/list/?publisher={:d}'.format(pub))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?publisher={:d}'.format(pub + 1))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 0)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?agenda={:d}'.format(models.Agenda.objects.first().id))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?agenda=9999')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 0)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?desc=ozvrh&desc_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?desc=rozvrh&desc_opt=istartswith')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?desc=1&desc_opt=iendswith')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        res = self.client.get('/uds/list/?desc=rozvrh práce, změna č. 1&desc_opt=iexact')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(res.context['total'], 1)
        check_html(self, res.content)

        doc = models.Document.objects.first().__dict__
        del doc['id'], doc['_state']
        for docid in range(200, 438):
            doc['docid'] = docid
            if docid == 437:
                doc['number'] = 654
            models.Document(**doc).save()

        res = self.client.get('/uds/list/?number=653')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0]['href'], '#')
        self.assertTrue(link_equal(links[1]['href'], '/uds/list/?number=653&start=50'))
        self.assertTrue(link_equal(links[2]['href'], '/uds/list/?number=653&start=200'))

        res = self.client.get('/uds/list/?number=653&start=50')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 5)
        self.assertTrue(link_equal(links[0]['href'], '/uds/list/?number=653&start=0'))
        self.assertTrue(link_equal(links[1]['href'], '/uds/list/?number=653&start=0'))
        self.assertEqual(links[2]['href'], '#')
        self.assertTrue(link_equal(links[3]['href'], '/uds/list/?number=653&start=100'))
        self.assertTrue(link_equal(links[4]['href'], '/uds/list/?number=653&start=200'))

        res = self.client.get('/uds/list/?number=653&start=100')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(len(res.context['rows']), 50)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 5)
        self.assertTrue(link_equal(links[0]['href'], '/uds/list/?number=653&start=0'))
        self.assertTrue(link_equal(links[1]['href'], '/uds/list/?number=653&start=50'))
        self.assertEqual(links[2]['href'], '#')
        self.assertTrue(link_equal(links[3]['href'], '/uds/list/?number=653&start=150'))
        self.assertTrue(link_equal(links[4]['href'], '/uds/list/?number=653&start=200'))

        res = self.client.get('/uds/list/?number=653&start=200')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'uds_list.xhtml')
        self.assertEqual(len(res.context['rows']), 38)
        check_html(self, res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('.list tfoot a')
        self.assertEqual(len(links), 3)
        self.assertTrue(link_equal(links[0]['href'], '/uds/list/?number=653&start=0'))
        self.assertTrue(link_equal(links[1]['href'], '/uds/list/?number=653&start=150'))
        self.assertEqual(links[2]['href'], '#')


class TestViews3(TransactionTestCase):

    def setUp(self):
        populate()

    def test_xmllist(self):

        res0 = '''<?xml version="1.0" encoding="utf-8"?>
<documents application="uds" created="2017-08-31T10:17:35" version="1.0" xmlns="http://{0}" xmlns:xsi="http://www.w\
3.org/2001/XMLSchema-instance" xsi:schemaLocation="{0} {1}/static/uds-1.0.xsd"><document id="82464"><publisher id="\
203040">Okresní soud Pelhřimov</publisher><ref>0 SPR 653/2009</ref><description>Rozvrh práce, změna č. 1</descripti\
on><agenda>Správa soudu</agenda><posted>2009-07-29T08:10:00</posted><files><file id="82788"><name>změna_č._1_RP_.pd\
f</name><url>{2}uds/82788/změna_č._1_RP_.pdf</url></file></files></document></documents>
'''.format(LOCAL_SUBDOMAIN, LOCAL_URL, REPO_URL)

        res = self.client.get('/uds/xmllist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/uds/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/uds/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/xml; charset=utf-8')
        self.assertTrue(validate_xml(res.content, XSD))

        res = self.client.get('/uds/xmllist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?year=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?date_posted_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?date_posted_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?desc_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/xmllist/?register=spr')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(strip_xml(res.content), strip_xml(res0.encode('utf-8')))
        self.assertTrue(validate_xml(res.content, XSD))

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/uds/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.xhtml')
        check_html(self, res.content)
        views.EXLIM = exlim

    def test_csvlist(self):

        res0 = '''Datum vyvěšení,Soud/státní zastupitelství,Popis dokumentu,Spisová značka/číslo jednací,Agenda,\
Soubory
'''

        res1 = '''{}29.07.2009 08:10:00,Okresní soud Pelhřimov,"Rozvrh práce, změna č. 1",0 SPR 653/2009,Správa \
soudu,{}uds/82788/změna_č._1_RP_.pdf
'''.format(res0, REPO_URL)

        res = self.client.get('/uds/csvlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/uds/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/uds/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')

        res = self.client.get('/uds/csvlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?year=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?date_posted_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?date_posted_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?desc_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/csvlist/?register=spr')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), res1)

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/uds/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.xhtml')
        check_html(self, res.content)
        views.EXLIM = exlim

    def test_jsonlist(self):

        res1 = '''[{{"posted": "2009-07-29T08:10:00", "publisher": "Okresn\u00ed soud Pelh\u0159imov", "desc": "Roz\
vrh pr\u00e1ce, zm\u011bna \u010d. 1", "ref": "0 SPR 653/2009", "agenda": "Spr\u00e1va soudu", "files": [{{"id": 82\
788, "name": "zm\u011bna_\u010d._1_RP_.pdf", "url": "{}uds/82788/změna_č._1_RP_.pdf"}}]}}]'''.format(REPO_URL)

        res = self.client.get('/uds/jsonlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/uds/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/uds/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'application/json; charset=utf-8')

        res = self.client.get('/uds/jsonlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?year=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?date_posted_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?date_posted_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?desc_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/uds/jsonlist/?register=spr')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), res1)

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/uds/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.xhtml')
        check_html(self, res.content)
        views.EXLIM = exlim
