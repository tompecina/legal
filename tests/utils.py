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
from io import BytesIO

from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from tinycss import make_parser
from lxml.etree import parse, XMLSchema
from django.http import QueryDict

from legal.settings import TEST_DIR, TEST_DATA_DIR, STATIC_URL, APPS, BASE_DIR
from legal.common.utils import new_xml
from legal.common.models import Lock, Pending
from legal.sir.models import Counter


with open(join(BASE_DIR, 'lib', 'xhtml5.xsd'), 'rb') as xsdfile:
    XSD = xsdfile.read()


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


class Schema:

    def __init__(self, xsd):
        xmlschema_doc = parse(BytesIO(xsd))
        self.schema = XMLSchema(xmlschema_doc)


SCHEMAS = {}


def validate_xml(xml, xsd):

    key = hash(xsd)
    if key not in SCHEMAS:
        SCHEMAS[key] = Schema(xsd)
    xmlschema = SCHEMAS[key].schema
    doc = parse(BytesIO(xml))
    return xmlschema.validate(doc)


class Request:

    def __init__(self, method, url, parameters=None):
        self.method = method
        if method == 'GET':
            if '?' in url:
                self.url, query = url.split('?', 1)
                self.parameters = QueryDict(query).dict()
            else:
                self.url = url
                self.parameters = parameters
        elif method == 'POST':
            self.url = url
            self.parameters = parameters.decode() if isinstance(parameters, bytes) else parameters
        else:
            raise ValueError('Invalid method')
        self.hashable_parameters = frozenset(self.parameters) if isinstance(self.parameters, dict) else self.parameters

    def __eq__(self, other):
        return self.method == other.method and self.url == other.url and self.parameters == other.parameters

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.method, self.url, self.hashable_parameters))

    def to_xml(self, xml):
        t_request = xml.new_tag('request')
        t_request['method'] = self.method
        t_url = xml.new_tag('url')
        t_request.append(t_url)
        t_url.append(self.url)
        if self.parameters:
            t_parameters = xml.new_tag('parameters')
            t_request.append(t_parameters)
            if isinstance(self.parameters, dict):
                for key, val in self.parameters.items():
                    t_parameter = xml.new_tag('parameter')
                    t_parameters.append(t_parameter)
                    t_name = xml.new_tag('name')
                    t_parameter.append(t_name)
                    t_name.append(key)
                    t_value = xml.new_tag('value')
                    t_parameter.append(t_value)
                    t_value.append(str(val))
            else:
                t_parameters.append(self.parameters)
        return t_request

    @staticmethod
    def from_xml(t_request):
        method = t_request['method']
        url = t_request.url.text
        t_parameters = t_request.find('parameters')
        if t_parameters:
            t_parameter_s = t_parameters.find_all('parameter')
            if t_parameter_s:
                parameters = {}
                for t_parameter in t_parameter_s:
                    parameters[t_parameter.find('name').text] = t_parameter.value.text
            else:
                parameters = t_parameters.text
        else:
            parameters = None
        return Request(method, url, parameters)


class Response:

    def __init__(self, content, status=HTTPStatus.OK):
        if content is None:
            self.content = ''
        elif isinstance(content, bytes):
            self.content = content.decode()
        else:
            self.content = str(content)
        self.status = int(status)

    def __eq__(self, other):
        return self.status == other.status and self.content == other.content

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.content, self.status))

    def to_xml(self, xml):
        t_response = xml.new_tag('response')
        t_response['status'] = self.status
        t_response.append(self.content)
        return t_response

    @staticmethod
    def from_xml(t_response):
        return Response(t_response.text, int(t_response['status']))


class Pairs(dict):

    def __init__(self):
        super().__init__(self)
        with open(join(TEST_DATA_DIR, 'common_pairs.xml'), 'rb') as infile:
            t_pairs = new_xml(infile.read()).find('pairs')
        t_pair_s = t_pairs.find_all('pair')
        for t_pair in t_pair_s:
            request = Request.from_xml(t_pair.request)
            response = Response.from_xml(t_pair.response)
            self[request] = response


PAIRS = Pairs()


def test_req(post, *args):

    request = Request('POST' if post else 'GET', args[0], *args[1:])
    if request in PAIRS:
        response = PAIRS[request]
        return DummyResponse(response.content, status=response.status)
    return DummyResponse(None, status=HTTPStatus.NOT_FOUND)


def test_content(content):

    if not validate_xml(content, XSD):
        raise AssertionError('XML does not validate')


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
        super().__init__(self)
        if not WRITE_CHECKFILE:
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


def parse_tokens(tokens):

    classes = set()
    dot = False
    for token in tokens:
        if token.is_container:
            dot = False
            classes.update(parse_tokens(token.content))
        elif token.type == 'DELIM' and token.value == '.':
            dot = True
        else:
            if dot and token.type == 'IDENT':
                classes.add(token.value)
            dot = False
    return classes


CSS_CLASSES_RE = compile(r'// +css_classes: +(.*) *$')


def parse_comments(data):

    classes = set()
    for line in data.splitlines():
        match = CSS_CLASSES_RE.match(line)
        if match:
            classes = classes.union(set(match.group(1).split()))
    return classes


class ClassArray(dict):

    def __init__(self):
        super().__init__(self)
        parser = make_parser()
        for app in APPS + ('acc',):
            try:
                with open(
                        join(BASE_DIR, 'legal', 'common' if app == 'acc' else app, 'static', '{}.scss'.format(app)),
                        'r'
                ) as infile:
                    scss = infile.read()
            except FileNotFoundError:
                pass
            self[app] = parse_comments(scss)

            try:
                with open(
                        join(BASE_DIR, 'legal', 'common' if app == 'acc' else app, 'static', '{}.css'.format(app)),
                        'r'
                ) as infile:
                    css = infile.read()
            except FileNotFoundError:
                pass
            stylesheet = parser.parse_stylesheet(css)
            for ruleset in stylesheet.rules:
                selector = ruleset.selector
                self[app].update(parse_tokens(selector))

            try:
                with open(
                        join(BASE_DIR, 'legal', 'common' if app == 'acc' else app, 'static', '{}.js'.format(app)),
                        'r'
                ) as infile:
                    js = infile.read()
            except FileNotFoundError:
                pass
            self[app] = self[app].union(parse_comments(js))

        for app in APPS:
            if app != 'common':
                self[app] = self[app].union(self['common'])
        self['common'] = self['common'].union(self['acc'])


CHECK_ARRAY = CheckArray()
CLASS_ARRAY = ClassArray()


def check_html(runner, html, key=None, app=None, check_html=True, check_classes=True):

    caller = stack()[1]
    filepos = '{}:{:d}'.format(caller.filename.rpartition('/')[2], caller.lineno)
    app = app or filepos.partition('_')[2].partition('.')[0]
    if key:
        filepos += '-{}'.format(key)

    store = []
    soup = BeautifulSoup(html, 'html.parser')
    for desc in soup.descendants:
        if isinstance(desc, Tag):
            name = desc.name
            attrs = desc.attrs
            store.append(name)
            for attr in sorted(attrs):
                tag = str(attrs.get('name'))
                if name == 'input' and tag == 'csrfmiddlewaretoken' and attr == 'value':
                    continue
                store.append(attr)
                val = attrs[attr]
                if check_classes and attr == 'class':
                    for cls in val:
                        if cls:
                            runner.assertIn(cls, CLASS_ARRAY[app], msg=filepos)
                if isinstance(val, list):
                    store.extend(sorted(val))
                elif (isinstance(val, str)
                    and not (val.startswith(STATIC_URL) or ('date' in tag and attr == 'value'))):
                    if '?' in val:
                        part = val.rpartition('?')
                        store.append(part[0])
                        for arg in sorted(part[2].split('&')):
                            store.append(arg)
                    else:
                        store.append(val)
        elif isinstance(desc, NavigableString):
            store.append(str(desc))
    string = ' '.join(' '.join(store).split())
    hsh = md5(string.encode()).hexdigest()

    if check_html:
        if WRITE_CHECKFILE:
            print(filepos, hsh, file=CHECKFILE)
        elif CHECK_HTML:
            runner.assertIn(filepos, CHECK_ARRAY, msg=filepos)
            runner.assertEqual(CHECK_ARRAY[filepos], hsh, msg=filepos)
