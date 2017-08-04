# -*- coding: utf-8 -*-
#
# cin/tests.py
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
from django.test import SimpleTestCase


class TestViews(SimpleTestCase):

    def test_main(self):

        cases = (
            ('11.11.2010', '6.7.2016',
             ('11.11.2010 → 06.07.2016',
              '2064 dnů',
              '1423 pracovních dnů',
              '5 let 7 měsíců 25 dnů',
              '5,650648 let (ACT/ACT)',
              '5,654795 let (ACT/365)',
              '5,733333 let (ACT/360)',
              '5,670330 let (ACT/364)',
              '5,652778 let (30U/360)',
              '5,652778 let (30E/360)',
              '5,652778 let (30E/360 ISDA)',
              '5,652778 let (30E+/360)',
              '67,826882 měsíců (ACT)',
              '67,833333 měsíců (30U)',
              '67,833333 měsíců (30E)',
              '67,833333 měsíců (30E ISDA)',
              '67,833333 měsíců (30E+)',
             )),
            ('11.11.2010', '06.07.2016',
             ('11.11.2010 → 06.07.2016',
              '2064 dnů',
              '1423 pracovních dnů',
              '5 let 7 měsíců 25 dnů',
              '5,650648 let (ACT/ACT)',
              '5,654795 let (ACT/365)',
              '5,733333 let (ACT/360)',
              '5,670330 let (ACT/364)',
              '5,652778 let (30U/360)',
              '5,652778 let (30E/360)',
              '5,652778 let (30E/360 ISDA)',
              '5,652778 let (30E+/360)',
              '67,826882 měsíců (ACT)',
              '67,833333 měsíců (30U)',
              '67,833333 měsíců (30E)',
              '67,833333 měsíců (30E ISDA)',
              '67,833333 měsíců (30E+)',
             )),
            ('11.11.2010', '6. 7. 2016',
             ('11.11.2010 → 06.07.2016',
              '2064 dnů',
              '1423 pracovních dnů',
              '5 let 7 měsíců 25 dnů',
              '5,650648 let (ACT/ACT)',
              '5,654795 let (ACT/365)',
              '5,733333 let (ACT/360)',
              '5,670330 let (ACT/364)',
              '5,652778 let (30U/360)',
              '5,652778 let (30E/360)',
              '5,652778 let (30E/360 ISDA)',
              '5,652778 let (30E+/360)',
              '67,826882 měsíců (ACT)',
              '67,833333 měsíců (30U)',
              '67,833333 měsíců (30E)',
              '67,833333 měsíců (30E ISDA)',
              '67,833333 měsíců (30E+)',
             )),
            ('3.8.2016', '4.8.2016',
             ('03.08.2016 → 04.08.2016',
              '1 den',
              '1 pracovní den',
              '0 let 0 měsíců 1 den',
              '0,002732 let (ACT/ACT)',
              '0,002740 let (ACT/365)',
              '0,002778 let (ACT/360)',
              '0,002747 let (ACT/364)',
              '0,002778 let (30U/360)',
              '0,002778 let (30E/360)',
              '0,002778 let (30E/360 ISDA)',
              '0,002778 let (30E+/360)',
              '0,032258 měsíců (ACT)',
              '0,033333 měsíců (30U)',
              '0,033333 měsíců (30E)',
              '0,033333 měsíců (30E ISDA)',
              '0,033333 měsíců (30E+)',
             )),
            ('15.2.2001', '29.3.2003',
             ('15.02.2001 → 29.03.2003',
              '772 dnů',
              '532 pracovních dnů',
              '2 roky 1 měsíc 14 dnů',
              '2,115068 let (ACT/ACT)',
              '2,115068 let (ACT/365)',
              '2,144444 let (ACT/360)',
              '2,120879 let (ACT/364)',
              '2,122222 let (30U/360)',
              '2,122222 let (30E/360)',
              '2,122222 let (30E/360 ISDA)',
              '2,122222 let (30E+/360)',
              '25,399770 měsíců (ACT)',
              '25,466667 měsíců (30U)',
              '25,466667 měsíců (30E)',
              '25,466667 měsíců (30E ISDA)',
              '25,466667 měsíců (30E+)',
             )),
            ('29.2.2016', '31.5.2016',
             ('29.02.2016 → 31.05.2016',
              '92 dnů',
              '64 pracovních dnů',
              '0 let 3 měsíce 2 dny',
              '0,251366 let (ACT/ACT)',
              '0,252055 let (ACT/365)',
              '0,255556 let (ACT/360)',
              '0,252747 let (ACT/364)',
              '0,255556 let (30U/360)',
              '0,252778 let (30E/360)',
              '0,250000 let (30E/360 ISDA)',
              '0,255556 let (30E+/360)',
              '3,000000 měsíců (ACT)',
              '3,066667 měsíců (30U)',
              '3,033333 měsíců (30E)',
              '3,000000 měsíců (30E ISDA)',
              '3,066667 měsíců (30E+)',
             )),
            ('', '31.5.2016', ('Chybné zadání',)),
            ('XXX', '31.5.2016', ('Chybné zadání',)),
            ('30.2.2016', '31.5.2016', ('Chybné zadání',)),
            ('29.2.2016', '', ('Chybné zadání',)),
            ('29.2.2016', 'XXX', ('Chybné zadání',)),
            ('29.2.2016', '29.2.2016', ('Počátek musí předcházet konci',)),
            ('29.2.2016', '1.4.2011', ('Počátek musí předcházet konci',)),
        )

        res = self.client.get('/cin')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/cin/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(res, 'cin_main.html')

        today = date.today()
        for button in ('beg_date', 'end_date'):
            res = self.client.post('/cin/', {'submit_set_' + button: 'Dnes'})
            self.assertEqual(res.context['form'][button].value(), today)

        for test in cases:
            res = self.client.post(
                '/cin/',
                {'beg_date': test[0],
                 'end_date': test[1]})
            self.assertEqual(res.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(res, 'cin_main.html')
            soup = BeautifulSoup(res.content, 'html.parser')
            msg = soup.find('td', 'msg').select('div')
            length = len(msg)
            self.assertEqual(length, len(test[2]))
            for idx in range(length):
                self.assertEqual(msg[idx].text, test[2][idx])
