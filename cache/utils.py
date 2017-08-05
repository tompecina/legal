# -*- coding: utf-8 -*-
#
# cache/utils.py
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

from datetime import datetime
from base64 import b64encode, b64decode

from django.db.transaction import atomic

from common.utils import get, logger
from cache.models import Cache, Asset


def getcache(url, lifespan):
    Cache.objects.filter(expire__lt=datetime.now()).delete()
    cache = Cache.objects.filter(url=url)
    if cache:
        return cache[0].text, None
    res = get(url)
    if not res.ok:
        logger.warning('Failed to access URL: "{}"'.format(url))
        return None, 'Chyba při komunikaci se serverem'
    txt = res.text
    Cache(
        url=url,
        text=txt,
        expire=datetime.now() + lifespan if lifespan else None,
    ).save()
    return txt, None


def getasset(request, asset):
    Asset.objects.filter(expire__lt=datetime.now()).delete()
    sid = request.COOKIES.get('sessionid')
    if not sid:
        return None
    asset = Asset.objects.filter(sessionid=sid, assetid=asset)
    return b64decode(asset[0].data) if asset else None


@atomic
def setasset(request, asset, data, lifespan):
    sid = request.COOKIES.get('sessionid')
    if not sid:
        return False
    Asset.objects.filter(sessionid=sid, assetid=asset).delete()
    Asset(
        sessionid=sid,
        assetid=asset,
        data=b64encode(data),
        expire=datetime.now() + lifespan if lifespan else None,
    ).save()
    return True
