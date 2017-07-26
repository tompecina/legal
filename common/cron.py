# -*- coding: utf-8 -*-
#
# common/cron.py
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

from datetime import datetime, timedelta
from django.contrib.auth.models import User
from szr.cron import (
    szr_notice, cron_courts as szr_courts, cron_update as szr_update)
from psj.cron import (
    cron_courtrooms as psj_courtrooms, cron_schedule as psj_schedule,
    cron_update as psj_update)
from udn.cron import cron_update as udn_update, cron_find as udn_find
from sur.cron import sur_notice
from sir.cron import sir_notice, cron_update as sir_update
from dir.cron import dir_notice
from .settings import TEST
from .utils import send_mail, logger
from .glob import localsubdomain, localurl
from .models import Pending, Lock

if TEST:
    def test_func(*args):
        global test_result, test_lock, test_pending
        test_lock = list(Lock.objects.all())
        test_pending = list(Pending.objects.all())
        if not args:
            test_result = 6
        elif len(args) == 1:
            test_result = int(args[0]) * 2
        else:
            test_result = int(args[0]) - int(args[1])

def cron_notify():
    for u in User.objects.all():
        uid = u.id
        text = szr_notice(uid) + sur_notice(uid) + sir_notice(uid) + \
               dir_notice(uid)
        if text and u.email:
            text += 'Server {} ({})\n'.format(localsubdomain, localurl)
            send_mail(
                'Zprava ze serveru {}'.format(localsubdomain),
                text,
                [u.email])
            logger.debug(
                'Email sent to user "{}" ({:d})'.format(
                    User.objects.get(pk=uid).username, uid))
    logger.info('Emails sent')

SCHED = [
    {'name': 'cron_notify',
     'when': lambda t: (t.hour % 6) == 0 and t.minute == 0,
    },
    {'name': 'szr_courts',
     'when': lambda t: t.weekday() == 1 and t.hour == 1 and t.minute == 5,
    },
    {'name': 'szr_update',
     'when': lambda t: True,
     'lock': 'szr',
     'blocking': False,
    },
    {'name': 'psj_courtrooms',
     'when': lambda t: t.weekday() == 0 and t.hour == 4 and t.minute == 10,
     'lock': 'psj',
     'blocking': True,
    },
    {'name': 'psj_schedule',
     'args': '15 22 29',
     'when': lambda t: t.weekday() < 5 and t.hour == 18 and t.minute == 31,
     'lock': 'psj',
     'blocking': True,
    },
    {'name': 'psj_schedule',
     'args': '3 4 5 6 7',
     'when': lambda t: t.weekday() == 5 and t.hour == 20 and t.minute == 1,
     'lock': 'psj',
     'blocking': True,
    },
    {'name': 'psj_update',
     'when': lambda t: (t.minute % 2) == 0,
     'lock': 'psj',
     'blocking': False,
    },
    {'name': 'udn_update',
     'when': lambda t: (t.hour % 4) == 0 and t.minute == 10,
    },
    {'name': 'udn_find',
     'when': lambda t: (t.minute % 15) == 0,
    },
    {'name': 'sir_update',
     'when': lambda t: t.hour in [4, 10, 16, 22] and t.minute == 5,
     'lock': 'sir',
     'blocking': False,
    },
]

EXPIRE = timedelta(minutes=30)

def run(name, args):
    globals()[name](*args.split())

def cron_run():
    now = datetime.now()
    Lock.objects.filter(timestamp_add__lt=(now - EXPIRE)).delete()
    for job in Pending.objects.order_by('timestamp_add'):
        if not Pending.objects.filter(pk=job.id).exists():
            continue
        lock = job.lock
        if not Lock.objects.filter(name=lock).exists():
            job.delete()
            Lock.objects.get_or_create(name=lock)
            args = getattr(job, 'args', '')
            run(job.name, args)
            Lock.objects.filter(name=lock).delete()
            logger.debug(
                'Scheduled job {} with arguments "{}" completed' \
                    .format(job.name, args))
    for job in SCHED:
        if job['when'](now):
            args = job.get('args', '')
            if 'lock' in job:
                lock = job['lock']
                if Lock.objects.filter(name=lock).exists():
                    if job['blocking']:
                        Pending(
                            name=job['name'],
                            args=args,
                            lock=lock
                        ).save()
                        logger.debug(
                            'Job {} with arguments "{}" scheduled' \
                                .format(job['name'], args))
                    continue
                Lock.objects.get_or_create(name=lock)
            run(job['name'], args)
            if 'lock' in job:
                Lock.objects.filter(name=lock).delete()

def cron_unlock():
    Lock.objects.all().delete()
    logger.info('Locks removed')

def cron_clean():
    Pending.objects.all().delete()
    logger.info('Pending jobs deleted')
    cron_unlock()
