# -*- coding: utf-8 -*-
#
# uds/cron.py
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
from os import makedirs
from os.path import join
from re import compile, split

from bs4 import BeautifulSoup
from textract import process
from django.contrib.auth.models import User
from django.db import connection

from legal.settings import BASE_DIR, TEST, TEST_TEMP_DIR
from legal.common.glob import ODP
from legal.common.utils import get, sleep, LOGGER, between
from legal.sur.models import Party
from legal.uds.glob import TYPES
from legal.uds.models import Publisher, Agenda, Document, File, Retrieved


ROOT_URL = 'http://infodeska.justice.cz/'
PUBLISHERS_URL = '{}subjekty.aspx?typ={{}}'.format(ROOT_URL)
LIST_URL = '{}historie.aspx?subjkod={{:d}}&datum={{:%d.%m.%Y}}'.format(ROOT_URL)
DETAIL_URL = '{}vyveseni.aspx?verzeid={{:d}}'.format(ROOT_URL)
FILE_URL = '{}soubor.aspx?souborid={{:d}}'.format(ROOT_URL)
REPO_PREF = TEST_TEMP_DIR if TEST else join(BASE_DIR, 'repo', 'uds')

UPDATE_INTERVAL = timedelta(hours=12)


def cron_publishers():

    def proc_publisher(tag, typ, high=False, subsidiary_region=False, subsidiary_county=False, reports=None):
        pubid = int(tag['href'].rpartition('=')[2])
        name = (
            tag.text.replace('  ', ' ')
            .replace('KS ', 'Krajský soud ')
            .replace('MS ', 'Městský soud ')
            .replace('OS Praha ', 'Obvodní soud Praha ')
            .replace('OS ', 'Okresní soud ')
            .replace('KSZ ', 'Krajské státní zastupitelství ')
            .replace('MSZ ', 'Městské státní zastupitelství ')
            .replace('OSZ Praha ', 'Obvodní státní zastupitelství Praha ')
            .replace('OSZ ', 'Okresní státní zastupitelství ')
        )
        return Publisher.objects.update_or_create(
            name=name,
            defaults={
                'type': typ,
                'pubid': pubid,
                'high': high,
                'subsidiary_region': subsidiary_region,
                'subsidiary_county': subsidiary_county,
                'reports': reports,
                'updated': datetime.now() - UPDATE_INTERVAL})[0]


    def proc_publishers(soup, typ, high=False):
        if high:
            for tag in soup.find_all('a'):
                proc_publisher(tag, typ, high=True)
        else:
            rep = proc_publisher(soup.select('dt a')[0], typ)
            for tag in soup.find_all('dd'):
                cls = tag.get('class', [])
                subsidiary_region = 'pobockakraj' in cls
                subsidiary_county = 'pobockaokres' in cls
                proc_publisher(
                    tag.find('a'),
                    typ,
                    subsidiary_region=subsidiary_region,
                    subsidiary_county=subsidiary_county,
                    reports=rep)

    for typ in TYPES:
        try:
            res = get(PUBLISHERS_URL.format(typ))
            soup = BeautifulSoup(res.text, 'html.parser')
            high = soup.find('div', 'bezlokality')
            lower = soup.find('div', 'slokalitou')
            proc_publishers(high, typ, high=True)
            for reg in lower.find_all('dl'):
                proc_publishers(reg, typ, high=False)
        except:
            pass

    LOGGER.info('Publishers imported')


SPLIT_NUM_RE = compile(r'\D+')
SPLIT_STR_RE = compile(r'[\W\d]+')


def split_numbers(string):

    return list(map(int, filter(bool, split(SPLIT_NUM_RE, string))))


def split_strings(string):

    return list(filter(bool, split(SPLIT_STR_RE, string)))


def parse_ref(ref):

    empty = (None,) * 5

    try:
        left, slash, right = ref.partition('/')
        assert slash
        lnum = split_numbers(left)
        rnum = split_numbers(right)
        assert between(1, len(lnum), 2) and between(1, len(rnum), 3)
        senate = lnum[-2] if len(lnum) == 2 else None
        number = lnum[-1]
        year = rnum[0]
        page = rnum[1] if len(rnum) > 1 and rnum[1] else None
        if 'P A NC' in left.upper():
            register = 'P A NC'
        else:
            strings = split_strings(left)
            assert strings
            if len(strings) == 1:
                register = strings[0].upper()
            else:
                for string in strings:
                    if string[0].isupper():
                        register = string.upper()
                        break
                else:
                    return empty
        assert not senate or senate > 0
        assert register
        assert number > 0
        assert between(1990, year, date.today().year)
        assert not page or page > 0
        return senate, register, number, year, page
    except:
        return empty


def cron_update(*args):

    today = date.today()
    if args:
        dates = []
        for arg in args:
            string = arg.split('.')
            dates.append(datetime(*map(int, string[2::-1])))
    else:
        dates = [today + ODP]
    for dat in dates:
        flt = {'subsidiary_region': False, 'subsidiary_county': False}
        if not args:
            flt['updated__lt'] = datetime.now() - UPDATE_INTERVAL
        for publisher in Publisher.objects.filter(**flt):
            try:
                sleep(1)
                res = get(LIST_URL.format(publisher.pubid, dat))
                assert res.ok
                soup = BeautifulSoup(res.text, 'html.parser')
                for link in soup.select('a[href]'):
                    href = link.get('href')
                    if href and href.startswith('vyveseni.aspx?verzeid='):
                        try:
                            docid = int(href.partition('=')[2])
                        except ValueError:
                            continue
                        if Document.objects.filter(docid=docid).exists():
                            continue
                        sleep(1)
                        subres = get(DETAIL_URL.format(docid))
                        assert subres.ok
                        subsoup = BeautifulSoup(subres.text, 'html.parser')
                        rows = subsoup.find_all('tr')
                        desc = ref = senate = register = number = year = page = agenda = posted = None
                        files = []
                        for row in rows:
                            cells = row.find_all('td')
                            if not cells or len(cells) != 2:
                                continue
                            left = cells[0].text.strip()
                            right = cells[1].text.strip()
                            if left == 'Popis':
                                desc = right
                            elif left == 'Značka':
                                ref = right
                                senate, register, number, year, page = parse_ref(ref)
                            elif left == 'Vyvěšení':
                                pdat, ptim = right.split()
                                posted = datetime(*map(int, pdat.split('.')[2::-1]), *map(int, ptim.split(':')))
                            elif left == 'Agenda':
                                agenda = Agenda.objects.get_or_create(desc=right)[0]
                            else:
                                anchor = cells[0].find('a')
                                if not(anchor and anchor.has_attr('href')
                                    and anchor['href'].startswith('soubor.aspx?souborid=')):
                                    continue
                                fileid = int(anchor['href'].partition('=')[2])
                                span = anchor.find('span', 'zkraceno')
                                filename = span['title'].strip() if span else anchor.text.strip()
                                if not filename:
                                    continue
                                if filename.endswith(')'):
                                    filename = filename.rpartition(' (')[0]
                                filename = filename.replace(' ', '_')
                                if fileid not in [x[0] for x in files]:
                                    files.append((fileid, filename))
                        doc = Document.objects.get_or_create(
                            docid=docid,
                            publisher=publisher,
                            desc=desc,
                            ref=ref,
                            senate=senate,
                            register=register,
                            number=number,
                            year=year,
                            page=page,
                            agenda=agenda,
                            posted=posted,
                        )[0]
                        for fileid, filename in files:
                            infile = get(FILE_URL.format(fileid))
                            assert infile.ok
                            content = infile.content
                            dirname = join(REPO_PREF, str(fileid))
                            makedirs(dirname, exist_ok=True)
                            pathname = join(dirname, filename)
                            with open(pathname, 'wb') as outfile:
                                outfile.write(content)
                            if File.objects.filter(fileid=fileid).exists():
                                continue
                            try:
                                text = process(pathname).decode()
                                ocr = len(text) < 5
                                if ocr:
                                    text = process(pathname, method='tesseract', language='ces').decode()
                            except:
                                text = ''
                                ocr = False
                            File.objects.get_or_create(
                                fileid=fileid,
                                document=doc,
                                name=filename,
                                text=text,
                                ocr=ocr,
                            )
                            if not args or TEST:
                                for party in Party.objects.all():
                                    with connection.cursor() as cursor:
                                        try:
                                            cursor.execute(
                                                "SELECT to_tsvector('simple', concat_ws(' ', %s, %s))@@to_tsquery(%s)",
                                                (desc, text, ' <-> '.join(party.party.split())))
                                            res = cursor.fetchone()[0]
                                        except:
                                            res = False
                                    if res:
                                        Retrieved.objects.update_or_create(
                                            uid_id=party.uid_id,
                                            party=party,
                                            document=doc)
                                        if party.uid.email:
                                            Party.objects.filter(id=party.id).update(notify=True)
                                        LOGGER.info(
                                            'New party "{}" detected for user "{}" ({:d})'
                                            .format(
                                                party.party,
                                                User.objects.get(pk=party.uid_id).username,
                                                party.uid_id))
                LOGGER.debug('Updated "{}", {:%Y-%m-%d}'.format(publisher.name, dat))
                if not args:
                    Publisher.objects.filter(id=publisher.id).update(updated=datetime.now())
            except:
                LOGGER.info('Failed to update "{}", {:%Y-%m-%d}'.format(publisher.name, dat))
        LOGGER.debug('Updated all publishers, {:%Y-%m-%d}'.format(dat))


def uds_notice(uid):

    text = ''
    docs = Retrieved.objects.filter(uid=uid).order_by('id').distinct()
    if docs:
        text = 'Na úředních deskách byly nově zaznamenány tyto osoby, které sledujete:\n\n'
        for doc in docs:
            lst = [doc.party.party, doc.document.publisher.name, doc.document.desc]
            if doc.document.ref:
                lst.append('sp. zn. {}'.format(doc.document.ref))
            text += ' - {}\n'.format(', '.join(filter(bool, lst)))
            text += '   {}\n\n'.format(DETAIL_URL.format(doc.document.docid))
        Retrieved.objects.filter(uid=uid).delete()
        LOGGER.info(
            'Non-empty notice prepared for user "{}" ({:d})'.format(User.objects.get(pk=uid).username, uid))
    Party.objects.filter(uid=uid).update(notify=False)
    return text
