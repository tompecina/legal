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
from http import HTTPStatus
from datetime import date
from bs4 import BeautifulSoup
from re import compile
from os.path import join
from os import unlink
from common.settings import BASE_DIR
from common.tests import stripxml
from . import cron, forms, glob, models, views

class TestCron1(TestCase):
    fixtures = ['udn_test1.json']
    
    def checkpdf(self, ll):
        fl = []
        for l in ll:
            fn = join(BASE_DIR, 'test', l)
            try:
                with open(fn) as fi:
                    fc = fi.read()
                unlink(fn)
            except:  # pragma: no cover
                fl.append('E: ' + l)
            if not fc[:-1].endswith('/' + l):  # pragma: no cover
                fl.append('C: ' + l)
        self.assertFalse(fl, msg=fl)
        
    def test_update(self):
        cron.update()
        d = models.Decision.objects.all()
        self.assertEqual(len(d), 16)
        self.checkpdf([
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
            ])
        
    def test_find(self):
        cron.find()
        d = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=158,
            year=2015,
            page=33)
        self.assertEqual(len(d), 1)
        self.assertTrue(d[0].anonfilename)
        self.checkpdf(['0046_3As__1600114_20160622142215_prevedeno.pdf'])
        cron.find()

class TestCron2(TestCase):
    fixtures = ['udn_test2.json']
    
    def test_find(self):
        cron.find()
        d = models.Decision.objects.filter(
            senate=8,
            register='As',
            number=158,
            year=2015,
            page=33)
        self.assertEqual(len(d), 1)
        self.assertFalse(d[0].anonfilename)

class TestForms(SimpleTestCase):

    def test_MainForm(self):
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'format': 'html'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.6.2001',
             'format': 'html'})
        self.assertFalse(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '3.3.2005',
             'format': 'html'})
        self.assertTrue(f.is_valid())
        f = forms.MainForm(
            {'party_opt': 'icontains',
             'date_from': '2.3.2005',
             'date_to': '2.3.2005',
             'format': 'html'})
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

def link_equal(a, b):
    a = a.split('?')
    b = b.split('?')
    if a[0] != b[0]:  # pragma: no cover
        return False
    a = a[1].split('&')
    a.sort()
    b = b[1].split('&')
    b.sort()
    if len(a) != len(b):  # pragma: no cover
        return False
    for i in range(len(a)):
        if a[i] != b[i]:  # pragma: no cover
            return False
    return True

x0 = '<?xml version="1.0" encoding="utf-8"?>\n' \
     '<decisions application="udn" created="2016-08-04T00:20:47" ' \
     'version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:' \
     '//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:' \
     '//legal.pecina.cz https://legal.pecina.cz/static/udn-1.0.xsd">' \
     '</decisions>\n'

x1 = '<?xml version="1.0" encoding="utf-8"?>\n' \
     '<decisions application="udn" created="2016-08-04T00:20:47" ' \
     'version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:' \
     '//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:' \
     '//legal.pecina.cz https://legal.pecina.cz/static/udn-1.0.xsd">' \
     '<decision><court id="NSS">Nejvyšší správní soud</court><date>' \
     '2199-07-01</date><ref>8 As 158/2015-33</ref><agenda>Ochrana ' \
     'hospodářské soutěže a veřejné zakázky</agenda><parties><party>' \
     'Úřad pro ochranu hospodářské soutěže</party><party>BUREAU VERITAS ' \
     'CZECH REPUBLIC, spol. s r.o.</party><party>Zlínský kraj</party>' \
     '</parties><files><file type="abridged">https://legal.pecina.cz/' \
     'repo/udn/0158_8As__1500033S.pdf</file></files></decision></decisions>\n'

x2 = '<?xml version="1.0" encoding="utf-8"?>\n' \
     '<decisions application="udn" created="2016-08-04T00:20:47" ' \
     'version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:' \
     '//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:' \
     '//legal.pecina.cz https://legal.pecina.cz/static/udn-1.0.xsd">' \
     '<decision><court id="NSS">Nejvyšší správní soud</court><date>' \
     '2199-07-01</date><ref>8 As 158/2015-33</ref><agenda>Ochrana ' \
     'hospodářské soutěže a veřejné zakázky</agenda><parties><party>' \
     'Úřad pro ochranu hospodářské soutěže</party><party>BUREAU VERITAS ' \
     'CZECH REPUBLIC, spol. s r.o.</party><party>Zlínský kraj</party>' \
     '</parties><files><file type="abridged">https://legal.pecina.cz/' \
     'repo/udn/0158_8As__1500033S.pdf</file><file type="anonymized">' \
     'https://legal.pecina.cz/repo/udn/0067_5As__1500054_20151119130217' \
     '_prevedeno.pdf</file></files></decision></decisions>\n'

c0 = 'Soud,Datum,Číslo jednací,Oblast,Účastníci řízení,Zkrácené znění,' \
     'Anonymisované znění\n'

c1 = c0 + 'Nejvyšší správní soud,01.07.2199,8 As 158/2015-33,Ochrana ' \
     'hospodářské soutěže a veřejné zakázky,"Úřad pro ochranu hospodářské ' \
     'soutěže;BUREAU VERITAS CZECH REPUBLIC, spol. s r.o.;Zlínský kraj",' \
     'https://legal.pecina.cz/repo/udn/0158_8As__1500033S.pdf,\n'

c2 = c0 + 'Nejvyšší správní soud,01.07.2199,8 As 158/2015-33,Ochrana ' \
     'hospodářské soutěže a veřejné zakázky,"Úřad pro ochranu hospodářské ' \
     'soutěže;BUREAU VERITAS CZECH REPUBLIC, spol. s r.o.;Zlínský kraj",' \
     'https://legal.pecina.cz/repo/udn/0158_8As__1500033S.pdf,https://' \
     'legal.pecina.cz/repo/udn/0067_5As__1500054_20151119130217_prevedeno.pdf\n'

j0 = '[]'

j1 = '[{"parties": ["\u00da\u0159ad pro ochranu hospod\u00e1\u0159sk' \
     '\u00e9 sout\u011b\u017ee", "BUREAU VERITAS CZECH REPUBLIC, spol. ' \
     's r.o.", "Zl\u00ednsk\u00fd kraj"], "files": {"abridged": "https:' \
     '//legal.pecina.cz/repo/udn/0158_8As__1500033S.pdf"}, "date": ' \
     '"2199-07-01", "court": {"name": "Nejvy\u0161\u0161\u00ed spr' \
     '\u00e1vn\u00ed soud", "id": "NSS"}, "ref": "8 As 158/2015-33", ' \
     '"agenda": "Ochrana hospod\u00e1\u0159sk\u00e9 sout\u011b\u017ee ' \
     'a ve\u0159ejn\u00e9 zak\u00e1zky"}]'

j2 = '[{"parties": ["\u00da\u0159ad pro ochranu hospod\u00e1\u0159sk' \
     '\u00e9 sout\u011b\u017ee", "BUREAU VERITAS CZECH REPUBLIC, spol. ' \
     's r.o.", "Zl\u00ednsk\u00fd kraj"], "files": {"abridged": "https:' \
     '//legal.pecina.cz/repo/udn/0158_8As__1500033S.pdf", "anonymized": ' \
     '"https://legal.pecina.cz/repo/udn/0067_5As__1500054_20151119130217_' \
     'prevedeno.pdf"}, "date": "2199-07-01", "court": {"name": "Nejvy' \
     '\u0161\u0161\u00ed spr\u00e1vn\u00ed soud", "id": "NSS"}, "ref": ' \
     '"8 As 158/2015-33", "agenda": "Ochrana hospod\u00e1\u0159sk\u00e9 ' \
     'sout\u011b\u017ee a ve\u0159ejn\u00e9 zak\u00e1zky"}]'

class TestViews(TestCase):
    fixtures = ['udn_test1.json']
    
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
        res = self.client.get('/udn/list/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get( '/udn/list/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/list/?start=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get(
            '/udn/list/?date_from=2015-01-01&date_to=2199-07-01&register=As&' \
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
        d = models.Decision.objects.get().__dict__
        del d['id'], d['_state']
        for page in range(200, 437):
            d['page'] = page
            models.Decision(**d).save()
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
        res = self.client.get('/udn/xmllist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get( '/udn/xmllist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/xmllist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x0.encode('utf-8')))
        res = self.client.get(
            '/udn/xmllist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x1.encode('utf-8')))
        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')
        res = self.client.get(
            '/udn/xmllist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x2.encode('utf-8')))
        views.EXLIM = 0
        res = self.client.get('/udn/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000
     
    def test_csvlist(self):
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
        res = self.client.get('/udn/csvlist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get( '/udn/csvlist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/csvlist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), c0)
        res = self.client.get(
            '/udn/csvlist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), c1)
        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')
        res = self.client.get(
            '/udn/csvlist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), c2)
        views.EXLIM = 0
        res = self.client.get('/udn/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000

    def test_jsonlist(self):
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
        res = self.client.get('/udn/jsonlist/?register=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?year=1989')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?page=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?agenda=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get( '/udn/jsonlist/?date_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?date_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?party_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)
        res = self.client.get('/udn/jsonlist/?register=Ads')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j0)
        res = self.client.get(
            '/udn/jsonlist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j1)
        models.Decision.objects.update(
            anonfilename='0067_5As__1500054_20151119130217_prevedeno.pdf')
        res = self.client.get(
            '/udn/jsonlist/?date_from=2015-01-01&date_to=2199-07-01&' \
            'register=As&agenda=1&party_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j2)
        views.EXLIM = 0
        res = self.client.get('/udn/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000
