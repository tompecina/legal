# -*- coding: utf-8 -*-
#
# tests/cache_tests.py
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

from datetime import datetime, timedelta

from django.test import SimpleTestCase, TestCase

from tests.utils import DummyRequest
from cache import models, utils


class TestModels(SimpleTestCase):

    def test_models(self):

        self.assertEqual(
            str(models.Cache(
                url='test_url',
                text='test',
                expire=datetime.now())),
            'test_url')

        self.assertEqual(
            str(models.Asset(
                sessionid='test_sessionid',
                assetid='test_assetid',
                data='test',
                expire=datetime.now())),
            'test_sessionid')


class TestUtils(TestCase):

    fixtures = ('cache_test.json',)

    def test_getcache(self):

        res = utils.getcache('test', timedelta(1))
        self.assertEqual(res, ('ok', None))

        res = utils.getcache('xxx', timedelta(1))
        self.assertEqual(res, (None, 'Chyba při komunikaci se serverem'))

    def test_asset(self):

        self.assertIsNone(utils.getasset(
            DummyRequest(None),
            None))

        self.assertIsNone(utils.getasset(
            DummyRequest('test_session'),
            'test_asset1'))

        self.assertTrue(utils.setasset(
            DummyRequest('test_session'),
            'test_asset1',
            b'test_data',
            timedelta(1)))

        self.assertEqual(
            utils.getasset(
                DummyRequest('test_session'), 'test_asset1'),
            b'test_data')

        self.assertFalse(
            utils.setasset(
                DummyRequest(None),
                'test_asset',
                b'test_data',
                timedelta(1)))

        self.assertTrue(
            utils.setasset(
                DummyRequest('test_session'),
                'test_asset2',
                b'test_data',
                timedelta(-1)))

        self.assertIsNone(
            utils.getasset(
                DummyRequest('test_session'),
                'test_asset2'))
