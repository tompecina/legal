# -*- coding: utf-8 -*-
#
# common/cron.py
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

from django.contrib.auth.models import User
from .utils import send_mail
from .glob import localsubdomain, localurl
from szr.cron import szr_notice
from sur.cron import sur_notice
from sir.cron import sir_notice
from dir.cron import dir_notice

def cron_notify():
    for u in User.objects.all():
        uid = u.id;
        text = szr_notice(uid) + sur_notice(uid) + sir_notice(uid) + \
               dir_notice(uid)
        if text and u.email:
            text += 'Server ' + localsubdomain + ' (' + localurl + ')\n'
            send_mail(
                'Zprava ze serveru ' + localsubdomain,
                text,
                [u.email])
