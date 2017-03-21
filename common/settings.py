# -*- coding: utf-8 -*-
#
# common/settings.py
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

import os.path
import locale
from sys import argv
from logging import Filter
from .secrets import DBPASSWD, SECKEY

LOCAL = ((len(argv) > 1) and (argv[1] == 'runserver'))
TEST = ((len(argv) > 1) and (argv[1] == 'test'))

DEBUG = LOCAL
DEBUG_LOG = True

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_ROOT = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, 'log')

ADMINS = (
    ('Tomas Pecina', 'tomas@pecina.cz'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'legal',
        'USER': 'legal',
        'PASSWORD': DBPASSWD,
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_czech_ci',
        }
    }
}

TIME_ZONE = 'Europe/Prague'
LANGUAGE_CODE = 'cs-CZ'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = os.path.join(LOCAL_ROOT, 'collect').replace('\\','/')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = ()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = SECKEY

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'common.urls'

APPS = ['common',
        'sop',
        'lht',
        'cin',
        'dvt',
        'cnb',
        'knr',
        'hjp',
        'hsp',
        'szr',
        'sur',
        'psj',
        'udn',
        'sir',
        'dir',
        'pir',
        'kos',
        'cache',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
] + [(x + '.apps.' + x.capitalize() + 'Config') for x in APPS]

class AddFields(Filter):

    def filter(self, record):
        a = ''
        if hasattr(record, 'request'):
            if hasattr(record,'params'):
                for k in record.params:
                    if 'password' in k:
                        v = '?'
                    else:
                        v = '"' + record.params[k] + '"'
                    a += ', ' + k + '=' + v + ''
            a += ' [' + record.request.META['REMOTE_ADDR'] + ']'
        record.append = a
        return True

LOGGING_BC = 5

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'logger': {
            'handlers':
                ['error_file', 'info_file'] + \
                (['debug_file'] if DEBUG_LOG else []),
            'level': 'DEBUG',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'add_fields': {
            '()': 'common.settings.AddFields'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 100,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ['add_fields'],
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'info.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 30,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ['add_fields'],
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 10,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ['add_fields'],
        },
    },
    'formatters': {
        'verbose': {
            'format':
                '%(levelname)-7s %(asctime)s %(package)s %(message)s%(append)s'
        },
        'simple': {
            'format': '%(levelname)-7s %(message)s'
        },
    },
}

if not (LOCAL or TEST):  # pragma: no cover
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 15768000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
DECIMAL_SEPARATOR = ','
DATE_FORMAT = 'd.m.Y'
SHORT_DATE_FORMAT = 'd.m.Y'
DATE_INPUT_FORMATS = ['%d.%m.%Y']
ALLOWED_HOSTS = ['*']
LOCALE_PATHS = ()
locale.setlocale(locale.LC_ALL, 'cs_CZ')
