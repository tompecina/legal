# -*- coding: utf-8 -*-
#
# test/test_common.py
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

from datetime import date, datetime, timedelta
from calendar import monthrange
from os.path import join
from decimal import Decimal
from copy import copy
from http import HTTPStatus
from re import compile
from hashlib import md5

from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.http import QueryDict

from test.test_cache import DummyRequest
from szr.cron import cron_update
from szr.models import Proceedings
from sir.models import Counter
from common.settings import TEST_DATA_DIR
from common import cron, glob, fields, forms, models, utils, views


TEST_STRING = 'Příliš žluťoučký kůň úpěnlivě přepíná ďábelské kódy'


class DummyResponse:

    def __init__(self, content, status=HTTPStatus.OK):
        self.text = content
        if content:
            self.content = content.encode('utf-8')
        self.status_code = status
        self.ok = status == HTTPStatus.OK


def strip_xml(string):

    xml_regex = compile(r'^(<[^<]+<\w+)[^>]*(.*)$')

    try:
        string = string.decode('utf-8')
        match = xml_regex.match(string)
        return match.group(1) + match.group(2)
    except:
        return ''


def testreq(post, *args):

    if post:
        req, data = args
        if isinstance(data, bytes):
            data = {'bytes': data.decode()}
    else:
        url = args[0]
        if '?' in url:
            req, query = url.split('?', 1)
        else:
            req = url
            query = ''
        data = QueryDict(query).dict()
    hsh = md5(req.encode())
    for key in sorted(data):
        hsh.update(key.encode())
        hsh.update(data[key].encode())
    filename = hsh.hexdigest() + '.dat'
    try:
        with open(
                join(
                    TEST_DATA_DIR,
                    'common_{}'.format(filename)),
                'rb') as infile:
            return DummyResponse(infile.read().decode())
    except:
        return DummyResponse(None, status=HTTPStatus.NOT_FOUND)


def link_equal(link1, link2):

    link1 = link1.split('?')
    link2 = link2.split('?')
    if link1[0] != link2[0]:  # pragma: no cover
        return False
    link1 = link1[1].split('&')
    link2 = link2[1].split('&')
    return sorted(link1) == sorted(link2)


def setcounter(key, num):

    Counter.objects.update_or_create(id=key, defaults={'number': num})


def setdl(num):

    setcounter('DL', num)


def setpr(num):

    setcounter('PR', num)


def getcounter(key):

    return Counter.objects.get(id=key).number


def getdl():

    return getcounter('DL')


def getpr():

    return getcounter('PR')


class TestCron(TestCase):

    fixtures = ('common_test.json',)

    def test_szr_notice(self):

        for dummy in range(Proceedings.objects.count()):
            cron_update()
        cron.cron_notify()
        msgs = mail.outbox
        self.assertEqual(len(msgs), 1)
        msg = msgs[0]
        self.assertEqual(
            msg.from_email,
            'Server {} <{}>'.format(glob.LOCAL_SUBDOMAIN, glob.LOCAL_EMAIL))
        self.assertEqual(
            msg.to,
            ['tomas@' + glob.LOCAL_DOMAIN])
        self.assertEqual(
            msg.subject,
            'Zprava ze serveru ' + glob.LOCAL_SUBDOMAIN)
        self.assertEqual(
            msg.body,
            '''\
V těchto soudních řízeních, která sledujete, došlo ke změně:

 - Nejvyšší soud, sp. zn. 8 Tdo 819/2015
   http://infosoud.justice.cz/InfoSoud/public/search.do?\
org=NSJIMBM&krajOrg=NSJIMBM&cisloSenatu=8&druhVec=TDO&\
bcVec=819&rocnik=2015&typSoudu=ns&autoFill=true&type=spzn

 - Městský soud Praha, sp. zn. 41 T 3/2016 (Igor Ševcov)
   http://infosoud.justice.cz/InfoSoud/public/search.do?\
org=MSPHAAB&krajOrg=MSPHAAB&cisloSenatu=41&druhVec=T\
&bcVec=3&rocnik=2016&typSoudu=os&autoFill=true&type=spzn

 - Nejvyšší správní soud, sp. zn. 11 Kss 6/2015 \
(Miloš Zbránek)
   http://www.nssoud.cz/mainc.aspx?cls=InfoSoud&\
kau_id=173442

 - Městský soud Praha, sp. zn. 10 T 8/2014 (Opencard)
   http://infosoud.justice.cz/InfoSoud/public/search.do?\
org=MSPHAAB&krajOrg=MSPHAAB&cisloSenatu=10&druhVec=T\
&bcVec=8&rocnik=2014&typSoudu=os&autoFill=true&type=spzn

 - Obvodní soud Praha 2, sp. zn. 6 T 136/2013 (RWU)
   http://infosoud.justice.cz/InfoSoud/public/search.do?\
org=OSPHA02&krajOrg=MSPHAAB&cisloSenatu=6&druhVec=T\
&bcVec=136&rocnik=2013&typSoudu=os&autoFill=true&type=spzn

Server {} ({})
'''.format(glob.LOCAL_SUBDOMAIN, glob.LOCAL_URL))

    def test_run(self):

        cron.test_result = 0
        cron.run('test_func', '')
        self.assertEqual(cron.test_result, 6)

        cron.run('test_func', '1')
        self.assertEqual(cron.test_result, 2)

        cron.run('test_func', '5 2')
        self.assertEqual(cron.test_result, 3)

    def test_cron_run(self):

        cron.cron_clean()

        cron.SCHED = (
            {'name': 'test_func',
             'when': lambda t: True,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertFalse(cron.test_lock)
        self.assertFalse(cron.test_pending)

        cron.SCHED = (
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': False,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertEqual(len(cron.test_lock), 1)
        self.assertFalse(cron.test_pending)
        self.assertEqual(cron.test_lock[0].name, 'test')

        cron.SCHED = (
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 6)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())
        self.assertEqual(len(cron.test_lock), 1)
        self.assertFalse(cron.test_pending)
        self.assertEqual(cron.test_lock[0].name, 'test')
        models.Lock(name='test').save()

        cron.SCHED = (
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': False,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())

        cron.SCHED = (
            {'name': 'test_func',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertEqual(models.Pending.objects.count(), 1)

        cron.SCHED = (
            {'name': 'test_func',
             'args': '1',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertEqual(models.Pending.objects.count(), 2)
        pend = models.Pending.objects.latest('timestamp_add')
        self.assertEqual(pend.name, 'test_func')
        self.assertEqual(pend.args, '1')
        self.assertEqual(pend.lock, 'test')

        cron.cron_unlock()
        cron.SCHED = ()
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 2)
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())

        models.Lock(name='another').save()
        cron.SCHED = (
            {'name': 'test_func',
             'args': '4',
             'when': lambda t: True,
             'lock': 'test',
             'blocking': True,
            },
        )
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 8)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())

        models.Lock(name='test').save()
        models.Lock.objects.filter(name='test').update(
            timestamp_add=(datetime.now() - cron.EXPIRE - timedelta(1)))
        self.assertEqual(models.Lock.objects.count(), 2)

        cron.SCHED = ()
        cron.test_result = 0
        cron.cron_run()
        self.assertEqual(cron.test_result, 0)
        self.assertEqual(models.Lock.objects.count(), 1)
        self.assertFalse(models.Pending.objects.exists())

    def test_cron_unlock(self):

        models.Lock(name='test').save()
        self.assertTrue(models.Lock.objects.exists())

        cron.cron_unlock()
        self.assertFalse(models.Lock.objects.exists())

    def test_cron_clean(self):

        models.Lock(name='test').save()
        models.Pending(name='test', args='', lock='test').save()
        self.assertTrue(models.Lock.objects.exists())
        self.assertTrue(models.Pending.objects.exists())

        cron.cron_clean()
        self.assertFalse(models.Lock.objects.exists())
        self.assertFalse(models.Pending.objects.exists())


class TestFields(SimpleTestCase):

    def test_proc_num(self):

        self.assertEqual(fields.proc_num('−11.216 530,5'), '-11216530.5')

    def test_date_field(self):

        fld = fields.DateField()
        self.assertIsNone(fld.to_python(()))
        self.assertEqual(
            fld.to_python(datetime(2012, 4, 3, 15, 32)),
            date(2012, 4, 3))
        self.assertEqual(fld.to_python(date(2012, 4, 3)), date(2012, 4, 3))
        self.assertEqual(fld.to_python('3.4.2012'), date(2012, 4, 3))
        self.assertEqual(fld.to_python('03.04.2012'), date(2012, 4, 3))
        self.assertEqual(fld.to_python('3. 4. 2012'), date(2012, 4, 3))
        self.assertEqual(fld.to_python('03. 04. 2012'), date(2012, 4, 3))

    def test_amount_field(self):

        fld = fields.AmountField()
        self.assertIsNone(fld.prepare_value(()))

        fld.rounding = 0
        self.assertEqual(fld.prepare_value(115), '115')
        self.assertEqual(fld.prepare_value(115.6), '116')
        self.assertEqual(fld.prepare_value('115'), '115')
        self.assertIsNone(fld.to_python(()))
        self.assertEqual(fld.to_python('−11.216 530,7'), -11216531)
        with self.assertRaises(forms.ValidationError):
            fld.to_python('x')

        fld.rounding = 2
        self.assertEqual(fld.prepare_value(115), '115,00')
        self.assertEqual(fld.prepare_value(115.6), '115,60')
        self.assertAlmostEqual(fld.to_python('−11.216 530,7'), -11216530.7)

    def test_decimal_field(self):

        fld = fields.DecimalField()
        self.assertIsNone(fld.to_python(()))
        self.assertAlmostEqual(
            fld.to_python('−11.216 530,7'),
            Decimal(-11216530.7))
        self.assertIsInstance(fld.to_python('−11.216 530,7'), Decimal)
        self.assertAlmostEqual(fld.to_python(-11216530.7), Decimal(-11216530.7))
        self.assertIsInstance(fld.to_python(-11216530.7), Decimal)
        with self.assertRaises(forms.ValidationError):
            fld.to_python('x')

    def test_float_field(self):

        fld = fields.FloatField()
        self.assertIsNone(fld.to_python(()))
        self.assertAlmostEqual(fld.to_python('−11.216 530,7'), -11216530.7)
        self.assertAlmostEqual(fld.to_python(-11216530.7), -11216530.7)
        with self.assertRaises(forms.ValidationError):
            fld.to_python('x')

    def test_integer_field(self):

        fld = fields.IntegerField()
        self.assertIsNone(fld.to_python(()))
        self.assertEqual(fld.to_python('−11.216 530,7'), -11216530)
        self.assertEqual(fld.to_python(-11216530.7), -11216530)
        with self.assertRaises(forms.ValidationError):
            fld.to_python('x')

    def test_currency_field(self):

        fld = fields.CurrencyField()
        self.assertIsNone(fld.compress(()))
        self.assertEqual(fld.compress(('EUR', 'xxx')), 'EUR')
        self.assertEqual(fld.compress(('OTH', 'xxx')), 'XXX')
        with self.assertRaises(forms.ValidationError):
            fld.validate(())


class TestForms(TestCase):

    def test_user_add_form(self):

        User.objects.create_user(
            'existing',
            'existing@' + glob.LOCAL_DOMAIN, 'none')
        src = {
            'first_name': 'New',
            'last_name': 'User',
            'username': 'new',
            'password1': 'nopassword',
            'password2': 'nopassword',
            'captcha': 'Praha',
        }
        self.assertTrue(forms.UserAddForm(src).is_valid())

        dst = copy(src)
        del dst['password1']
        del dst['password2']
        self.assertFalse(forms.UserAddForm(dst).is_valid())

        dst = copy(src)
        dst['password2'] = 'different'
        self.assertFalse(forms.UserAddForm(dst).is_valid())

        dst = copy(src)
        dst['captcha'] = 'praha'
        self.assertTrue(forms.UserAddForm(dst).is_valid())

        dst = copy(src)
        dst['captcha'] = 'Brno'
        self.assertFalse(forms.UserAddForm(dst).is_valid())

        dst = copy(src)
        dst['username'] = 'existing'
        self.assertFalse(forms.UserAddForm(dst).is_valid())


class TestGlob(SimpleTestCase):

    def test_register_regex(self):

        register_re = compile(glob.REGISTER_REGEX)

        for reg in glob.REGISTERS:
            self.assertIsNotNone(register_re.match(reg), msg=reg)

        for reg in ('X', ''):
            self.assertIsNone(register_re.match(reg), msg=reg)


class TestModels(TestCase):

    def test_models(self):

        User.objects.create_user('user', 'user@' + glob.LOCAL_DOMAIN, 'none')
        uid = User.objects.all()[0].id

        pwd = models.PwResetLink(
            user_id=uid,
            link=('0' * 32))
        self.assertEqual(str(pwd), ('0' * 32))

        pwd = models.Preset(
            name='Test',
            value=15,
            valid=date(2016, 5, 18))
        self.assertEqual(str(pwd), 'Test, 2016-05-18')


def proc_link(link):
    return int(link.split('=')[-1]) if link else -1


class TestUtils1(SimpleTestCase):

    def test_lim(self):

        self.assertEqual(utils.lim(1, 2, 3), 2)
        self.assertEqual(utils.lim(1, -2, 3), 1)
        self.assertEqual(utils.lim(1, 4, 3), 3)

    def test_between(self):

        self.assertTrue(utils.between(1, 2, 3))
        self.assertTrue(utils.between(1, 1, 3))
        self.assertTrue(utils.between(1, 3, 3))
        self.assertFalse(utils.between(1, -2, 3))
        self.assertFalse(utils.between(1, 4, 3))

    def test_more(self):

        self.assertFalse(utils.more())
        self.assertFalse(utils.more(False))
        self.assertFalse(utils.more(True))
        self.assertFalse(utils.more(False, False))
        self.assertFalse(utils.more(False, True))
        self.assertFalse(utils.more(True, False))
        self.assertTrue(utils.more(True, True))
        self.assertFalse(utils.more(False, False, False))
        self.assertFalse(utils.more(True, False, False))
        self.assertFalse(utils.more(False, True, False))
        self.assertTrue(utils.more(True, True, False))
        self.assertFalse(utils.more(False, False, True))
        self.assertTrue(utils.more(True, False, True))
        self.assertTrue(utils.more(False, True, True))
        self.assertTrue(utils.more(True, True, True))


    def test_easter_sunday(self):

        easter_sundays = (
            date(1700, 4, 11), date(1701, 3, 27), date(1702, 4, 16),
            date(1703, 4, 8), date(1704, 3, 23), date(1705, 4, 12),
            date(1706, 4, 4), date(1707, 4, 24), date(1708, 4, 8),
            date(1709, 3, 31), date(1710, 4, 20), date(1711, 4, 5),
            date(1712, 3, 27), date(1713, 4, 16), date(1714, 4, 1),
            date(1715, 4, 21), date(1716, 4, 12), date(1717, 3, 28),
            date(1718, 4, 17), date(1719, 4, 9), date(1720, 3, 31),
            date(1721, 4, 13), date(1722, 4, 5), date(1723, 3, 28),
            date(1724, 4, 16), date(1725, 4, 1), date(1726, 4, 21),
            date(1727, 4, 13), date(1728, 3, 28), date(1729, 4, 17),
            date(1730, 4, 9), date(1731, 3, 25), date(1732, 4, 13),
            date(1733, 4, 5), date(1734, 4, 25), date(1735, 4, 10),
            date(1736, 4, 1), date(1737, 4, 21), date(1738, 4, 6),
            date(1739, 3, 29), date(1740, 4, 17), date(1741, 4, 2),
            date(1742, 3, 25), date(1743, 4, 14), date(1744, 4, 5),
            date(1745, 4, 18), date(1746, 4, 10), date(1747, 4, 2),
            date(1748, 4, 14), date(1749, 4, 6), date(1750, 3, 29),
            date(1751, 4, 11), date(1752, 4, 2), date(1753, 4, 22),
            date(1754, 4, 14), date(1755, 3, 30), date(1756, 4, 18),
            date(1757, 4, 10), date(1758, 3, 26), date(1759, 4, 15),
            date(1760, 4, 6), date(1761, 3, 22), date(1762, 4, 11),
            date(1763, 4, 3), date(1764, 4, 22), date(1765, 4, 7),
            date(1766, 3, 30), date(1767, 4, 19), date(1768, 4, 3),
            date(1769, 3, 26), date(1770, 4, 15), date(1771, 3, 31),
            date(1772, 4, 19), date(1773, 4, 11), date(1774, 4, 3),
            date(1775, 4, 16), date(1776, 4, 7), date(1777, 3, 30),
            date(1778, 4, 19), date(1779, 4, 4), date(1780, 3, 26),
            date(1781, 4, 15), date(1782, 3, 31), date(1783, 4, 20),
            date(1784, 4, 11), date(1785, 3, 27), date(1786, 4, 16),
            date(1787, 4, 8), date(1788, 3, 23), date(1789, 4, 12),
            date(1790, 4, 4), date(1791, 4, 24), date(1792, 4, 8),
            date(1793, 3, 31), date(1794, 4, 20), date(1795, 4, 5),
            date(1796, 3, 27), date(1797, 4, 16), date(1798, 4, 8),
            date(1799, 3, 24), date(1800, 4, 13), date(1801, 4, 5),
            date(1802, 4, 18), date(1803, 4, 10), date(1804, 4, 1),
            date(1805, 4, 14), date(1806, 4, 6), date(1807, 3, 29),
            date(1808, 4, 17), date(1809, 4, 2), date(1810, 4, 22),
            date(1811, 4, 14), date(1812, 3, 29), date(1813, 4, 18),
            date(1814, 4, 10), date(1815, 3, 26), date(1816, 4, 14),
            date(1817, 4, 6), date(1818, 3, 22), date(1819, 4, 11),
            date(1820, 4, 2), date(1821, 4, 22), date(1822, 4, 7),
            date(1823, 3, 30), date(1824, 4, 18), date(1825, 4, 3),
            date(1826, 3, 26), date(1827, 4, 15), date(1828, 4, 6),
            date(1829, 4, 19), date(1830, 4, 11), date(1831, 4, 3),
            date(1832, 4, 22), date(1833, 4, 7), date(1834, 3, 30),
            date(1835, 4, 19), date(1836, 4, 3), date(1837, 3, 26),
            date(1838, 4, 15), date(1839, 3, 31), date(1840, 4, 19),
            date(1841, 4, 11), date(1842, 3, 27), date(1843, 4, 16),
            date(1844, 4, 7), date(1845, 3, 23), date(1846, 4, 12),
            date(1847, 4, 4), date(1848, 4, 23), date(1849, 4, 8),
            date(1850, 3, 31), date(1851, 4, 20), date(1852, 4, 11),
            date(1853, 3, 27), date(1854, 4, 16), date(1855, 4, 8),
            date(1856, 3, 23), date(1857, 4, 12), date(1858, 4, 4),
            date(1859, 4, 24), date(1860, 4, 8), date(1861, 3, 31),
            date(1862, 4, 20), date(1863, 4, 5), date(1864, 3, 27),
            date(1865, 4, 16), date(1866, 4, 1), date(1867, 4, 21),
            date(1868, 4, 12), date(1869, 3, 28), date(1870, 4, 17),
            date(1871, 4, 9), date(1872, 3, 31), date(1873, 4, 13),
            date(1874, 4, 5), date(1875, 3, 28), date(1876, 4, 16),
            date(1877, 4, 1), date(1878, 4, 21), date(1879, 4, 13),
            date(1880, 3, 28), date(1881, 4, 17), date(1882, 4, 9),
            date(1883, 3, 25), date(1884, 4, 13), date(1885, 4, 5),
            date(1886, 4, 25), date(1887, 4, 10), date(1888, 4, 1),
            date(1889, 4, 21), date(1890, 4, 6), date(1891, 3, 29),
            date(1892, 4, 17), date(1893, 4, 2), date(1894, 3, 25),
            date(1895, 4, 14), date(1896, 4, 5), date(1897, 4, 18),
            date(1898, 4, 10), date(1899, 4, 2), date(1900, 4, 15),
            date(1901, 4, 7), date(1902, 3, 30), date(1903, 4, 12),
            date(1904, 4, 3), date(1905, 4, 23), date(1906, 4, 15),
            date(1907, 3, 31), date(1908, 4, 19), date(1909, 4, 11),
            date(1910, 3, 27), date(1911, 4, 16), date(1912, 4, 7),
            date(1913, 3, 23), date(1914, 4, 12), date(1915, 4, 4),
            date(1916, 4, 23), date(1917, 4, 8), date(1918, 3, 31),
            date(1919, 4, 20), date(1920, 4, 4), date(1921, 3, 27),
            date(1922, 4, 16), date(1923, 4, 1), date(1924, 4, 20),
            date(1925, 4, 12), date(1926, 4, 4), date(1927, 4, 17),
            date(1928, 4, 8), date(1929, 3, 31), date(1930, 4, 20),
            date(1931, 4, 5), date(1932, 3, 27), date(1933, 4, 16),
            date(1934, 4, 1), date(1935, 4, 21), date(1936, 4, 12),
            date(1937, 3, 28), date(1938, 4, 17), date(1939, 4, 9),
            date(1940, 3, 24), date(1941, 4, 13), date(1942, 4, 5),
            date(1943, 4, 25), date(1944, 4, 9), date(1945, 4, 1),
            date(1946, 4, 21), date(1947, 4, 6), date(1948, 3, 28),
            date(1949, 4, 17), date(1950, 4, 9), date(1951, 3, 25),
            date(1952, 4, 13), date(1953, 4, 5), date(1954, 4, 18),
            date(1955, 4, 10), date(1956, 4, 1), date(1957, 4, 21),
            date(1958, 4, 6), date(1959, 3, 29), date(1960, 4, 17),
            date(1961, 4, 2), date(1962, 4, 22), date(1963, 4, 14),
            date(1964, 3, 29), date(1965, 4, 18), date(1966, 4, 10),
            date(1967, 3, 26), date(1968, 4, 14), date(1969, 4, 6),
            date(1970, 3, 29), date(1971, 4, 11), date(1972, 4, 2),
            date(1973, 4, 22), date(1974, 4, 14), date(1975, 3, 30),
            date(1976, 4, 18), date(1977, 4, 10), date(1978, 3, 26),
            date(1979, 4, 15), date(1980, 4, 6), date(1981, 4, 19),
            date(1982, 4, 11), date(1983, 4, 3), date(1984, 4, 22),
            date(1985, 4, 7), date(1986, 3, 30), date(1987, 4, 19),
            date(1988, 4, 3), date(1989, 3, 26), date(1990, 4, 15),
            date(1991, 3, 31), date(1992, 4, 19), date(1993, 4, 11),
            date(1994, 4, 3), date(1995, 4, 16), date(1996, 4, 7),
            date(1997, 3, 30), date(1998, 4, 12), date(1999, 4, 4),
            date(2000, 4, 23), date(2001, 4, 15), date(2002, 3, 31),
            date(2003, 4, 20), date(2004, 4, 11), date(2005, 3, 27),
            date(2006, 4, 16), date(2007, 4, 8), date(2008, 3, 23),
            date(2009, 4, 12), date(2010, 4, 4), date(2011, 4, 24),
            date(2012, 4, 8), date(2013, 3, 31), date(2014, 4, 20),
            date(2015, 4, 5), date(2016, 3, 27), date(2017, 4, 16),
            date(2018, 4, 1), date(2019, 4, 21), date(2020, 4, 12),
            date(2021, 4, 4), date(2022, 4, 17), date(2023, 4, 9),
            date(2024, 3, 31), date(2025, 4, 20), date(2026, 4, 5),
            date(2027, 3, 28), date(2028, 4, 16), date(2029, 4, 1),
            date(2030, 4, 21), date(2031, 4, 13), date(2032, 3, 28),
            date(2033, 4, 17), date(2034, 4, 9), date(2035, 3, 25),
            date(2036, 4, 13), date(2037, 4, 5), date(2038, 4, 25),
            date(2039, 4, 10), date(2040, 4, 1), date(2041, 4, 21),
            date(2042, 4, 6), date(2043, 3, 29), date(2044, 4, 17),
            date(2045, 4, 9), date(2046, 3, 25), date(2047, 4, 14),
            date(2048, 4, 5), date(2049, 4, 18), date(2050, 4, 10),
            date(2051, 4, 2), date(2052, 4, 21), date(2053, 4, 6),
            date(2054, 3, 29), date(2055, 4, 18), date(2056, 4, 2),
            date(2057, 4, 22), date(2058, 4, 14), date(2059, 3, 30),
            date(2060, 4, 18), date(2061, 4, 10), date(2062, 3, 26),
            date(2063, 4, 15), date(2064, 4, 6), date(2065, 3, 29),
            date(2066, 4, 11), date(2067, 4, 3), date(2068, 4, 22),
            date(2069, 4, 14), date(2070, 3, 30), date(2071, 4, 19),
            date(2072, 4, 10), date(2073, 3, 26), date(2074, 4, 15),
            date(2075, 4, 7), date(2076, 4, 19), date(2077, 4, 11),
            date(2078, 4, 3), date(2079, 4, 23), date(2080, 4, 7),
            date(2081, 3, 30), date(2082, 4, 19), date(2083, 4, 4),
            date(2084, 3, 26), date(2085, 4, 15), date(2086, 3, 31),
            date(2087, 4, 20), date(2088, 4, 11), date(2089, 4, 3),
            date(2090, 4, 16), date(2091, 4, 8), date(2092, 3, 30),
            date(2093, 4, 12), date(2094, 4, 4), date(2095, 4, 24),
            date(2096, 4, 15), date(2097, 3, 31), date(2098, 4, 20),
            date(2099, 4, 12), date(2100, 3, 28), date(2101, 4, 17),
            date(2102, 4, 9), date(2103, 3, 25), date(2104, 4, 13),
            date(2105, 4, 5), date(2106, 4, 18), date(2107, 4, 10),
            date(2108, 4, 1), date(2109, 4, 21), date(2110, 4, 6),
            date(2111, 3, 29), date(2112, 4, 17), date(2113, 4, 2),
            date(2114, 4, 22), date(2115, 4, 14), date(2116, 3, 29),
            date(2117, 4, 18), date(2118, 4, 10), date(2119, 3, 26),
            date(2120, 4, 14), date(2121, 4, 6), date(2122, 3, 29),
            date(2123, 4, 11), date(2124, 4, 2), date(2125, 4, 22),
            date(2126, 4, 14), date(2127, 3, 30), date(2128, 4, 18),
            date(2129, 4, 10), date(2130, 3, 26), date(2131, 4, 15),
            date(2132, 4, 6), date(2133, 4, 19), date(2134, 4, 11),
            date(2135, 4, 3), date(2136, 4, 22), date(2137, 4, 7),
            date(2138, 3, 30), date(2139, 4, 19), date(2140, 4, 3),
            date(2141, 3, 26), date(2142, 4, 15), date(2143, 3, 31),
            date(2144, 4, 19), date(2145, 4, 11), date(2146, 4, 3),
            date(2147, 4, 16), date(2148, 4, 7), date(2149, 3, 30),
            date(2150, 4, 12), date(2151, 4, 4), date(2152, 4, 23),
            date(2153, 4, 15), date(2154, 3, 31), date(2155, 4, 20),
            date(2156, 4, 11), date(2157, 3, 27), date(2158, 4, 16),
            date(2159, 4, 8), date(2160, 3, 23), date(2161, 4, 12),
            date(2162, 4, 4), date(2163, 4, 24), date(2164, 4, 8),
            date(2165, 3, 31), date(2166, 4, 20), date(2167, 4, 5),
            date(2168, 3, 27), date(2169, 4, 16), date(2170, 4, 1),
            date(2171, 4, 21), date(2172, 4, 12), date(2173, 4, 4),
            date(2174, 4, 17), date(2175, 4, 9), date(2176, 3, 31),
            date(2177, 4, 20), date(2178, 4, 5), date(2179, 3, 28),
            date(2180, 4, 16), date(2181, 4, 1), date(2182, 4, 21),
            date(2183, 4, 13), date(2184, 3, 28), date(2185, 4, 17),
            date(2186, 4, 9), date(2187, 3, 25), date(2188, 4, 13),
            date(2189, 4, 5), date(2190, 4, 25), date(2191, 4, 10),
            date(2192, 4, 1), date(2193, 4, 21), date(2194, 4, 6),
            date(2195, 3, 29), date(2196, 4, 17), date(2197, 4, 9),
            date(2198, 3, 25), date(2199, 4, 14), date(2200, 4, 6),
            date(2201, 4, 19), date(2202, 4, 11), date(2203, 4, 3),
            date(2204, 4, 22), date(2205, 4, 7), date(2206, 3, 30),
            date(2207, 4, 19), date(2208, 4, 3), date(2209, 3, 26),
            date(2210, 4, 15), date(2211, 3, 31), date(2212, 4, 19),
            date(2213, 4, 11), date(2214, 3, 27), date(2215, 4, 16),
            date(2216, 4, 7), date(2217, 3, 30), date(2218, 4, 12),
            date(2219, 4, 4), date(2220, 4, 23), date(2221, 4, 15),
            date(2222, 3, 31), date(2223, 4, 20), date(2224, 4, 11),
            date(2225, 3, 27), date(2226, 4, 16), date(2227, 4, 8),
            date(2228, 3, 23), date(2229, 4, 12), date(2230, 4, 4),
            date(2231, 4, 24), date(2232, 4, 8), date(2233, 3, 31),
            date(2234, 4, 20), date(2235, 4, 5), date(2236, 3, 27),
            date(2237, 4, 16), date(2238, 4, 1), date(2239, 4, 21),
            date(2240, 4, 12), date(2241, 4, 4), date(2242, 4, 17),
            date(2243, 4, 9), date(2244, 3, 31), date(2245, 4, 13),
            date(2246, 4, 5), date(2247, 3, 28), date(2248, 4, 16),
            date(2249, 4, 1), date(2250, 4, 21), date(2251, 4, 13),
            date(2252, 3, 28), date(2253, 4, 17), date(2254, 4, 9),
            date(2255, 3, 25), date(2256, 4, 13), date(2257, 4, 5),
            date(2258, 4, 25), date(2259, 4, 10), date(2260, 4, 1),
            date(2261, 4, 21), date(2262, 4, 6), date(2263, 3, 29),
            date(2264, 4, 17), date(2265, 4, 2), date(2266, 3, 25),
            date(2267, 4, 14), date(2268, 4, 5), date(2269, 4, 18),
            date(2270, 4, 10), date(2271, 4, 2), date(2272, 4, 21),
            date(2273, 4, 6), date(2274, 3, 29), date(2275, 4, 18),
            date(2276, 4, 2), date(2277, 4, 22), date(2278, 4, 14),
            date(2279, 3, 30), date(2280, 4, 18), date(2281, 4, 10),
            date(2282, 3, 26), date(2283, 4, 15), date(2284, 4, 6),
            date(2285, 3, 22), date(2286, 4, 11), date(2287, 4, 3),
            date(2288, 4, 22), date(2289, 4, 7), date(2290, 3, 30),
            date(2291, 4, 19), date(2292, 4, 10), date(2293, 3, 26),
            date(2294, 4, 15), date(2295, 4, 7), date(2296, 4, 19),
            date(2297, 4, 11), date(2298, 4, 3), date(2299, 4, 16),
        )

        for dat in easter_sundays:
            self.assertEqual(utils.easter_sunday(dat.year), dat)

    def test_movable_holiday(self):

        hol = (
            date(2016, 3, 25), date(1939, 4, 10), date(1946, 4, 22),
            date(1948, 3, 29), date(1951, 5, 3), date(1939, 5, 29),
            date(1946, 6, 10), date(1948, 5, 17), date(1951, 5, 14),
            date(1951, 5, 24),
        )

        nohol = (
            date(1945, 3, 30), date(1947, 4, 4), date(2015, 4, 3),
            date(1947, 4, 7), date(1952, 5, 22), date(1947, 5, 26),
            date(1952, 6, 2), date(1952, 6, 12),
        )

        for dat in hol:
            self.assertTrue(utils.movable_holiday(dat))
            self.assertFalse(utils.movable_holiday(dat - timedelta(days=1)))

        for dat in nohol:
            self.assertFalse(utils.movable_holiday(dat))

    def test_holiday(self):

        self.assertTrue(utils.holiday(date(2016, 1, 1)))
        self.assertFalse(utils.holiday(date(2016, 1, 5)))
        self.assertTrue(utils.holiday(date(2016, 1, 16)))
        self.assertTrue(utils.holiday(date(2016, 2, 7)))
        self.assertFalse(utils.holiday(date(2016, 2, 29)))
        self.assertFalse(utils.holiday(date(2016, 3, 8)))
        self.assertTrue(utils.holiday(date(2016, 3, 20)))
        self.assertTrue(utils.holiday(date(2016, 3, 25)))
        self.assertTrue(utils.holiday(date(2016, 3, 28)))
        self.assertFalse(utils.holiday(date(2016, 4, 18)))
        self.assertFalse(utils.holiday(date(2016, 5, 19)))
        self.assertFalse(utils.holiday(date(2016, 6, 3)))
        self.assertFalse(utils.holiday(date(1991, 5, 8)))
        self.assertTrue(utils.holiday(date(1991, 5, 9)))
        self.assertTrue(utils.holiday(date(1992, 5, 8)))
        self.assertTrue(utils.holiday(date(1992, 5, 9)))
            # not testable as 1992-05-09 was Saturday

        cal = {
            1952: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (2, 9, 16, 23, 30),
                (6, 13, 14, 20, 27),
                (1, 4, 9, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26, 28),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 25, 26, 28),
            ),
            1953: (
                (1, 4, 11, 18, 25),
                (1, 8, 15, 22),
                (1, 8, 15, 22, 29),
                (5, 6, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1954: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (7, 14, 21, 28),
                (4, 11, 18, 19, 25),
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 28, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 25, 26),
            ),
            1955: (
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (6, 13, 20, 27),
                (3, 10, 11, 17, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 28, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 26),
            ),
            1956: (
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (4, 11, 18, 25),
                (1, 2, 8, 15, 22, 29),
                (1, 6, 9, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 25, 26, 30),
            ),
            1957: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 22, 28),
                (1, 5, 9, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27, 28),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 25, 26, 29),
            ),
            1958: (
                (1, 5, 12, 19, 26),
                (2, 9, 16, 23),
                (2, 9, 16, 23, 30),
                (6, 7, 13, 20, 27),
                (1, 4, 9, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26, 28),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 25, 26, 28),
            ),
            1959: (
                (1, 4, 11, 18, 25),
                (1, 8, 15, 22),
                (1, 8, 15, 22, 29, 30),
                (5, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1960: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (6, 13, 20, 27),
                (3, 10, 17, 18, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 28, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 26),
            ),
            1961: (
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (5, 12, 19, 26),
                (2, 3, 9, 16, 23, 30),
                (1, 7, 9, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 28, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 25, 26, 31),
            ),
            1962: (
                (1, 7, 14, 21, 28),
                (4, 11, 18, 25),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 23, 29),
                (1, 6, 9, 13, 20, 27),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (2, 9, 16, 23, 25, 26, 30),
            ),
            1963: (
                (1, 6, 13, 20, 27),
                (3, 10, 17, 24),
                (3, 10, 17, 24, 31),
                (7, 14, 15, 21, 28),
                (1, 5, 9, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (7, 14, 21, 28),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 27, 28),
                (3, 10, 17, 24),
                (1, 8, 15, 22, 25, 26, 29),
            ),
            1964: (
                (1, 5, 12, 19, 26),
                (2, 9, 16, 23),
                (1, 8, 15, 22, 29, 30),
                (5, 12, 19, 26),
                (1, 3, 9, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 26),
                (2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25, 28),
                (1, 8, 15, 22, 29),
                (6, 13, 20, 25, 26, 27),
            ),
            1965: (
                (1, 3, 10, 17, 24, 31),
                (7, 14, 21, 28),
                (7, 14, 21, 28),
                (4, 11, 18, 19, 25),
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (4, 11, 18, 25),
                (1, 8, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 28, 31),
                (7, 14, 21, 28),
                (5, 12, 19, 25, 26),
            ),
            1966: (
                (1, 2, 9, 16, 23, 30),
                (6, 13, 20, 27),
                (6, 13, 20, 27),
                (3, 10, 11, 17, 24),
                (1, 8, 9, 15, 22, 29),
                (5, 12, 19, 26),
                (3, 10, 17, 24, 31),
                (6, 7, 14, 21, 28),
                (3, 4, 11, 18, 25),
                (1, 2, 9, 16, 23, 28, 29, 30),
                (6, 13, 20, 26, 27),
                (4, 11, 18, 24, 25, 26),
            ),
            1967: (
                (1, 7, 8, 15, 21, 22, 29),
                (4, 5, 12, 18, 19, 26),
                (4, 5, 12, 18, 19, 26, 27),
                (1, 2, 9, 15, 16, 23, 29, 30),
                (1, 7, 9, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (2, 8, 9, 16, 22, 23, 30),
                (5, 6, 13, 19, 20, 27),
                (2, 3, 10, 16, 17, 24, 30),
                (1, 8, 14, 15, 22, 28, 29),
                (5, 11, 12, 19, 25, 26),
                (3, 9, 10, 17, 23, 24, 25, 26, 31),
            ),
            1968: (
                (1, 7, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (3, 9, 10, 17, 23, 24, 31),
                (6, 7, 14, 15, 20, 21, 28),
                (1, 4, 5, 9, 12, 18, 19, 26),
                (1, 2, 9, 15, 16, 23, 29, 30),
                (7, 13, 14, 21, 27, 28),
                (4, 10, 11, 18, 24, 25),
                (1, 7, 8, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 23, 24, 25, 26, 30, 31),
            ),
            1969: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 26, 27, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 31),
            ),
            1970: (
                (1, 2, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29, 30),
                (5, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 9, 10, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 30, 31),
                (1, 7, 8, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26),
            ),
            1971: (
                (1, 2, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 29, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1972: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1973: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 15, 21, 22, 23, 28, 29),
                (1, 5, 6, 9, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1974: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (7, 13, 14, 15, 20, 21, 27, 28),
                (1, 4, 5, 9, 10, 11, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 24, 25, 26, 30, 31),
            ),
            1975: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 23, 29, 30, 31),
                (6, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26),
            ),
            1976: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 19, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1977: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 11, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1978: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 12, 18, 19, 25, 26, 27),
                (2, 8, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 24, 30),
                (1, 7, 8, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1979: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 7, 8, 14, 15, 16, 22, 29, 30),
                (1, 7, 8, 9, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1980: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (5, 6, 7, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 21, 27, 28),
                (4, 5, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 25, 26, 27, 28),
            ),
            1981: (
                (1, 2, 3, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 26),
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 19, 20, 25, 26, 27),
            ),
            1982: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
            ),
            1983: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 25),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1984: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 7, 8, 14, 15, 21, 22, 23, 29, 30),
                (1, 5, 6, 9, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 23, 24, 25, 26, 30, 31),
            ),
            1985: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 24, 30, 31),
                (6, 7, 8, 14, 20, 21, 27, 28),
                (1, 2, 3, 9, 10, 11, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 29),
                (5, 6, 12, 13, 20, 26, 27),
                (2, 3, 9, 10, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 22, 24, 25, 26, 30, 31),
            ),
            1986: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 16, 22, 23, 29, 30, 31),
                (6, 12, 13, 19, 20, 26, 27),
                (1, 2, 3, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 31),
            ),
            1987: (
                (1, 2, 9, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 26),
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 13, 19, 20, 24, 25, 26, 31),
            ),
            1988: (
                (1, 2, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1989: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 12, 18, 19, 25, 26, 27),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (1, 7, 8, 9, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1990: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 16, 21, 22, 29, 30),
                (1, 5, 6, 9, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            1991: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 9, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            1992: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 20, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            1993: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            1994: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 4, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            1995: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            1996: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 8, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            1997: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30, 31),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            1998: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 13, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            1999: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 5, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2000: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 17, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            2001: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 16, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2002: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            2003: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 21, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2004: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 12, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 17, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2005: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            2006: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (1, 6, 7, 8, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 5, 6, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 17, 18, 19, 25, 26),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 26, 30, 31),
            ),
            2007: (
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2008: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2009: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 13, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 17, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            2010: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 5, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (3, 4, 5, 6, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 28, 30, 31),
                (6, 7, 13, 14, 17, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 24, 25, 26),
            ),
            2011: (
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 25, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
            2012: (
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 9, 14, 15, 21, 22, 28, 29),
                (1, 5, 6, 8, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 5, 6, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25),
                (1, 2, 8, 9, 15, 16, 22, 23, 24, 25, 26, 29, 30),
            ),
            2013: (
                (1, 5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (1, 6, 7, 13, 14, 20, 21, 27, 28),
                (1, 4, 5, 8, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 24, 25, 26, 28, 29),
            ),
            2014: (
                (1, 4, 5, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 21, 26, 27),
                (1, 3, 4, 8, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 26, 27),
                (2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 11, 12, 18, 19, 25, 26, 28),
                (1, 2, 8, 9, 15, 16, 17, 22, 23, 29, 30),
                (6, 7, 13, 14, 20, 21, 24, 25, 26, 27, 28),
            ),
            2015: (
                (1, 3, 4, 10, 11, 17, 18, 24, 25, 31),
                (1, 7, 8, 14, 15, 21, 22, 28),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 3, 8, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (4, 5, 6, 11, 12, 18, 19, 25, 26),
                (1, 2, 8, 9, 15, 16, 22, 23, 29, 30),
                (5, 6, 12, 13, 19, 20, 26, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28, 31),
                (1, 7, 8, 14, 15, 17, 21, 22, 28, 29),
                (5, 6, 12, 13, 19, 20, 24, 25, 26, 27),
            ),
            2016: (
                (1, 2, 3, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (5, 6, 12, 13, 19, 20, 25, 26, 27, 28),
                (2, 3, 9, 10, 16, 17, 23, 24, 30),
                (1, 7, 8, 14, 15, 21, 22, 28, 29),
                (4, 5, 11, 12, 18, 19, 25, 26),
                (2, 3, 5, 6, 9, 10, 16, 17, 23, 24, 30, 31),
                (6, 7, 13, 14, 20, 21, 27, 28),
                (3, 4, 10, 11, 17, 18, 24, 25, 28),
                (1, 2, 8, 9, 15, 16, 22, 23, 28, 29, 30),
                (5, 6, 12, 13, 17, 19, 20, 26, 27),
                (3, 4, 10, 11, 17, 18, 24, 25, 26, 31),
            ),
        }

        for year in range(1952, 2017):
            for month in range(1, 13):
                for day in range(1, (monthrange(year, month)[1] + 1)):
                    dat = date(year, month, day)
                    self.assertEqual(
                        utils.holiday(dat),
                        (day in cal[year][month - 1]))

    def test_ply(self):

        self.assertEqual(utils.ply(date(2016, 7, 5), 1), date(2017, 7, 5))
        self.assertEqual(utils.ply(date(2016, 2, 29), 1), date(2017, 2, 28))

    def test_plm(self):

        self.assertEqual(utils.plm(date(2016, 7, 5), 1), date(2016, 8, 5))
        self.assertEqual(utils.plm(date(2015, 1, 31), 1), date(2015, 2, 28))
        self.assertEqual(utils.plm(date(2016, 1, 31), 1), date(2016, 2, 29))

    def test_yfactor(self):

        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2011, 7, 11),
                'ACT/ACT'))

        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/ACT'),
            4.9821618384609625)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/365'),
            1820/365)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/360'),
            1820/360)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/364'),
            1820/364)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30U/360'),
            1793/360)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 30),
                date(2016, 7, 31),
                '30U/360'),
            5)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E/360'),
            1793/360)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E/360 ISDA'),
            1793/360)

        self.assertAlmostEqual(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E+/360'),
            1793/360)

        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT/XXX'))

        self.assertIsNone(
            utils.yfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

    def test_mfactor(self):

        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2011, 7, 11),
                'ACT'))

        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'ACT'),
            59.774193548387096)

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30U'),
            1793/30)

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 30),
                date(2016, 7, 31),
                '30U'),
            60)

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E'),
            1793/30)

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E ISDA'),
            1793/30)

        self.assertAlmostEqual(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                '30E+'),
            1793/30)

        self.assertIsNone(
            utils.mfactor(
                date(2011, 7, 12),
                date(2016, 7, 5),
                'XXX'))

    def test_grammar(self):

        test = ('koruna', 'koruny', 'korun')
        self.assertEqual(utils.grammar(-5, test), '-5 korun')
        self.assertEqual(utils.grammar(-4, test), '-4 koruny')
        self.assertEqual(utils.grammar(-2, test), '-2 koruny')
        self.assertEqual(utils.grammar(-1, test), '-1 koruna')
        self.assertEqual(utils.grammar(0, test), '0 korun')
        self.assertEqual(utils.grammar(1, test), '1 koruna')
        self.assertEqual(utils.grammar(2, test), '2 koruny')
        self.assertEqual(utils.grammar(4, test), '4 koruny')
        self.assertEqual(utils.grammar(5, test), '5 korun')

    def test_normfl(self):

        self.assertEqual(utils.normfl(0), .0)
        self.assertEqual(utils.normfl(1), 1.0)
        self.assertEqual(utils.normfl(-1.), -1.0)
        self.assertEqual(utils.normfl(.004999), .0)
        self.assertEqual(utils.normfl(.005), .005)
        self.assertEqual(utils.normfl(-.004999), -.0)
        self.assertEqual(utils.normfl(-.005), -.005)

    def test_famt(self):

        self.assertEqual(utils.famt(0), '0')
        self.assertEqual(utils.famt(1), '1')
        self.assertEqual(utils.famt(-1), '-1')
        self.assertEqual(utils.famt(1.4), '1,40')
        self.assertEqual(utils.famt(-1.4), '-1,40')
        self.assertEqual(utils.famt(1.489), '1,49')
        self.assertEqual(utils.famt(-1.489), '-1,49')
        self.assertEqual(utils.famt(537), '537')
        self.assertEqual(utils.famt(-537), '-537')
        self.assertEqual(utils.famt(1537), '1.537')
        self.assertEqual(utils.famt(-1537), '-1.537')
        self.assertEqual(utils.famt(68562515458), '68.562.515.458')
        self.assertEqual(utils.famt(-68562515458), '-68.562.515.458')
        self.assertEqual(utils.famt(68562515458.216), '68.562.515.458,22')
        self.assertEqual(utils.famt(-68562515458.216), '-68.562.515.458,22')
        self.assertEqual(utils.famt(968562515458.216), '968.562.515.458,22')
        self.assertEqual(utils.famt(-968562515458.216), '-968.562.515.458,22')
        self.assertEqual(utils.famt(-.001), '0,00')
        self.assertEqual(utils.famt(.001), '0,00')

    def test_getxml(self):

        self.assertIsNone(utils.get_xml(b'test'))

    def test_iso2date(self):

        soup = utils.new_xml(None)
        tag = soup.new_tag('date')
        tag['year'] = 2014
        tag['month'] = 11
        tag['day'] = 14
        self.assertEqual(utils.iso2date(tag), date(2014, 11, 14))

        soup = utils.new_xml(None)
        tag = soup.new_tag('date')
        tag.string = '2014-11-14'
        self.assertEqual(utils.iso2date(tag), date(2014, 11, 14))

    def test_pager(self):

        cases = (
            (0, 1, (1, 1, -1, -1, -1, -1)),
            (0, 50, (1, 1, -1, -1, -1, -1)),
            (0, 51, (1, 2, -1, -1, 50, 50)),
            (0, 100, (1, 2, -1, -1, 50, 50)),
            (0, 101, (1, 3, -1, -1, 50, 100)),
            (0, 53697, (1, 1074, -1, -1, 50, 53650)),
            (50, 51, (2, 2, 0, 0, -1, -1)),
            (50, 100, (2, 2, 0, 0, -1, -1)),
            (50, 101, (2, 3, 0, 0, 100, 100)),
            (50, 53697, (2, 1074, 0, 0, 100, 53650)),
            (100, 53697, (3, 1074, 0, 50, 150, 53650)),
            (53600, 53697, (1073, 1074, 0, 53550, 53650, 53650)),
            (53650, 53697, (1074, 1074, 0, 53600, -1, -1)),
        )

        idx = 0
        for test in cases:
            pag = utils.Pager(
                test[0],
                test[1],
                'url',
                QueryDict(mutable=True),
                50)
            res = (
                pag.curr,
                pag.total,
                proc_link(pag.linkbb),
                proc_link(pag.linkb),
                proc_link(pag.linkf),
                proc_link(pag.linkff),
            )
            self.assertEqual(res, test[2], msg=str(idx))
            idx += 1

    def test_ref(self):

        refs = (
            '3 As 12/2015-8',
            '12 Azs 4/2009-118',
            'Konf 1/2011-221',
            '3 As 12/2015',
            '12 Azs 4/2009',
            'Konf 1/2011',
        )

        for ref in refs:
            self.assertEqual(utils.composeref(*utils.decomposeref(ref)), ref)
            self.assertEqual(utils.composeref(*utils.decomposeref(
                ref.replace('-', ' - '))), ref)

    def test_normreg(self):

        regs = ((
            'T', 'C', 'P A NC', 'D', 'E', 'P', 'NC', 'ERO', 'RO', 'EC',
            'EVC', 'EXE', 'EPR', 'PP', 'CM', 'SM', 'CA', 'CAD', 'AZ', 'TO',
            'NT', 'CO', 'NTD', 'CMO', 'KO', 'NCO', 'NCD', 'NCP', 'ECM',
            'ICM', 'INS', 'K', 'KV', 'EVCM', 'A', 'AD', 'AF', 'NA', 'UL',
            'CDO', 'ODO', 'TDO', 'TZ', 'NCU', 'ADS', 'AFS', 'ANS', 'AO',
            'AOS', 'APRK', 'APRN', 'APS', 'ARS', 'AS', 'ASZ', 'AZS', 'KOMP',
            'KONF', 'KSE', 'KSEO', 'KSS', 'KSZ', 'NA', 'NAD', 'NAO', 'NCN',
            'NK', 'NTN', 'OBN', 'PLEN', 'PLSN', 'PST', 'ROZK', 'RS', 'S',
            'SPR', 'SST', 'VOL', 'ABC', 'abc'
        ), (
            'T', 'C', 'P a Nc', 'D', 'E', 'P', 'Nc', 'ERo', 'Ro', 'EC',
            'EVC', 'EXE', 'EPR', 'PP', 'Cm', 'Sm', 'Ca', 'Cad', 'Az', 'To',
            'Nt', 'Co', 'Ntd', 'Cmo', 'Ko', 'Nco', 'Ncd', 'Ncp', 'ECm',
            'ICm', 'INS', 'K', 'Kv', 'EVCm', 'A', 'Ad', 'Af', 'Na', 'UL',
            'Cdo', 'Odo', 'Tdo', 'Tz', 'Ncu', 'Ads', 'Afs', 'Ans', 'Ao',
            'Aos', 'Aprk', 'Aprn', 'Aps', 'Ars', 'As', 'Asz', 'Azs', 'Komp',
            'Konf', 'Kse', 'Kseo', 'Kss', 'Ksz', 'Na', 'Nad', 'Nao', 'Ncn',
            'Nk', 'Ntn', 'Obn', 'Plen', 'Plsn', 'Pst', 'Rozk', 'Rs', 'S',
            'Spr', 'Sst', 'Vol', 'Abc', 'Abc'
        ))

        for reg1, reg2 in zip(regs[0], regs[1]):
            self.assertEqual(utils.normreg(reg1), reg2)

    def test_xmlbool(self):

        self.assertEqual(utils.xmlbool(False), 'false')
        self.assertEqual(utils.xmlbool(True), 'true')

    def test_icontains(self):

        self.assertTrue(utils.icontains('yz', 'xyzw'))
        self.assertFalse(utils.icontains('q', 'xyzw'))
        self.assertTrue(utils.icontains('YZ', 'xyzw'))
        self.assertTrue(utils.icontains('yz', 'XYZW'))
        self.assertTrue(utils.icontains('YZ', 'xyzw'))
        self.assertTrue(utils.icontains('čď', 'áčďě'))
        self.assertFalse(utils.icontains('é', 'áčďě'))
        self.assertTrue(utils.icontains('ČĎ', 'áčďě'))
        self.assertTrue(utils.icontains('čď', 'ÁČĎĚ'))
        self.assertTrue(utils.icontains('ČĎ', 'áčďě'))
        self.assertFalse(utils.icontains('yz', ''))
        self.assertTrue(utils.icontains('', 'xyzw'))
        self.assertTrue(utils.icontains('', ''))

    def test_istartswith(self):

        self.assertTrue(utils.istartswith('xy', 'xyzw'))
        self.assertFalse(utils.istartswith('y', 'xyzw'))
        self.assertFalse(utils.istartswith('q', 'xyzw'))
        self.assertTrue(utils.istartswith('XY', 'xyzw'))
        self.assertTrue(utils.istartswith('xy', 'XYZW'))
        self.assertTrue(utils.istartswith('XY', 'xyzw'))
        self.assertTrue(utils.istartswith('áč', 'áčďě'))
        self.assertFalse(utils.istartswith('č', 'áčďě'))
        self.assertFalse(utils.istartswith('ě', 'áčďě'))
        self.assertTrue(utils.istartswith('ÁČ', 'áčďě'))
        self.assertTrue(utils.istartswith('áč', 'ÁČĎĚ'))
        self.assertTrue(utils.istartswith('ÁČ', 'áčďě'))
        self.assertFalse(utils.istartswith('y', ''))
        self.assertTrue(utils.istartswith('', 'xyzw'))
        self.assertTrue(utils.istartswith('', ''))

    def test_iendswith(self):

        self.assertTrue(utils.iendswith('zw', 'xyzw'))
        self.assertFalse(utils.iendswith('y', 'xyzw'))
        self.assertFalse(utils.iendswith('q', 'xyzw'))
        self.assertTrue(utils.iendswith('ZW', 'xyzw'))
        self.assertTrue(utils.iendswith('zw', 'XYZW'))
        self.assertTrue(utils.iendswith('ZW', 'xyzw'))
        self.assertTrue(utils.iendswith('ďě', 'áčďě'))
        self.assertFalse(utils.iendswith('č', 'áčďě'))
        self.assertFalse(utils.iendswith('á', 'áčďě'))
        self.assertTrue(utils.iendswith('ĎĚ', 'áčďě'))
        self.assertTrue(utils.iendswith('ďě', 'ÁČĎĚ'))
        self.assertTrue(utils.iendswith('ĎĚ', 'áčďě'))
        self.assertFalse(utils.iendswith('y', ''))
        self.assertTrue(utils.iendswith('', 'xyzw'))
        self.assertTrue(utils.iendswith('', ''))

    def test_iexact(self):

        self.assertTrue(utils.iexact('xyzw', 'xyzw'))
        self.assertFalse(utils.iexact('y', 'xyzw'))
        self.assertFalse(utils.iexact('q', 'xyzw'))
        self.assertTrue(utils.iexact('XYZW', 'xyzw'))
        self.assertTrue(utils.iexact('xyzw', 'XYZW'))
        self.assertTrue(utils.iexact('XYZW', 'xyzw'))
        self.assertTrue(utils.iexact('áčďě', 'áčďě'))
        self.assertFalse(utils.iexact('č', 'áčďě'))
        self.assertFalse(utils.iexact('ě', 'áčďě'))
        self.assertTrue(utils.iexact('ÁČĎĚ', 'áčďě'))
        self.assertTrue(utils.iexact('áčďě', 'ÁČĎĚ'))
        self.assertTrue(utils.iexact('ÁČĎĚ', 'áčďě'))
        self.assertFalse(utils.iexact('y', ''))
        self.assertFalse(utils.iexact('', 'xyzw'))
        self.assertTrue(utils.iexact('', ''))

    def test_text_opt(self):

        self.assertTrue(utils.text_opt('yz', 'xyzw', 0))
        self.assertFalse(utils.text_opt('q', 'xyzw', 0))
        self.assertTrue(utils.text_opt('YZ', 'xyzw', 0))
        self.assertTrue(utils.text_opt('yz', 'XYZW', 0))
        self.assertTrue(utils.text_opt('YZ', 'xyzw', 0))
        self.assertTrue(utils.text_opt('čď', 'áčďě', 0))
        self.assertFalse(utils.text_opt('é', 'áčďě', 0))
        self.assertTrue(utils.text_opt('ČĎ', 'áčďě', 0))
        self.assertTrue(utils.text_opt('čď', 'ÁČĎĚ', 0))
        self.assertTrue(utils.text_opt('ČĎ', 'áčďě', 0))
        self.assertFalse(utils.text_opt('yz', '', 0))
        self.assertTrue(utils.text_opt('', 'xyzw', 0))
        self.assertTrue(utils.text_opt('', '', 0))
        self.assertTrue(utils.text_opt('xy', 'xyzw', 1))
        self.assertFalse(utils.text_opt('y', 'xyzw', 1))
        self.assertFalse(utils.text_opt('q', 'xyzw', 1))
        self.assertTrue(utils.text_opt('XY', 'xyzw', 1))
        self.assertTrue(utils.text_opt('xy', 'XYZW', 1))
        self.assertTrue(utils.text_opt('XY', 'xyzw', 1))
        self.assertTrue(utils.text_opt('áč', 'áčďě', 1))
        self.assertFalse(utils.text_opt('č', 'áčďě', 1))
        self.assertFalse(utils.text_opt('ě', 'áčďě', 1))
        self.assertTrue(utils.text_opt('ÁČ', 'áčďě', 1))
        self.assertTrue(utils.text_opt('áč', 'ÁČĎĚ', 1))
        self.assertTrue(utils.text_opt('ÁČ', 'áčďě', 1))
        self.assertFalse(utils.text_opt('y', '', 1))
        self.assertTrue(utils.text_opt('', 'xyzw', 1))
        self.assertTrue(utils.text_opt('', '', 1))
        self.assertTrue(utils.text_opt('zw', 'xyzw', 2))
        self.assertFalse(utils.text_opt('y', 'xyzw', 2))
        self.assertFalse(utils.text_opt('q', 'xyzw', 2))
        self.assertTrue(utils.text_opt('ZW', 'xyzw', 2))
        self.assertTrue(utils.text_opt('zw', 'XYZW', 2))
        self.assertTrue(utils.text_opt('ZW', 'xyzw', 2))
        self.assertTrue(utils.text_opt('ďě', 'áčďě', 2))
        self.assertFalse(utils.text_opt('č', 'áčďě', 2))
        self.assertFalse(utils.text_opt('á', 'áčďě', 2))
        self.assertTrue(utils.text_opt('ĎĚ', 'áčďě', 2))
        self.assertTrue(utils.text_opt('ďě', 'ÁČĎĚ', 2))
        self.assertTrue(utils.text_opt('ĎĚ', 'áčďě', 2))
        self.assertFalse(utils.text_opt('y', '', 2))
        self.assertTrue(utils.text_opt('', 'xyzw', 2))
        self.assertTrue(utils.text_opt('', '', 2))
        self.assertTrue(utils.text_opt('xyzw', 'xyzw', 3))
        self.assertFalse(utils.text_opt('y', 'xyzw', 3))
        self.assertFalse(utils.text_opt('q', 'xyzw', 3))
        self.assertTrue(utils.text_opt('XYZW', 'xyzw', 3))
        self.assertTrue(utils.text_opt('xyzw', 'XYZW', 3))
        self.assertTrue(utils.text_opt('XYZW', 'xyzw', 3))
        self.assertTrue(utils.text_opt('áčďě', 'áčďě', 3))
        self.assertFalse(utils.text_opt('č', 'áčďě', 3))
        self.assertFalse(utils.text_opt('ě', 'áčďě', 3))
        self.assertTrue(utils.text_opt('ÁČĎĚ', 'áčďě', 3))
        self.assertTrue(utils.text_opt('áčďě', 'ÁČĎĚ', 3))
        self.assertTrue(utils.text_opt('ÁČĎĚ', 'áčďě', 3))
        self.assertFalse(utils.text_opt('y', '', 3))
        self.assertTrue(utils.text_opt('', 'xyzw', 3))
        self.assertTrue(utils.text_opt('', '', 3))

    def test_normalize(self):

        self.assertEqual(utils.normalize('a'), 'a')
        self.assertEqual(utils.normalize(' a'), 'a')
        self.assertEqual(utils.normalize('  a'), 'a')
        self.assertEqual(utils.normalize('a '), 'a')
        self.assertEqual(utils.normalize('a  '), 'a')
        self.assertEqual(utils.normalize('  a  '), 'a')
        self.assertEqual(utils.normalize('a b'), 'a b')
        self.assertEqual(utils.normalize('a  b'), 'a b')
        self.assertEqual(utils.normalize('  a b  '), 'a b')
        self.assertEqual(utils.normalize('  a  b  '), 'a b')
        self.assertEqual(utils.normalize('  a \u00a0 b  '), 'a b')

    def test_icmp(self):

        self.assertTrue(utils.icmp('ab', 'ab'))
        self.assertTrue(utils.icmp('aB', 'Ab'))
        self.assertFalse(utils.icmp('aB', 'AbC'))
        self.assertTrue(utils.icmp('', ''))
        self.assertFalse(utils.icmp(None, ''))
        self.assertTrue(utils.icmp(None, None))
        self.assertFalse(utils.icmp('a', ''))
        self.assertFalse(utils.icmp('', 'a'))


class TestUtils2(TestCase):

    def test_getpreset(self):

        today = date.today()
        models.Preset.objects.get_or_create(
            name='Test',
            value=15,
            valid=today)
        models.Preset.objects.get_or_create(
            name='Test',
            value=16,
            valid=(today + glob.ODP))
        self.assertEqual(utils.getpreset('XXX'), 0)
        self.assertEqual(utils.getpreset('Test'), 15)


class TestViews(TestCase):

    def setUp(self):

        User.objects.create_user(
            'user',
            'user@' + glob.LOCAL_DOMAIN,
            'none'
        )

        User.objects.create_superuser(
            'superuser',
            'superuser@' + glob.LOCAL_DOMAIN,
            'none'
        )

    def test_login(self):

        res = self.client.get('/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/html; charset=utf-8')

        res = self.client.get('/knr')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/knr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertFalse(self.client.login(username='user', password='wrong'))
        self.assertFalse(self.client.login(username='nouser', password='none'))
        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.client.logout()

        res = self.client.get('/knr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/knr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

        res = self.client.get('/xxx/')
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

        res = self.client.post(
            '/accounts/login/?next=/knr/',
            {'username': 'user',
             'password': 'wrong'})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'login.html')
        self.assertContains(
            res,
            'Chybné uživatelské jméno nebo heslo')

        res = self.client.post(
            '/accounts/login/?next=/knr/',
            {'username': 'user',
             'password': 'none'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')

    def test_robots(self):

        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res['content-type'], 'text/plain; charset=utf-8')
        self.assertTemplateUsed(res, 'robots.txt')

        res = self.client.post('/robots.txt')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_unauth(self):

        res = self.client.get('/knr/presets/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/knr/presets/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/knr/presets/')
        self.assertEqual(res.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTemplateUsed(res, 'unauth.html')
        self.assertTrue(self.client.login(
            username='superuser',
            password='none'))

        res = self.client.get('/knr/presets/', follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'knr_mainpage.html')

    def test_error(self):

        req = DummyRequest(None)
        req.method = 'GET'
        res = views.error(req)
        self.assertContains(
            res,
            'Interní chyba aplikace',
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    def test_logout(self):

        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.OK)

        res = self.client.get('/accounts/logout/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/accounts/logout/', follow=True)
        self.assertTemplateUsed(res, 'home.html')

        res = self.client.get('/szr/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/szr/', follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_user(self):

        res = self.client.get('/accounts/user')
        self.assertEqual(res.status_code, HTTPStatus.MOVED_PERMANENTLY)

        res = self.client.get('/accounts/user/')
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get('/accounts/user/', follow=True)
        self.assertTemplateUsed(res, 'login.html')
        self.assertTrue(self.client.login(username='user', password='none'))

        res = self.client.get('/accounts/user/')
        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_pwchange(self):


        self.assertTrue(self.client.login(username='user', password='none'))
        res = self.client.post(
            '/accounts/pwchange/',
            {'back': 'Zpět'},
            follow=True)

        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'home.html')

        res = self.client.get('/accounts/pwchange/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')

        src = {'oldpassword': 'none',
             'newpassword1': 'newpass',
             'newpassword2': 'newpass',
             'submit': 'Změnit'}

        dst = copy(src)
        dst['oldpassword'] = 'wrong'
        res = self.client.post('/accounts/pwchange/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(res.context['error_message'], 'Nesprávné heslo')

        dst = copy(src)
        dst['newpassword1'] = 'different'
        res = self.client.post('/accounts/pwchange/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(
            res.context['error_message'],
            'Zadaná hesla se neshodují')

        dst = copy(src)
        dst['newpassword1'] = dst['newpassword2'] = 'short'
        res = self.client.post('/accounts/pwchange/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchange.html')
        self.assertEqual(
            res.context['error_message'],
            'Nové heslo je příliš krátké')

        res = self.client.post('/accounts/pwchange/', src, follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwchanged.html')
        self.assertTrue(self.client.login(username='user', password='newpass'))

        res = self.client.get('/hsp/')
        self.assertEqual(res.status_code, HTTPStatus.OK)

    def test_pwlost(self):

        pw_regex = compile(r'/accounts/resetpw/([0-9a-f]{32})/')

        res = self.client.get('/accounts/lostpw/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'lostpw.html')

        res = self.client.post(
            '/accounts/lostpw/',
            {'username': '',
             'back': 'Zpět'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'login.html')

        res = self.client.post(
            '/accounts/lostpw/',
            {'username': ''})
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'lostpw.html')

        res = self.client.post(
            '/accounts/lostpw/',
            {'username': 'user'},
            follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'pwlinksent.html')

        msgs = mail.outbox
        self.assertEqual(len(msgs), 1)
        msg = msgs[0]
        self.assertEqual(
            msg.from_email,
            'Server {} <{}>'.format(glob.LOCAL_SUBDOMAIN, glob.LOCAL_EMAIL))
        self.assertEqual(
            msg.to,
            ['user@' + glob.LOCAL_DOMAIN])
        self.assertEqual(
            msg.subject,
            'Link pro obnoveni hesla')
        match = pw_regex.search(msg.body)
        self.assertTrue(match)
        link = match.group(1)
        res = self.client.get('/accounts/resetpw/{}/'.format(link))
        self.assertTemplateUsed(res, 'pwreset.html')
        newpassword = res.context['newpassword']
        self.assertEqual(len(newpassword), 10)
        self.assertFalse(self.client.login(username='user', password='none'))
        self.assertTrue(self.client.login(
            username='user',
            password=newpassword))

    def test_resetpw(self):

        res = self.client.get('/accounts/resetpw/{}/'.format('0' * 32))
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

    def test_home(self):

        res = self.client.get('/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'home.html')

        res = self.client.post('/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_about(self):

        res = self.client.get('/about/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'about.html')

        res = self.client.post('/about/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_stat(self):

        setdl(1)
        setpr(1)

        res = self.client.get('/stat/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'stat.html')

        res = self.client.post('/stat/')
        self.assertEqual(res.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_useradd(self):

        res = self.client.get('/accounts/useradd/')
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')

        src = {
            'first_name': 'Tomáš',
            'last_name': 'Pecina',
            'username': 'newuser',
            'password1': 'newpass',
            'password2': 'newpass',
            'email': 'tomas@' + glob.LOCAL_DOMAIN,
            'captcha': 'Praha',
        }

        dst = copy(src)
        dst['first_name'] = ''
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        dst = copy(src)
        dst['last_name'] = ''
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        dst = copy(src)
        dst['username'] = ''
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        dst = copy(src)
        dst['username'] = 'user'
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        dst = copy(src)
        dst['password1'] = 'different'
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())
        dst = copy(src)

        dst['password1'] = dst['password2'] = 'short'
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        dst = copy(src)
        dst['email'] = 'noemail'
        res = self.client.post('/accounts/useradd/', dst)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradd.html')
        self.assertTrue('err_message' in res.context.keys())

        res = self.client.post('/accounts/useradd/', src, follow=True)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(res, 'useradded.html')
        self.assertTrue(self.client.login(
            username='newuser',
            password='newpass'))
