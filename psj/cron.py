# -*- coding: utf-8 -*-
#
# psj/cron.py
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

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from bs4 import BeautifulSoup
from time import sleep
from common.utils import get
from szr.models import Court
from szr.glob import supreme_administrative_court
from .models import Courtroom

list_courtrooms = 'http://infosoud.justice.cz/InfoSoud/seznamJednacichSini?' \
                  'okres=%s'

@require_http_methods(['GET'])
def cron_courtrooms(request):
    for c in Court.objects.exclude(id=supreme_administrative_court):
        try:
            sleep(1)
            res = get(list_courtrooms % c.pk)
            soup = BeautifulSoup(res.text, 'xml')
            for r in soup.find_all('jednaciSin'):
                if not Courtroom.objects.filter(court=c,
                                                name=r.id.string,
                                                desc=r.nazev.string).exists():
                    Courtroom(court=c,
                              name=r.id.string,
                              desc=r.nazev.string).save()
        except:
            pass
    return HttpResponse()
