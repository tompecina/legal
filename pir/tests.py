# -*- coding: utf-8 -*-
#
# pir/tests.py
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
from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase
from common.tests import stripxml, link_equal, setpr, getpr
from sir.tests import populate
from sir.cron import cron_getws2
from sir.models import Osoba, DruhRoleVRizeni, Vec
from pir import forms, views


class TestForms(SimpleTestCase):

    def test_MainForm(self):

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'party_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_first_from': '2.3.2015',
             'date_first_to': '2.6.2011',
             'format': 'html'})
        self.assertFalse(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_first_from': '2.3.2015',
             'date_first_to': '3.3.2015',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_first_from': '2.3.2015',
             'date_first_to': '2.3.2015',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'party_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_last_from': '2.3.2015',
             'date_last_to': '2.6.2011',
             'format': 'html'})
        self.assertFalse(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_last_from': '2.3.2015',
             'date_last_to': '3.3.2015',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'date_last_from': '2.3.2015',
             'date_last_to': '2.3.2015',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'party_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1961',
             'format': 'html'})
        self.assertFalse(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1965',
             'format': 'html'})
        self.assertTrue(f.is_valid())

        f = forms.MainForm(
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'year_birth_from': '1965',
             'year_birth_to': '1966',
             'format': 'html'})
        self.assertTrue(f.is_valid())


class TestViews1(SimpleTestCase):

    def test_o2s(self):

        pp = [
            [Osoba(),
             False,
             ''],
            [Osoba(nazevOsoby='Novák'),
             False,
             'Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef'),
             False,
             'Josef Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.'),
             False,
             'Ing. Josef Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.'),
             False,
             'Ing. Josef Novák, CSc.'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO'),
             False,
             'Ing. Josef Novák, CSc., NOWACO'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                datumNarozeni=date(1970, 5, 18)),
             False,
             'Ing. Josef Novák, CSc., NOWACO'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                datumNarozeni=date(1970, 5, 18),
                ic='12345678'),
             False,
             'Ing. Josef Novák, CSc., NOWACO'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                ic='12345678'),
             False,
             'Ing. Josef Novák, CSc., NOWACO'],
            [Osoba(),
             True,
             ''],
            [Osoba(nazevOsoby='Novák'),
             True,
             'Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef'),
             True,
             'Josef Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.'),
             True,
             'Ing. Josef Novák'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.'),
             True,
             'Ing. Josef Novák, CSc.'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO'),
             True,
             'Ing. Josef Novák, CSc., NOWACO'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                datumNarozeni=date(1970, 5, 18)),
             True,
             'Ing. Josef Novák, CSc., NOWACO, nar.&nbsp;18.05.1970'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                datumNarozeni=date(1970, 5, 18),
                ic='12345678'),
             True,
             'Ing. Josef Novák, CSc., NOWACO, nar.&nbsp;18.05.1970'],
            [Osoba(
                nazevOsoby='Novák',
                jmeno='Josef',
                titulPred='Ing.',
                titulZa='CSc.',
                nazevOsobyObchodni='NOWACO',
                ic='12345678'),
             True,
             'Ing. Josef Novák, CSc., NOWACO, IČO:&nbsp;12345678'],
            ]

        for p in pp:
            self.assertEqual(views.o2s(p[0], detailed=p[1]), p[2])


class TestViews2(TestCase):

    def setUp(self):
        populate()
        setpr(-1)
        cron_getws2()

    def test_mainpage(self):

        res = self.client.get('/pir')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/pir/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'pir_mainpage.html')

        res = self.client.post(
            '/pir/',
            {'court': 'KSJIMBM',
             'senate': '81',
             'number': '200',
             'year': '2015',
             'date_first_from': '1.1.2015',
             'date_first_to': '1.7.2016',
             'date_last_from': '1.1.2015',
             'date_last_to': '1.7.2016',
             'name': 'Název',
             'first_name': 'Jméno',
             'city': 'Město',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'genid': '12345678',
             'taxid': 'CZ12345678',
             'birthid': '700101/1234',
             'date_birth': '1.1.1970',
             'year_birth_from': '1950',
             'year_birth_to': '1970',
             'role_debtor': 'on',
             'role_trustee': 'on',
             'role_creditor': 'on',
             'deleted': 'on',
             'creditors': 'on',
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')

        res = self.client.post(
            '/pir/',
            {'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.redirect_chain[0][1], HTTPStatus.FOUND)
        self.assertTrue(link_equal(
            res.redirect_chain[0][0],
            '/pir/list/?start=0'))

        res = self.client.post(
            '/pir/',
            {'name': 'Název',
             'first_name': 'Jméno',
             'city': 'Město',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.redirect_chain[0][1], HTTPStatus.FOUND)
        self.assertTrue(link_equal(
            res.redirect_chain[0][0],
            '/pir/list/?name=N%C3%A1zev&name_opt=icontains'
            '&first_name=Jm%C3%A9no&first_name_opt=icontains'
            '&city=M%C4%9Bsto&city_opt=icontains&start=0'))

        res = self.client.post(
            '/pir/',
            {'date_first_from': 'XXX',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

        res = self.client.post(
            '/pir/',
            {'date_first_from': '1.1.2015',
             'date_first_to': '1.7.2014',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

        res = self.client.post(
            '/pir/',
            {'date_last_from': '1.1.2015',
             'date_last_to': '1.7.2014',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

        res = self.client.post(
            '/pir/',
            {'year_birth_from': '1966',
             'year_birth_to': '1965',
             'name_opt': 'icontains',
             'first_name_opt': 'icontains',
             'city_opt': 'icontains',
             'format': 'html',
             'submit': 'Hledat'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_mainpage.html')
        self.assertEqual(
            res.context['err_message'],
            'Chybné zadání, prosím, opravte údaje')

    def test_g2p(self):

        pr = getpr()
        debtor = DruhRoleVRizeni.objects.get(desc='DLUŽNÍK').id
        trustee = DruhRoleVRizeni.objects.get(desc='SPRÁVCE').id
        creditor = DruhRoleVRizeni.objects.get(desc='VĚŘITEL').id
        motioner = DruhRoleVRizeni.objects.get(desc='VĚŘIT-NAVR').id

        rr = [
            [
                {},
                {'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'court': 'KSJIMBM',
                 'senate': '24',
                 'number': '200',
                 'year': '2010',
                 'date_first_from': '2014-04-22',
                 'date_first_to': '2014-04-23',
                 'date_last_from': '2014-04-24',
                 'date_last_to': '2014-04-25',
                 'name': 'Název',
                 'name_opt': 'icontains',
                 'first_name': 'Jméno',
                 'first_name_opt': 'istartswith',
                 'city': 'Město',
                 'city_opt': 'iendswith',
                 'genid': '12345678',
                 'taxid': 'CZ12345678',
                 'birthid': '700101/1234',
                 'date_birth': '1970-05-18',
                 'year_birth_from': '1970',
                 'year_birth_to': '1971',
                 'deleted': 'on'},
                {'idOsobyPuvodce': 'KSJIMBM',
                 'senat': 24,
                 'bc': 200,
                 'rocnik': 2010,
                 'firstAction__gte': date(2014, 4, 22),
                 'firstAction__lte': date(2014, 4, 23),
                 'lastAction__gte': date(2014, 4, 24),
                 'lastAction__lte': date(2014, 4, 25),
                 'roles__osoba__nazevOsoby__icontains': 'Název',
                 'roles__osoba__jmeno__istartswith': 'Jméno',
                 'roles__osoba__adresy__mesto__iendswith': 'Město',
                 'roles__osoba__ic': '12345678',
                 'roles__osoba__dic': 'CZ12345678',
                 'roles__osoba__rc': '700101/1234',
                 'roles__osoba__datumNarozeni': date(1970, 5, 18),
                 'roles__osoba__datumNarozeni__year__gte': '1970',
                 'roles__osoba__datumNarozeni__year__lte': '1971',
                 'roles__druhRoleVRizeni__in': [],
                 'id__lte': pr}],
            [
                {'role_debtor': 'on',
                 'role_trustee': 'on',
                 'role_creditor': 'on'},
                {'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'name': 'Název',
                 'name_opt': 'icontains',
                 'role_debtor': 'on'},
                {'roles__osoba__nazevOsoby__icontains': 'Název',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'first_name': 'Jméno',
                 'first_name_opt': 'icontains',
                 'role_debtor': 'on'},
                {'roles__osoba__jmeno__icontains': 'Jméno',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'city': 'Město',
                 'city_opt': 'icontains',
                 'role_debtor': 'on'},
                {'roles__osoba__adresy__mesto__icontains': 'Město',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'genid': '12345678',
                 'role_debtor': 'on'},
                {'roles__osoba__ic': '12345678',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'taxid': 'CZ12345678',
                 'role_debtor': 'on'},
                {'roles__osoba__dic': 'CZ12345678',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'birthid': '700101/1234',
                 'role_debtor': 'on'},
                {'roles__osoba__rc': '700101/1234',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'date_birth': '1970-05-18',
                 'role_debtor': 'on'},
                {'roles__osoba__datumNarozeni': date(1970, 5, 18),
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'year_birth_from': '1970',
                 'role_debtor': 'on'},
                {'roles__osoba__datumNarozeni__year__gte': '1970',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'year_birth_to': '1971',
                 'role_debtor': 'on'},
                {'roles__osoba__datumNarozeni__year__lte': '1971',
                 'roles__druhRoleVRizeni__in': [debtor],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'genid': '12345678',
                 'role_trustee': 'on'},
                {'roles__osoba__ic': '12345678',
                 'roles__druhRoleVRizeni__in': [trustee],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'genid': '12345678',
                 'role_creditor': 'on'},
                {'roles__osoba__ic': '12345678',
                 'roles__druhRoleVRizeni__in': [creditor, motioner],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
            [
                {'genid': '12345678',
                 'role_debtor': 'on',
                 'role_trustee': 'on',
                 'role_creditor': 'on'},
                {'roles__osoba__ic': '12345678',
                 'roles__druhRoleVRizeni__in':
                 [debtor, trustee, creditor, motioner],
                 'datumVyskrtnuti__isnull': True,
                 'id__lte': pr}],
        ]

        ee = [
            {'senate': '-1'},
            {'senate': 'XXX'},
            {'number': '0'},
            {'number': 'XXX'},
            {'year': '2007'},
            {'year': 'XXX'},
            {'date_first_from': 'XXX'},
            {'date_first_from': '2011-02-29'},
            {'name_opt': 'XXX'},
            {'first_name_opt': 'XXX'},
            {'city_opt': 'XXX'},
            {'name': 'XXX'},
            {'first_name': 'XXX'},
            {'city': 'XXX'},
            {'date_birth': 'XXX'},
            {'date_birth': '2011-02-29'},
        ]

        for p in rr:
            self.assertEqual(views.g2p(p[0]), p[1])

        for p in ee:
            try:
                views.g2p(p)
                self.fail(p)  # pragma: no cover
            except:
                pass

    def test_getosoby(self):

        pp = [
            [
                [],
                []],
            [
                ['debtor'],
                ['Bártová']],
            [
                ['trustee'],
                ['Vodrážková']],
            [
                ['creditor'],
                ['AB 4 B.V.',
                 'BNP Paribas Personal Finance SA, odštěpný závod',
                 'Česká spořitelna, a.s.',
                 'ESSOX s.r.o.',
                 'JET Money s.r.o.',
                 'Komerční banka, a.s.',
                 'Makovský',
                 'Provident Financial s. r. o.']],
            [
                ['motioner'],
                []],
            [
                ['debtor', 'trustee', 'creditor', 'motioner'],
                ['AB 4 B.V.',
                 'Bártová',
                 'BNP Paribas Personal Finance SA, odštěpný závod',
                 'Česká spořitelna, a.s.',
                 'ESSOX s.r.o.',
                 'JET Money s.r.o.',
                 'Komerční banka, a.s.',
                 'Makovský',
                 'Provident Financial s. r. o.',
                 'Vodrážková']],
        ]

        for p in pp:
            self.assertEqual(
                list(views.getosoby(Vec.objects.get(bc=47, rocnik=2015),
                    *(p[0])).order_by('nazevOsoby')
                     .values_list('nazevOsoby', flat=True)),
                p[1])

    def test_htmllist(self):

        res = self.client.get('/pir/list')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/pir/list/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/pir/list/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'pir_list.html')

        res = self.client.get('/pir/list/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?year=2007')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?date_first_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?date_first_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?date_last_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?date_last_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?first_name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?city_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?first_name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?city=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?date_birth=1970-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?year_birth_from=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?year_birth_to=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/?start=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/list/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)
        self.assertFalse(res.context['creditors'])

        res = self.client.get('/pir/list/?creditors=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)
        self.assertTrue(res.context['creditors'])

        res = self.client.get('/pir/list/?court=KSVYCHKP1')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?senate=56')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?number=47')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?year=2015')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?date_first_from=2015-01-05')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 2)

        res = self.client.get('/pir/list/?date_first_from=2015-01-06')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?date_first_to=2015-01-05')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 2)

        res = self.client.get('/pir/list/?date_first_to=2015-01-04')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?date_last_from=2016-07-20')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)

        res = self.client.get('/pir/list/?date_last_from=2016-07-21')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 2)

        res = self.client.get('/pir/list/?date_last_to=2016-07-20')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?date_last_to=2016-07-19')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get(
            '/pir/list/?name=Bártová&name_opt=iexact&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get(
            '/pir/list/?name=Bártová&name_opt=iexact')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get(
            '/pir/list/?first_name=Veronika&first_name_opt=iexact'
            '&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get(
            '/pir/list/?first_name=Veronika&first_name_opt=iexact')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get(
            '/pir/list/?city=Litomyšl&city_opt=iexact&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?city=Litomyšl&city_opt=iexact')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?genid=03814742&role_creditor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?genid=03814742')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?taxid=004-13584324&role_creditor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?taxid=004-13584324')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?birthid=8060143487&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?birthid=8060143487')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?date_birth=1980-10-14&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?date_birth=1980-10-14')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?year_birth_from=1980&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 1)

        res = self.client.get('/pir/list/?year_birth_from=1980')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?year_birth_to=1980&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)

        res = self.client.get('/pir/list/?year_birth_to=1980')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get('/pir/list/?name=b&name_opt=icontains')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 0)

        res = self.client.get(
            '/pir/list/?name=k&name_opt=icontains&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 2)

        res = self.client.get(
            '/pir/list/?name=k&name_opt=icontains&role_debtor=on'
            '&role_trustee=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)

        res = self.client.get(
            '/pir/list/?name=k&name_opt=icontains&role_creditor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 3)

        res = self.client.get('/pir/list/?deleted=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(res.context['total'], 4)

        v = Vec.objects.filter(link__isnull=False).first().__dict__
        del v['id'], v['_state']
        for number in range(1200, 1433):
            v['bc'] = number
            o = Vec(**v)
            o.save()
        setpr(o.id)

        res = self.client.get('/pir/list/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 20)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?start=20'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?start=220'))

        res = self.client.get('/pir/list/?creditors=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 10)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?creditors=on&start=10'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?creditors=on&start=230'))

        res = self.client.get('/pir/list/?start=20')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 20)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 4)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?start=0'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/pir/list/?start=40'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/pir/list/?start=220'))

        res = self.client.get('/pir/list/?start=40')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 20)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 4)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?start=20'))
        self.assertTrue(link_equal(
            links[2]['href'],
            '/pir/list/?start=60'))
        self.assertTrue(link_equal(
            links[3]['href'],
            '/pir/list/?start=220'))

        res = self.client.get('/pir/list/?start=220')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 16)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?start=200'))

        res = self.client.get('/pir/list/?start=236')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pir_list.html')
        self.assertEqual(len(res.context['rows']), 1)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = soup.select('tr.footer a')
        self.assertEqual(len(links), 2)
        self.assertTrue(link_equal(
            links[0]['href'],
            '/pir/list/?start=0'))
        self.assertTrue(link_equal(
            links[1]['href'],
            '/pir/list/?start=215'))

    def test_xmllist(self):

        x0 = '''\
<?xml version="1.0" encoding="utf-8"?>
<insolvencies application="pir" created="2016-11-22T15:44:22" \
version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//legal.pecina.cz https://legal.pecina.cz/static/pir-1.0.xsd">\
<insolvency><court id="KSSTCAB">Krajský soud v Praze</court>\
<ref><court>KSPH</court><senate>36</senate><register>INS</register>\
<number>16046</number><year>2011</year></ref>\
<debtors><debtor><name>Hanzlíková</name>\
<first_name>Anděla</first_name><gen_id>74550381</gen_id>\
<birth_date>1975-08-19</birth_date><birth_id>755819/0112</birth_id>\
<addresses><address type="trvalá"><city>Kladno</city>\
<street>Čs. armády</street><street_number>3208</street_number>\
<zip>272 01</zip></address><address type="trvalá">\
<city>okr. Kladno</city><street>Kmetiněves</street>\
<street_number>70</street_number><zip>273 22</zip></address>\
<address type="trvalá"><city>okr. Kladno</city><street>Čs. \
armády</street><street_number>3208</street_number><zip>273 22</zip>\
</address></addresses></debtor></debtors><trustees><trustee>\
<name>Mikeš</name><first_name>Ivan</first_name>\
<honorifics_prepended>Ing.</honorifics_prepended>\
<gen_id>61048232</gen_id><birth_date>1967-06-16</birth_date>\
<addresses><address type="trvalá"><city>Petrov</city>\
<street>U ručiček</street><street_number>306</street_number>\
<country>Česká republika</country><zip>252 81</zip></address>\
<address type="sídlo firmy"><city>Praha 1</city>\
<street>Novotného lávka</street><street_number>5</street_number>\
<district>Hlavní město Praha</district><country>CZE</country>\
<zip>116 68</zip><phone>602530769</phone></address>\
<address type="sídlo firmy"><city>Praha 1</city>\
<street>Novotného lávka</street><street_number>5</street_number>\
<district>Praha 1</district><country>CZE</country><zip>116 68</zip>\
<phone>602530769</phone></address><address type="trvalá">\
<city>Petrov</city><street>U ručiček</street>\
<street_number>306</street_number><district>Praha-západ</district>\
<country>CZE</country><zip>252 81</zip></address></addresses>\
</trustee></trustees></insolvency><insolvency>\
<court id="KSVYCHKP1">Krajský soud v Hradci Králové, pobočka \
v Pardubicích</court><ref><court>KSPA</court><senate>56</senate>\
<register>INS</register><number>47</number><year>2015</year>\
</ref><state>Povoleno oddlužení</state><debtors><debtor>\
<name>Bártová</name><first_name>Veronika</first_name>\
<birth_date>1980-10-14</birth_date><birth_id>806014/3487</birth_id>\
<addresses><address type="trvalá"><city>Litomyšl</city>\
<street>Šmilovského</street><street_number>197</street_number>\
<district>Svitavy</district><zip>570 01</zip>\
<fax>+420-123456789</fax><email>tomas@pecina.cz</email></address>\
</addresses></debtor></debtors><trustees><trustee>\
<name>Vodrážková</name><first_name>Jana</first_name>\
<honorifics_prepended>Ing.</honorifics_prepended>\
<gen_id>74267604</gen_id><birth_date>1977-12-05</birth_date>\
<addresses><address type="trvalá"><city>Chrudim</city>\
<street>Sladkovského</street><street_number>756</street_number>\
<district>Chrudim</district><country>CZE</country>\
<zip>537 01</zip></address><address type="sídlo firmy">\
<city>Chrudim</city><street>Novoměstská</street>\
<street_number>960</street_number><district>Chrudim</district>\
<country>CZE</country><zip>537 01</zip></address></addresses>\
</trustee></trustees></insolvency><insolvency>\
<court id="KSJICCB">Krajský soud v Českých Budějovicích</court>\
<ref><court>KSCB</court><senate>27</senate>\
<register>INS</register><number>19124</number>\
<year>2016</year></ref><state>Před rozhodnutím o úpadku</state>\
<debtors><debtor><name>Sviták</name>\
<first_name>Milan</first_name><gen_id>88176681</gen_id>\
<birth_date>1970-08-13</birth_date>\
<birth_id>700813/2659</birth_id><addresses>\
<address type="sídlo firmy"><city>Bechyně</city>\
<street>Hodonice</street><street_number>65</street_number>\
<zip>391 65</zip></address></addresses></debtor></debtors>\
<trustees></trustees></insolvency></insolvencies>
'''

        x1 = '''\
<?xml version="1.0" encoding="utf-8"?>
<insolvencies application="pir" created="2016-11-22T15:58:43" \
version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//legal.pecina.cz https://legal.pecina.cz/static/pir-1.0.xsd">\
<insolvency><court id="KSVYCHKP1">Krajský soud v Hradci Králové, \
pobočka v Pardubicích</court><ref><court>KSPA</court>\
<senate>56</senate><register>INS</register><number>47</number>\
<year>2015</year></ref><state>Povoleno oddlužení</state>\
<debtors><debtor><name>Bártová</name><first_name>Veronika\
</first_name><birth_date>1980-10-14</birth_date><birth_id>\
806014/3487</birth_id><addresses><address type="trvalá">\
<city>Litomyšl</city><street>Šmilovského</street>\
<street_number>197</street_number><district>Svitavy</district>\
<zip>570 01</zip><fax>+420-123456789</fax><email>tomas@pecina.cz\
</email></address></addresses></debtor></debtors>\
<trustees><trustee><name>Vodrážková</name><first_name>Jana\
</first_name><honorifics_prepended>Ing.</honorifics_prepended>\
<gen_id>74267604</gen_id><birth_date>1977-12-05</birth_date>\
<addresses><address type="trvalá"><city>Chrudim</city>\
<street>Sladkovského</street><street_number>756</street_number>\
<district>Chrudim</district><country>CZE</country>\
<zip>537 01</zip></address><address type="sídlo firmy">\
<city>Chrudim</city><street>Novoměstská</street>\
<street_number>960</street_number><district>Chrudim</district>\
<country>CZE</country><zip>537 01</zip></address></addresses>\
</trustee></trustees></insolvency></insolvencies>
'''

        x2 = '''\
<?xml version="1.0" encoding="utf-8"?>
<insolvencies application="pir" created="2016-11-22T16:03:58" \
version="1.0" xmlns="http://legal.pecina.cz" xmlns:xsi="http:\
//www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http:\
//legal.pecina.cz https://legal.pecina.cz/static/pir-1.0.xsd">\
<insolvency><court id="KSSTCAB">Krajský soud v Praze</court>\
<ref><court>KSPH</court><senate>36</senate><register>INS</register>\
<number>16046</number><year>2011</year></ref>\
<debtors><debtor><name>Hanzlíková</name><first_name>\
Anděla</first_name><gen_id>74550381</gen_id><birth_date>1975-08-19\
</birth_date><birth_id>755819/0112</birth_id><addresses>\
<address type="trvalá"><city>Kladno</city><street>Čs. armády\
</street><street_number>3208</street_number><zip>272 01</zip>\
</address><address type="trvalá"><city>okr. Kladno</city>\
<street>Kmetiněves</street><street_number>70</street_number>\
<zip>273 22</zip></address><address type="trvalá">\
<city>okr. Kladno</city><street>Čs. armády</street>\
<street_number>3208</street_number><zip>273 22</zip>\
</address></addresses></debtor></debtors><trustees>\
<trustee><name>Mikeš</name><first_name>Ivan</first_name>\
<honorifics_prepended>Ing.</honorifics_prepended><gen_id>61048232\
</gen_id><birth_date>1967-06-16</birth_date><addresses>\
<address type="trvalá"><city>Petrov</city><street>U ručiček</street>\
<street_number>306</street_number><country>Česká republika</country>\
<zip>252 81</zip></address><address type="sídlo firmy">\
<city>Praha 1</city><street>Novotného lávka</street>\
<street_number>5</street_number><district>Hlavní město \
Praha</district><country>CZE</country><zip>116 68</zip>\
<phone>602530769</phone></address><address type="sídlo firmy">\
<city>Praha 1</city><street>Novotného lávka</street>\
<street_number>5</street_number><district>Praha 1</district>\
<country>CZE</country><zip>116 68</zip><phone>602530769</phone>\
</address><address type="trvalá"><city>Petrov</city>\
<street>U ručiček</street><street_number>306</street_number>\
<district>Praha-západ</district><country>CZE</country>\
<zip>252 81</zip></address></addresses></trustee></trustees>\
<creditors><creditor><name>Česká správa sociálního zabezpečení</name>\
<business_name>územní pracoviště Praha 9</business_name>\
<gen_id>00006963</gen_id><addresses></addresses></creditor>\
<creditor><name>Československá obchodní banka, a. s.</name>\
<gen_id>00001350</gen_id><addresses></addresses></creditor>\
<creditor><name>ČEZ Prodej, s.r.o.</name><gen_id>27232433</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>ČSOB Pojišťovna, a. s., člen holdingu ČSOB</name>\
<gen_id>45534306</gen_id><addresses></addresses></creditor>\
<creditor><name>ESSOX s. r. o.</name><gen_id>26764652</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>Finanční úřad v Kladně</name><gen_id>72080043</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>Hypoteční banka, a. s.</name><gen_id>13584324</gen_id>\
<tax_id>004-13584324</tax_id><addresses></addresses></creditor>\
<creditor><name>JUSTRINON MANAGEMENT s. r. o.</name>\
<gen_id>29216842</gen_id><addresses></addresses></creditor>\
<creditor><name>Koncz</name><first_name>David</first_name>\
<honorifics_prepended>Mgr.</honorifics_prepended>\
<gen_id>66253080</gen_id><addresses></addresses></creditor>\
<creditor><name>Mareš</name><first_name>Ondřej</first_name>\
<honorifics_prepended>JUDr.</honorifics_prepended>\
<honorifics_appended>, LL.M.</honorifics_appended>\
<gen_id>66253799</gen_id><addresses></addresses></creditor>\
<creditor><name>Město Slaný</name><gen_id>00234877</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>OSPEN, s.r.o.</name><gen_id>25262823</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>Poláčková Uličná</name><first_name>Blanka</first_name>\
<honorifics_prepended>Ing.</honorifics_prepended>\
<birth_date>1968-01-18</birth_date><addresses></addresses>\
</creditor><creditor><name>RWE Energie, a. s.</name>\
<gen_id>49903209</gen_id><addresses></addresses></creditor>\
<creditor><name>Středočeské vodárny, a. s.</name>\
<gen_id>26196620</gen_id><addresses></addresses></creditor>\
<creditor><name>T-Mobile Czech Republic a. s.</name>\
<gen_id>64949681</gen_id><addresses></addresses></creditor>\
<creditor><name>Telefónica Czech Republic, a.s.</name>\
<gen_id>60193336</gen_id><addresses></addresses></creditor>\
<creditor><name>Zdravotní pojišťovna METAL - ALIANCE</name>\
<gen_id>48703893</gen_id><addresses></addresses></creditor>\
</creditors></insolvency><insolvency><court id="KSVYCHKP1">\
Krajský soud v Hradci Králové, pobočka v Pardubicích</court>\
<ref><court>KSPA</court><senate>56</senate>\
<register>INS</register><number>47</number><year>2015</year>\
</ref><state>Povoleno oddlužení</state><debtors><debtor>\
<name>Bártová</name><first_name>Veronika</first_name>\
<birth_date>1980-10-14</birth_date>\
<birth_id>806014/3487</birth_id><addresses>\
<address type="trvalá"><city>Litomyšl</city>\
<street>Šmilovského</street><street_number>197</street_number>\
<district>Svitavy</district><zip>570 01</zip>\
<fax>+420-123456789</fax><email>tomas@pecina.cz</email></address>\
</addresses></debtor></debtors><trustees><trustee>\
<name>Vodrážková</name><first_name>Jana</first_name>\
<honorifics_prepended>Ing.</honorifics_prepended>\
<gen_id>74267604</gen_id><birth_date>1977-12-05</birth_date>\
<addresses><address type="trvalá"><city>Chrudim</city>\
<street>Sladkovského</street><street_number>756</street_number>\
<district>Chrudim</district><country>CZE</country><zip>537 01</zip>\
</address><address type="sídlo firmy"><city>Chrudim</city>\
<street>Novoměstská</street><street_number>960</street_number>\
<district>Chrudim</district><country>CZE</country><zip>537 01</zip>\
</address></addresses></trustee></trustees><creditors><creditor>\
<name>AB 4 B.V.</name><addresses></addresses></creditor><creditor>\
<name>BNP Paribas Personal Finance SA, odštěpný závod</name>\
<gen_id>03814742</gen_id><addresses></addresses></creditor>\
<creditor><name>Česká spořitelna, a.s.</name>\
<gen_id>45244782</gen_id><addresses></addresses></creditor>\
<creditor><name>ESSOX s.r.o.</name><gen_id>26764652</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>JET Money s.r.o.</name><gen_id>25858246</gen_id>\
<addresses></addresses></creditor><creditor>\
<name>Komerční banka, a.s.</name><gen_id>45317054</gen_id>\
<addresses></addresses></creditor><creditor><name>Makovský</name>\
<first_name>Jan</first_name><birth_date>1992-11-22</birth_date>\
<birth_id>921122/3780</birth_id><addresses></addresses>\
</creditor><creditor><name>Provident Financial s. r. o.</name>\
<gen_id>25621351</gen_id><addresses></addresses></creditor>\
</creditors></insolvency><insolvency><court id="KSJICCB">\
Krajský soud v Českých Budějovicích</court><ref>\
<court>KSCB</court><senate>27</senate><register>INS</register>\
<number>19124</number><year>2016</year></ref>\
<state>Před rozhodnutím o úpadku</state><debtors><debtor>\
<name>Sviták</name><first_name>Milan</first_name>\
<gen_id>88176681</gen_id><birth_date>1970-08-13</birth_date>\
<birth_id>700813/2659</birth_id><addresses>\
<address type="sídlo firmy"><city>Bechyně</city>\
<street>Hodonice</street><street_number>65</street_number>\
<zip>391 65</zip></address></addresses></debtor></debtors>\
<trustees></trustees><creditors><creditor>\
<name>Českomoravská stavební spořitelna, a.s.</name>\
<gen_id>49241397</gen_id><addresses></addresses></creditor>\
</creditors></insolvency></insolvencies>
'''

        res = self.client.get('/pir/xmllist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/pir/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/pir/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/xml; charset=utf-8')

        res = self.client.get('/pir/xmllist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?year=2007')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?date_first_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?date_first_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?date_last_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?date_last_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?first_name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?city_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?first_name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?city=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?date_birth=1970-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?year_birth_from=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/?year_birth_to=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x0.encode('utf-8')))

        res = self.client.get(
            '/pir/xmllist/?name=Bártová&name_opt=iexact&role_debtor=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x1.encode('utf-8')))

        res = self.client.get('/pir/xmllist/?creditors=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertXMLEqual(stripxml(res.content), stripxml(x2.encode('utf-8')))

        views.EXLIM = 0
        res = self.client.get('/pir/xmllist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000

    def test_csvlist(self):

        c0 = 'Soud,Spisová značka,Stav řízení\n'

        c1 = c0 + '''\
Krajský soud v Praze,KSPH 36 INS 16046/2011,(není známo)
"Krajský soud v Hradci Králové, pobočka v Pardubicích",KSPA 56 \
INS 47/2015,Povoleno oddlužení
Krajský soud v Českých Budějovicích,KSCB 27 INS 19124/2016,Před \
rozhodnutím o úpadku
'''

        res = self.client.get('/pir/csvlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/pir/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/pir/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/csv; charset=utf-8')

        res = self.client.get('/pir/csvlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?year=2007')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?date_first_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?date_first_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?date_last_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?date_last_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?first_name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?city_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?first_name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?city=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?date_birth=1970-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?year_birth_from=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?year_birth_to=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/csvlist/?number=9')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), c0)

        res = self.client.get('/pir/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertEqual(res.content.decode('utf-8').replace('\r\n', '\n'), c1)

        views.EXLIM = 0
        res = self.client.get('/pir/csvlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000

    def test_jsonlist(self):

        j0 = '[]'

        j1 = '''\
[{"court": "Krajsk\u00fd soud v Praze", "debtors": [{"addresses": \
[{"street_number": "3208", "street": "\u010cs. arm\u00e1dy", \
"city": "Kladno", "type": "trval\u00e1", "zip": "272 01"}, \
{"street_number": "70", "street": "Kmetin\u011bves", "city": \
"okr. Kladno", "type": "trval\u00e1", "zip": "273 22"}, \
{"street_number": "3208", "street": "\u010cs. arm\u00e1dy", \
"city": "okr. Kladno", "type": "trval\u00e1", "zip": "273 22"}], \
"first_name": "And\u011bla", "gen_id": "74550381", "birth_id": \
"755819/0112", "birth_date": "1975-08-19", "name": \
"Hanzl\u00edkov\u00e1"}], "ref": {"court": "KSPH", "register": \
"INS", "number": 16046, "year": 2011, "senate": 36}, "trustees": \
[{"addresses": [{"street": "U ru\u010di\u010dek", "type": \
"trval\u00e1", "street_number": "306", "city": "Petrov", \
"country": "\u010cesk\u00e1 republika", "zip": "252 81"}, \
{"street": "Novotn\u00e9ho l\u00e1vka", "type": \
"s\u00eddlo firmy", "street_number": "5", "city": "Praha 1", \
"zip": "116 68", "phone": "602530769", "district": \
"Hlavn\u00ed m\u011bsto Praha", "country": "CZE"}, {"street": \
"Novotn\u00e9ho l\u00e1vka", "type": "s\u00eddlo firmy", \
"street_number": "5", "city": "Praha 1", "zip": "116 68", \
"phone": "602530769", "district": "Praha 1", "country": \
"CZE"}, {"street": "U ru\u010di\u010dek", "type": "trval\u00e1", \
"street_number": "306", "city": "Petrov", "zip": "252 81", \
"district": "Praha-z\u00e1pad", "country": "CZE"}], \
"first_name": "Ivan", "gen_id": "61048232", \
"honorifics_prepended": "Ing.", "birth_date": "1967-06-16", \
"name": "Mike\u0161"}], "state": ""}, {"court": "Krajsk\u00fd \
soud v Hradci Kr\u00e1lov\u00e9, pobo\u010dka v \
Pardubic\u00edch", "debtors": [{"first_name": "Veronika", \
"birth_id": "806014/3487", "addresses": [{"street": \
"\u0160milovsk\u00e9ho", "type": "trval\u00e1", "fax": \
"+420-123456789", "street_number": "197", "email": \
"tomas@pecina.cz", "city": "Litomy\u0161l", "district": \
"Svitavy", "zip": "570 01"}], "birth_date": "1980-10-14", \
"name": "B\u00e1rtov\u00e1"}], "ref": {"court": "KSPA", \
"register": "INS", "number": 47, "year": 2015, "senate": \
56}, "trustees": [{"addresses": [{"street": \
"Sladkovsk\u00e9ho", "type": "trval\u00e1", "street_number": \
"756", "city": "Chrudim", "zip": "537 01", "district": \
"Chrudim", "country": "CZE"}, {"street": "Novom\u011bstsk\u00e1", \
"type": "s\u00eddlo firmy", "street_number": "960", "city": \
"Chrudim", "zip": "537 01", "district": "Chrudim", "country": \
"CZE"}], "first_name": "Jana", "gen_id": "74267604", \
"honorifics_prepended": "Ing.", "birth_date": "1977-12-05", \
"name": "Vodr\u00e1\u017ekov\u00e1"}], "state": "Povoleno \
oddlu\u017een\u00ed"}, {"court": "Krajsk\u00fd soud v \
\u010cesk\u00fdch Bud\u011bjovic\u00edch", "debtors": \
[{"addresses": [{"street_number": "65", "street": "Hodonice", \
"city": "Bechyn\u011b", "type": "s\u00eddlo firmy", "zip": \
"391 65"}], "first_name": "Milan", "gen_id": "88176681", \
"birth_id": "700813/2659", "birth_date": "1970-08-13", \
"name": "Svit\u00e1k"}], "ref": {"court": "KSCB", "register": \
"INS", "number": 19124, "year": 2016, "senate": 27}, \
"trustees": [], "state": "P\u0159ed rozhodnut\u00edm o \
\u00fapadku"}]\
'''

        j2 = '''\
[{"creditors": [{"name": "\u010cesk\u00e1 spr\u00e1va \
soci\u00e1ln\u00edho zabezpe\u010den\u00ed", "addresses": \
[], "gen_id": "00006963", "business_name": \
"\u00fazemn\u00ed pracovi\u0161t\u011b Praha 9"}, \
{"name": "\u010ceskoslovensk\u00e1 obchodn\u00ed banka, \
a. s.", "addresses": [], "gen_id": "00001350"}, \
{"name": "\u010cEZ Prodej, s.r.o.", "addresses": [], \
"gen_id": "27232433"}, {"name": "\u010cSOB \
Poji\u0161\u0165ovna, a. s., \u010dlen holdingu \
\u010cSOB", "addresses": [], "gen_id": "45534306"}, \
{"name": "ESSOX s. r. o.", "addresses": [], "gen_id": \
"26764652"}, {"name": "Finan\u010dn\u00ed \u00fa\u0159ad \
v Kladn\u011b", "addresses": [], "gen_id": "72080043"}, \
{"name": "Hypote\u010dn\u00ed banka, a. s.", "addresses": \
[], "gen_id": "13584324", "tax_id": "004-13584324"}, \
{"name": "JUSTRINON MANAGEMENT s. r. o.", "addresses": [], \
"gen_id": "29216842"}, {"name": "Koncz", "first_name": \
"David", "gen_id": "66253080", "addresses": [], \
"honorifics_prepended": "Mgr."}, {"addresses": [], \
"first_name": "Ond\u0159ej", "honorifics_appended": \
", LL.M.", "name": "Mare\u0161", "gen_id": "66253799", \
"honorifics_prepended": "JUDr."}, {"name": \
"M\u011bsto Slan\u00fd", "addresses": [], "gen_id": \
"00234877"}, {"name": "OSPEN, s.r.o.", "addresses": [], \
"gen_id": "25262823"}, {"name": "Pol\u00e1\u010dkov\u00e1 \
Uli\u010dn\u00e1", "first_name": "Blanka", "addresses": [], \
"birth_date": "1968-01-18", "honorifics_prepended": \
"Ing."}, {"name": "RWE Energie, a. s.", "addresses": [], \
"gen_id": "49903209"}, {"name": "St\u0159edo\u010desk\u00e9 \
vod\u00e1rny, a. s.", "addresses": [], "gen_id": \
"26196620"}, {"name": "T-Mobile Czech Republic a. s.", \
"addresses": [], "gen_id": "64949681"}, {"name": \
"Telef\u00f3nica Czech Republic, a.s.", "addresses": [], \
"gen_id": "60193336"}, {"name": "Zdravotn\u00ed \
poji\u0161\u0165ovna METAL - ALIANCE", "addresses": [], \
"gen_id": "48703893"}], "ref": {"senate": 36, "year": 2011, \
"court": "KSPH", "number": 16046, "register": "INS"}, \
"state": "", "debtors": [{"addresses": [{"city": \
"Kladno", "zip": "272 01", "street": "\u010cs. \
arm\u00e1dy", "type": "trval\u00e1", "street_number": \
"3208"}, {"city": "okr. Kladno", "zip": "273 22", \
"street": "Kmetin\u011bves", "type": "trval\u00e1", \
"street_number": "70"}, {"city": "okr. Kladno", "zip": \
"273 22", "street": "\u010cs. arm\u00e1dy", "type": \
"trval\u00e1", "street_number": "3208"}], "first_name": \
"And\u011bla", "birth_id": "755819/0112", "name": \
"Hanzl\u00edkov\u00e1", "gen_id": "74550381", \
"birth_date": "1975-08-19"}], "court": "Krajsk\u00fd soud \
v Praze", "trustees": [{"addresses": [{"city": "Petrov", \
"street": "U ru\u010di\u010dek", "type": "trval\u00e1", \
"country": "\u010cesk\u00e1 republika", "street_number": \
"306", "zip": "252 81"}, {"phone": "602530769", "city": \
"Praha 1", "district": "Hlavn\u00ed m\u011bsto Praha", \
"street": "Novotn\u00e9ho l\u00e1vka", "type": "s\u00eddlo \
firmy", "country": "CZE", "street_number": "5", "zip": \
"116 68"}, {"phone": "602530769", "city": "Praha 1", \
"district": "Praha 1", "street": "Novotn\u00e9ho \
l\u00e1vka", "type": "s\u00eddlo firmy", "country": \
"CZE", "street_number": "5", "zip": "116 68"}, {"city": \
"Petrov", "district": "Praha-z\u00e1pad", "street": \
"U ru\u010di\u010dek", "type": "trval\u00e1", "country": \
"CZE", "street_number": "306", "zip": "252 81"}], \
"first_name": "Ivan", "name": "Mike\u0161", "gen_id": \
"61048232", "birth_date": "1967-06-16", \
"honorifics_prepended": "Ing."}]}, {"creditors": \
[{"name": "AB 4 B.V.", "addresses": []}, {"name": \
"BNP Paribas Personal Finance SA, od\u0161t\u011bpn\u00fd \
z\u00e1vod", "addresses": [], "gen_id": "03814742"}, \
{"name": "\u010cesk\u00e1 spo\u0159itelna, a.s.", \
"addresses": [], "gen_id": "45244782"}, {"name": \
"ESSOX s.r.o.", "addresses": [], "gen_id": "26764652"}, \
{"name": "JET Money s.r.o.", "addresses": [], "gen_id": \
"25858246"}, {"name": "Komer\u010dn\u00ed banka, a.s.", \
"addresses": [], "gen_id": "45317054"}, {"name": \
"Makovsk\u00fd", "first_name": "Jan", "addresses": [], \
"birth_date": "1992-11-22", "birth_id": "921122/3780"}, \
{"name": "Provident Financial s. r. o.", "addresses": \
[], "gen_id": "25621351"}], "ref": {"senate": 56, "year": \
2015, "court": "KSPA", "number": 47, "register": "INS"}, \
"state": "Povoleno oddlu\u017een\u00ed", "debtors": \
[{"name": "B\u00e1rtov\u00e1", "first_name": "Veronika", \
"addresses": [{"city": "Litomy\u0161l", "fax": \
"+420-123456789", "district": "Svitavy", "street": \
"\u0160milovsk\u00e9ho", "type": "trval\u00e1", \
"street_number": "197", "email": "tomas@pecina.cz", \
"zip": "570 01"}], "birth_date": "1980-10-14", \
"birth_id": "806014/3487"}], "court": "Krajsk\u00fd soud \
v Hradci Kr\u00e1lov\u00e9, pobo\u010dka \
v Pardubic\u00edch", "trustees": [{"addresses": [{"city": \
"Chrudim", "district": "Chrudim", "street": \
"Sladkovsk\u00e9ho", "type": "trval\u00e1", "country": \
"CZE", "street_number": "756", "zip": "537 01"}, \
{"city": "Chrudim", "district": "Chrudim", "street": \
"Novom\u011bstsk\u00e1", "type": "s\u00eddlo firmy", \
"country": "CZE", "street_number": "960", "zip": \
"537 01"}], "first_name": "Jana", "name": \
"Vodr\u00e1\u017ekov\u00e1", "gen_id": "74267604", \
"birth_date": "1977-12-05", "honorifics_prepended": \
"Ing."}]}, {"creditors": [{"name": "\u010ceskomoravsk\u00e1 \
stavebn\u00ed spo\u0159itelna, a.s.", "addresses": [], \
"gen_id": "49241397"}], "ref": {"senate": 27, "year": \
2016, "court": "KSCB", "number": 19124, "register": \
"INS"}, "state": "P\u0159ed rozhodnut\u00edm \
o \u00fapadku", "debtors": [{"addresses": [{"city": \
"Bechyn\u011b", "zip": "391 65", "street": "Hodonice", \
"type": "s\u00eddlo firmy", "street_number": "65"}], \
"first_name": "Milan", "birth_id": "700813/2659", "name": \
"Svit\u00e1k", "gen_id": "88176681", "birth_date": \
"1970-08-13"}], "court": "Krajsk\u00fd soud \
v \u010cesk\u00fdch Bud\u011bjovic\u00edch", "trustees": []}]\
'''

        res = self.client.get('/pir/jsonlist')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/pir/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/pir/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'application/json; charset=utf-8')

        res = self.client.get('/pir/jsonlist/?senate=-1')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?senate=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?number=0')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?number=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?year=2007')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?year=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?date_first_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?date_first_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?date_last_from=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?date_last_to=2015-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?first_name_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?city_opt=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?first_name=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?city=X')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?date_birth=1970-X-01')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?year_birth_from=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?year_birth_to=XXX')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.get('/pir/jsonlist/?number=9')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j0)

        res = self.client.get('/pir/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j1)

        res = self.client.get('/pir/jsonlist/?creditors=on')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertJSONEqual(res.content.decode('utf-8'), j2)

        views.EXLIM = 0
        res = self.client.get('/pir/jsonlist/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'exlim.html')
        views.EXLIM = 1000

    def test_party(self):

        party = Osoba.objects.get(nazevOsoby='Hanzlíková').id

        res = self.client.get('/pir/party/{:d}'.format(party))
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.post('/pir/party/{:d}/'.format(party))
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        res = self.client.get('/pir/party/{:d}/'.format(party))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'pir_party.html')
        con = res.context
        self.assertEqual(con['page_title'], 'Informace o osobě')
        self.assertEqual(con['subtitle'], 'Anděla Hanzlíková')
        self.assertEqual(con['birthid'], '755819/0112')
        self.assertEqual(len(con['adresy']), 3)
