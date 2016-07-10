# -*- coding: utf-8 -*-
#
# cache/main.py
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

from datetime import datetime
from base64 import b64encode, b64decode
from common.utils import get
from .models import Cache, Asset

now = datetime.now()

def getcache(url, lifespan, test=False, test_response=None):
    Cache.objects.filter(expire__lt=now).delete()
    c = Cache.objects.filter(url=url)
    if c:
        return (c[0].text, None)
    if test:
        t = test_response
    else:
        u = get(url)
        if not u.ok:
            return (None, 'Chyba při komunikaci se serverem')
        t = u.text
    Cache(url=url,
          text=t,
          expire=((now + lifespan) if lifespan else None)
    ).save()
    return (t, None)

def getasset(request, asset):
    Asset.objects.filter(expire__lt=now).delete()
    sid = request.COOKIES.get('sessionid')
    if not sid:
        return None
    a = Asset.objects.filter(sessionid=sid, assetid=asset)
    return (b64decode(a[0].data) if a else None)

def setasset(request, asset, data, lifespan):
    sid = request.COOKIES.get('sessionid')
    if not sid:
        return False
    Asset.objects.filter(sessionid=sid, assetid=asset).delete()
    Asset(sessionid=sid,
          assetid=asset,
          data=b64encode(data),
          expire=((now + lifespan) if lifespan else None)
    ).save()
    return True
