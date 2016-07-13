# -*- coding: utf-8 -*-
#
# cache/tests.py
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

from django.test import TestCase
from datetime import timedelta
from . import main

class DummyRequest:
    def __init__(self, session_id):
        self.COOKIES = {'sessionid': session_id}

class TestMain(TestCase):

    def test_getcache(self):
        r = main.getcache('test1',
                          timedelta(1),
                          test=True,
                          test_response='ok')
        self.assertEqual(r[0], 'ok')
        self.assertIsNone(r[1])
        r = main.getcache('test1',
                          timedelta(1),
                          test=True,
                          test_response='new')
        self.assertEqual(r[0], 'ok')
        self.assertIsNone(r[1])
        r = main.getcache('test2',
                          timedelta(-1),
                          test=True,
                          test_response='ok')
        self.assertEqual(r[0], 'ok')
        self.assertIsNone(r[1])
        r = main.getcache('test2',
                          timedelta(-1),
                          test=True,
                          test_response='new')
        self.assertEqual(r[0], 'new')
        self.assertIsNone(r[1])

    def test_asset(self):
        self.assertIsNone(main.getasset(DummyRequest(None), None))
        self.assertIsNone(main.getasset(DummyRequest('test_session'),
                                        'test_asset1'))
        self.assertTrue(main.setasset(DummyRequest('test_session'),
                                      'test_asset1',
                                      b'test_data',
                                      timedelta(1)))
        self.assertEqual(main.getasset(DummyRequest('test_session'),
                                       'test_asset1'),
                         b'test_data')
        self.assertTrue(main.setasset(DummyRequest('test_session'),
                                      'test_asset2',
                                      b'test_data',
                                      timedelta(-1)))
        self.assertIsNone(main.getasset(DummyRequest('test_session'),
                                        'test_asset2'))
