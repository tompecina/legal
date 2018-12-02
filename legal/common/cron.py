# -*- coding: utf-8 -*-
#
# common/cron.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from legal.szr.cron import szr_notice, cron_courts as szr_courts, cron_update as szr_update
from legal.psj.cron import (
    cron_courtrooms as psj_courtrooms, cron_schedule as psj_schedule, cron_update as psj_update, cron_update2 as psj_update2)
from legal.settings import TEST
from legal.udn.cron import cron_update as udn_update, cron_find as udn_find
from legal.sur.cron import sur_notice
from legal.sir.cron import sir_notice, cron_update as sir_update, cron_refresh_links as sir_refresh_links
from legal.dir.cron import dir_notice
from legal.uds.cron import (
    cron_publishers as uds_publishers, cron_update as uds_update, uds_notice, cron_remove_orphans as uds_remove_orphans)
from legal.common.glob import LOCAL_SUBDOMAIN, LOCAL_URL
from legal.common.utils import send_mail, LOGGER, holiday
from legal.common.models import Pending, Lock


def cron_notify():

    for user in User.objects.all():
        uid = user.id
        text = szr_notice(uid) + sur_notice(uid) + sir_notice(uid) + dir_notice(uid) + uds_notice(uid)
        if text and user.email:
            text += 'Server {} ({})\n'.format(LOCAL_SUBDOMAIN, LOCAL_URL)
            send_mail(
                'Zprava ze serveru {}'.format(LOCAL_SUBDOMAIN),
                text,
                [user.email])
            LOGGER.debug(
                'Email sent to user "{}" ({:d})'
                .format(User.objects.get(pk=uid).username, uid))
    LOGGER.info('Emails sent')


SCHED = (
    {'name': 'psj_schedule',
     'args': '3 4 5 6 7',
     'when': lambda t: t.weekday() == 4 and t.hour == 20 and t.minute == 1,
    },
    {'name': 'psj_schedule',
     'args': '1 15 29',
     'when': lambda t: t.weekday() in {6, 0, 1, 2, 3} and t.hour == 18 and t.minute == 30,
    },
    {'name': 'cron_notify',
     'when': lambda t: (t.hour % 6) == 0 and t.minute == 0,
     'lock': 'sir_ws2',
     'blocking': True,
    },
    {'name': 'psj_update',
     'when': lambda t: (t.minute % 2) == 0,
     'lock': 'psj',
     'blocking': False,
    },
    {'name': 'psj_update2',
     'when': lambda t: (t.hour % 5) == 0 and t.minute == 40,
     'lock': 'psj_update2',
     'blocking': False,
    },
    {'name': 'udn_update',
     'when': lambda t: (t.hour % 4) == 0 and t.minute == 10,
     'lock': 'udn',
     'blocking': False,
    },
    {'name': 'udn_find',
     'when': lambda t: (t.minute % 15) == 0,
     'lock': 'udn',
     'blocking': False,
    },
    {'name': 'szr_update',
     'when': lambda t: True,
     'lock': 'szr',
     'blocking': False,
    },
    {'name': 'psj_courtrooms',
     'when': lambda t: t.weekday() == 6 and t.hour == 4 and t.minute == 10,
     'lock': 'psj',
     'blocking': True,
    },
    {'name': 'szr_courts',
     'when': lambda t: t.weekday() == 0 and t.hour == 1 and t.minute == 5,
    },
    {'name': 'uds_publishers',
     'when': lambda t: t.weekday() == 0 and t.hour == 1 and t.minute == 15,
    },
    {'name': 'sir_refresh_links',
     'when': lambda t: True,
     'lock': 'sir_ws2',
     'blocking': False,
    },
    {'name': 'uds_update',
     'when': lambda t: not holiday(t.date()) and t.hour == 19 and t.minute == 15,
     'lock': 'uds',
     'blocking': False,
    },
    {'name': 'uds_remove_orphans',
     'when': lambda t: t.weekday() == 6 and t.hour == 0 and t.minute == 5,
     'lock': 'uds',
     'blocking': False,
    },
    {'name': 'sir_update',
     'when': lambda t: t.hour in {4, 10, 16, 22} and t.minute == 5,
     'lock': 'sir',
     'blocking': False,
    },
)

EXPIRE = timedelta(hours=71)


if TEST:
    from tests.utils import testfunc


LOG_LOCKS = False


def run(name, args):

    globals()[name](*args.split())


def cron_run():

    now = datetime.now()

    expired = Lock.objects.filter(timestamp_add__lt=(now - EXPIRE))
    for lock in expired:
        LOGGER.warning('Expired lock "{}" deleted'.format(lock.name))
    expired.delete()

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
            LOGGER.debug('Scheduled job {} with arguments "{}" completed'.format(job.name, args))

    for job in SCHED:
        if job['when'](now):
            args = job.get('args', '')
            if 'lock' in job:
                lock = job['lock']
                if Lock.objects.filter(name=lock).exists():
                    if LOG_LOCKS:
                        LOGGER.debug('Lock "{}" exists'.format(lock))
                    if job['blocking']:
                        Pending(
                            name=job['name'],
                            args=args,
                            lock=lock
                        ).save()
                        LOGGER.debug('Job {} with arguments "{}" scheduled'.format(job['name'], args))
                    continue
                elif LOG_LOCKS:
                    LOGGER.debug('Lock "{}" does not exist'.format(lock))
                Lock.objects.get_or_create(name=lock)
                if LOG_LOCKS:
                    LOGGER.debug('Lock "{}" set'.format(lock))
            run(job['name'], args)
            if 'lock' in job:
                reslock = Lock.objects.filter(name=lock)
                if reslock.exists():
                    reslock.delete()
                    if LOG_LOCKS:
                        LOGGER.debug('Lock "{}" reset'.format(lock))


def cron_unlock():

    Lock.objects.all().delete()
    LOGGER.info('Locks removed')


def cron_clean():

    Pending.objects.all().delete()
    LOGGER.info('Pending jobs deleted')
    cron_unlock()
