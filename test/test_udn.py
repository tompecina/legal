# -*- coding: utf-8 -*-
#
# test/test_udn.py
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
from datetime import date
from re import compile
from os.path import join
from os import unlink

from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase

from common.glob import LOCAL_SUBDOMAIN, LOCAL_URL, REPO_URL
from common.settings import TEST_TEMP_DIR
from test.utils import strip_xml, link_equal
from udn import cron, forms, glob, models, views


class TestCron(TestCase):

    def checkpdf(self, lst):
        fil = []
        for item in lst:
            filename = join(TEST_TEMP_DIR, item)
            try:
                with open(filename) as infile:
                    filc = infile.read()
                unlink(filename)
                if not filc[:-1].endswith('/' + item):  # pragma: no cover
                    fil.append('C: ' + item)
            except:  # pragma: no cover
                fil.append('E: ' + item)
        self.assertFalse(fil, msg=fil)


class TestCron1(TestCron):

    fixtures = ('udn_test1.json',)

    def test_update(self):

        cron.cron_update()
        dec = models.Decision.objects.all()
        self.assertEqual(len(dec), 16)
        self.checkpdf((
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
            '003810Ads_1600040S.pdf',
            ))


class TestCron2(TestCron):

    fixtures = ('udn_test2.json',)

    def test_find(self):

        cron.cron_find()
        dec = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=159,
            year=2015,
            page=33)
        self.assertEqual(len(dec), 1)
        self.assertTrue(dec[0].anonfilename)
        self.checkpdf(('0046_3As__1600114_20160622142215_prevedeno.pdf',))


class TestCron3(TestCron):

    fixtures = ('udn_test3.json',)

    def test_find(self):

        cron.cron_find()
        dec = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=158,
            year=2015,
            page=33)
        self.assertEqual(len(dec), 1)
        self.assertFalse(dec[0].anonfilename)


class TestForms(SimpleTestCase):

    def test_main_form(self):

        form = forms.MainForm(
            {'party_opt': 'icontains',
             'format': 'html'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.6.2001',
             'format': 'html'})
        self.assertFalse(form.is_valid())

        form = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '3.3.2005',
             'format': 'html'})
        self.assertTrue(form.is_valid())

        form = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.3.2005',
             'format': 'html'})
        self.assertTrue(form.is_valid())


class TestGlob(SimpleTestCase):

    def test_filename_regex(self):

        fre = compile(glob.FILENAME_REGEX)

        cases = (
            'test.pdf',
            '9.pdf',
            'a_b.pdf',
            '0185_6Afs_1500040S.pdf',
            '0067_5As__1500054_20151119130217_prevedeno.pdf',
        )

        err_cases = (
            'a b.pdf',
            'a+b.pdf',
            'a-b.pdf',
            'a/b.pdf',
            'a%b.pdf',
            'a#b.pdf',
            '.pdf',
        )

        for test in cases:
            self.assertIsNotNone(fre.match(test), msg=test)

        for test in err_cases:
            self.assertIsNone(fre.match(test), msg=test)


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


class TestViews(TestCase):

    fixtures = ('udn_test1.json',)

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
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_list.html')

        res = self.client.post(
            '/udn/',
            {'party': 'Ing',
             'party_opt': 'icontains',
             'format': 'html',
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
             'format': 'html',
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
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'udn_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

    def test_htmllist(self):

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

        res = self.client.get('/udn/list/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?register=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?page=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/list/?start=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get(
            '/udn/list/?date_from=2015-01-01&date_to=2199-07-01&register=As&'
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

        dec = models.Decision.objects.get().__dict__
        del dec['id'], dec['_state']
        for page in range(200, 437):
            dec['page'] = page
            models.Decision(**dec).save()

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

    def test_xmllist(self):

        res0 = '''\
<?xml version="1.0" encoding="utf-8"?>
<decisions application="udn" created="2016-08-04T00:20:47" \
version="1.1" xmlns="http://{0}" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//{0} {1}/static/udn-1.0.xsd"></decisions>
'''.format(LOCAL_SUBDOMAIN, LOCAL_URL)

        res1 = '''\
<?xml version="1.0" encoding="utf-8"?>
<decisions application="udn" created="2016-08-04T00:20:47" \
version="1.1" xmlns="http://{0}" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//{0} {1}/static/udn-1.0.xsd">\
<decision><court id="NSS">Nejvyšší správní soud</court><date>\
2199-07-01</date><ref><senate>8</senate><register>As</register>\
<number>158</number><year>2015</year><page>33</page></ref><agenda>\
Ochrana hospodářské soutěže a veřejné zakázky</agenda><parties><party>\
Úřad pro ochranu hospodářské soutěže</party><party>BUREAU VERITAS \
CZECH REPUBLIC, spol. s r.o.</party><party>Zlínský kraj</party>\
</parties><files><file type="abridged">{2}\
udn/0158_8As__1500033S.pdf</file></files></decision></decisions>
'''.format(LOCAL_SUBDOMAIN, LOCAL_URL, REPO_URL)

        res2 = '''\
<?xml version="1.0" encoding="utf-8"?>
<decisions application="udn" created="2016-08-04T00:20:47" \
version="1.1" xmlns="http://{0}" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//{0} {1}/static/udn-1.0.xsd">\
<decision><court id="NSS">Nejvyšší správní soud</court><date>\
2199-07-01</date><ref><senate>8</senate><register>As</register>\
<number>158</number><year>2015</year><page>33</page></ref><agenda>\
Ochrana hospodářské soutěže a veřejné zakázky</agenda><parties><party>\
Úřad pro ochranu hospodářské soutěže</party><party>BUREAU VERITAS \
CZECH REPUBLIC, spol. s r.o.</party><party>Zlínský kraj</party>\
</parties><files><file type="abridged">{2}\
udn/0158_8As__1500033S.pdf</file><file type="anonymized">{2}\
udn/0067_5As__1500054_20151119130217_prevedeno.pdf</file></files>\
</decision></decisions>
'''.format(LOCAL_SUBDOMAIN, LOCAL_URL, REPO_URL)

        res = self.client.get('/udn/xmllist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/udn/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/udn/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/xml; charset=utf-8')

        res = self.client.get('/udn/xmllist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?register=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?page=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/xmllist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(
            strip_xml(res.content),
            strip_xml(res0.encode('utf-8')))

        res = self.client.get(
            '/udn/xmllist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(
            strip_xml(res.content),
            strip_xml(res1.encode('utf-8')))

        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')

        res = self.client.get(
            '/udn/xmllist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(
            strip_xml(res.content),
            strip_xml(res2.encode('utf-8')))

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/udn/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = exlim

    def test_csvlist(self):

        res0 = '''\
Soud,Datum,Číslo jednací,Oblast,Účastníci řízení,Zkrácené znění,\
Anonymisované znění
'''

        res1 = '''\
{}Nejvyšší správní soud,01.07.2199,8 As 158/2015-33,Ochrana \
hospodářské soutěže a veřejné zakázky,"Úřad pro ochranu hospodářské \
soutěže;BUREAU VERITAS CZECH REPUBLIC, spol. s r.o.;Zlínský kraj",\
{}udn/0158_8As__1500033S.pdf,
'''.format(res0, REPO_URL)

        res2 = '''\
{0}Nejvyšší správní soud,01.07.2199,8 As 158/2015-33,Ochrana \
hospodářské soutěže a veřejné zakázky,"Úřad pro ochranu hospodářské \
soutěže;BUREAU VERITAS CZECH REPUBLIC, spol. s r.o.;Zlínský kraj",{1}\
udn/0158_8As__1500033S.pdf,{1}\
udn/0067_5As__1500054_20151119130217_prevedeno.pdf
'''.format(res0, REPO_URL)

        res = self.client.get('/udn/csvlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/udn/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/udn/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')

        res = self.client.get('/udn/csvlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?register=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?page=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/csvlist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(
            res.content.decode('utf-8').replace('\r\n', '\n'),
            res0)

        res = self.client.get(
            '/udn/csvlist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(
            res.content.decode('utf-8').replace('\r\n', '\n'),
            res1)

        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')

        res = self.client.get(
            '/udn/csvlist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(
            res.content.decode('utf-8').replace('\r\n', '\n'),
            res2)

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/udn/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = exlim

    def test_jsonlist(self):

        res0 = '[]'

        res1 = '''\
[{{"parties": ["\u00da\u0159ad pro ochranu hospod\u00e1\u0159sk\
\u00e9 sout\u011b\u017ee", "BUREAU VERITAS CZECH REPUBLIC, spol. \
s r.o.", "Zl\u00ednsk\u00fd kraj"], "files": {{"abridged": "\
{}udn/0158_8As__1500033S.pdf"}}, "date": "2199-07-01", \
"court": {{"name": "Nejvy\u0161\u0161\u00ed spr\u00e1vn\u00ed \
soud", "id": "NSS"}}, "ref": {{"senate": 8, "register": "As", \
"number": 158, "year": 2015, "page": 33}}, "agenda": "Ochrana \
hospod\u00e1\u0159sk\u00e9 sout\u011b\u017ee a ve\u0159ejn\u00e9 \
zak\u00e1zky"}}]\
'''.format(REPO_URL)

        res2 = '''\
[{{"parties": ["\u00da\u0159ad pro ochranu hospod\u00e1\u0159sk\
\u00e9 sout\u011b\u017ee", "BUREAU VERITAS CZECH REPUBLIC, spol. \
s r.o.", "Zl\u00ednsk\u00fd kraj"], "files": {{"abridged": "\
{0}udn/0158_8As__1500033S.pdf", "anonymized": "{0}\
udn/0067_5As__1500054_20151119130217_prevedeno.pdf"}}, "date": \
"2199-07-01", "court": {{"name": "Nejvy\u0161\u0161\u00ed \
spr\u00e1vn\u00ed soud", "id": "NSS"}}, "ref": {{"senate": 8, \
"register": "As", "number": 158, "year": 2015, "page": 33}}, \
"agenda": "Ochrana hospod\u00e1\u0159sk\u00e9 sout\u011b\u017ee \
a ve\u0159ejn\u00e9 zak\u00e1zky"}}]\
'''.format(REPO_URL)

        res = self.client.get('/udn/jsonlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/udn/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/udn/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'application/json; charset=utf-8')


        res = self.client.get('/udn/jsonlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?register=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?page=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?agenda=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/udn/jsonlist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), res0)

        res = self.client.get(
            '/udn/jsonlist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), res1)

        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')

        res = self.client.get(
            '/udn/jsonlist/?date_from=2015-01-01&date_to=2199-07-01&'
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), res2)

        exlim = views.EXLIM
        views.EXLIM = 0
        res = self.client.get('/udn/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = exlim
