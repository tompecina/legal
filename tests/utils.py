# -*- coding: utf-8 -*-
#
# tests/utils.py
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
from os import environ
from os.path import join
from re import compile
from hashlib import md5
from inspect import stack

from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from django.http import QueryDict

from common.settings import TEST_DIR, TEST_DATA_DIR, STATIC_URL
from common.models import Lock, Pending
from sir.models import Counter


class DummyRequest:

    def __init__(self, session_id):
        self.COOKIES = {'sessionid': session_id}
        self.META = {'REMOTE_ADDR': ''}


class DummyResponse:

    def __init__(self, content, status=HTTPStatus.OK):
        self.text = content
        if content:
            self.content = content.encode('utf-8')
        self.status_code = status
        self.ok = status == HTTPStatus.OK


class TestObj:
    pass

    
TEST_OBJ = TestObj()


def testfunc(*args):
    TEST_OBJ.testlock = list(Lock.objects.all())
    TEST_OBJ.testpending = list(Pending.objects.all())
    if not args:
        TEST_OBJ.testresult = 6
    elif len(args) == 1:
        TEST_OBJ.testresult = int(args[0]) * 2
    else:
        TEST_OBJ.testresult = int(args[0]) - int(args[1])


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
        with open(join(TEST_DATA_DIR, 'common_{}'.format(filename)), 'rb') as infile:
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


CHECK_HTML = bool(environ.get('CHECK_HTML'))
WRITE_CHECKFILE = bool(environ.get('WRITE_CHECKFILE'))
CHECKFILE = open(join(TEST_DIR, 'test.chk'), 'w' if WRITE_CHECKFILE else 'r')


class CheckArray(dict):

    def __init__(self):

        if WRITE_CHECKFILE:
            return
        for line in CHECKFILE:
            fields = line.split()
            filepos = fields[0]
            if len(fields) == 2:
                hsh = fields[1]
            else:
                filepos += '-' + fields[1]
                hsh = fields[2]
            self[filepos] = hsh
        CHECKFILE.close()


CHECKARRAY = CheckArray()


def check_html(runner, html, key=None):

    caller = stack()[1]
    filepos = '{}:{:d}'.format(caller.filename.rpartition('/')[2], caller.lineno)
    if key:
        filepos += '-{}'.format(key)

    store = []
    soup = BeautifulSoup(html, 'html.parser')
    for desc in soup.descendants:
        if isinstance(desc, Tag):
            name = desc.name
            attrs = desc.attrs
            store.append(name)
            for key in sorted(attrs):
                tag = str(attrs.get('name'))
                if name == 'input' and tag == 'csrfmiddlewaretoken' and key == 'value':
                    continue
                store.append(key)
                val = attrs[key]
                if isinstance(val, list):
                    store.extend(sorted(val))
                elif (isinstance(val, str)
                    and not (val.startswith(STATIC_URL) or ('date' in tag and key == 'value'))):
                    store.append(val)
        elif isinstance(desc, NavigableString):
            store.append(str(desc))
    string = ' '.join(' '.join(store).split())
    hsh = md5(string.encode()).hexdigest()

    if WRITE_CHECKFILE:
        print(filepos, hsh, file=CHECKFILE)
    elif CHECK_HTML:
        runner.assertIn(filepos, CHECKARRAY, msg=filepos)
        runner.assertEqual(CHECKARRAY[filepos], hsh, msg=filepos)
