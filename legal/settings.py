# -*- coding: utf-8 -*-
#
# settings.py
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

from os.path import dirname, abspath, join
from os import environ
from sys import argv
from locale import setlocale, LC_ALL
from logging import Filter


try:
    from legal.secrets import DBPASSWD, SECKEY
except ImportError:
    DBPASSWD = environ.get('DBPASSWD', '')
    SECKEY = environ.get('SECKEY', 'empty')

TEST = 'TEST' in environ or (len(argv) > 1 and argv[1] == 'test')
LOCAL = len(argv) > 1 and argv[1] == 'runserver'

DEBUG = LOCAL
DEBUG_LOG = True

ALLOWED_HOSTS = ('*' if DEBUG else 'legal.pecina.cz',)

BASE_DIR = dirname(dirname(abspath(__file__)))
LOG_DIR = join(BASE_DIR, 'log')
FONT_DIR = join(BASE_DIR, 'fonts')
TEST_DIR = join(BASE_DIR, 'tests')
TEST_DATA_DIR = join(TEST_DIR, 'data')
TEST_TEMP_DIR = join(TEST_DIR, 'temp')

DBNAME = environ.get('DBNAME', 'legal')
DBUSER = environ.get('DBUSER', 'legal')

if TEST:
    FIXTURE_DIRS = (join(TEST_DIR, 'fixtures'),)

ADMINS = (
    ('Tomas Pecina', 'tomas@pecina.cz'),
)

TIME_ZONE = 'Europe/Prague'
LANGUAGE_CODE = 'cs-CZ'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = False
MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = join(BASE_DIR, 'collect')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

SECRET_KEY = SECKEY

STATICFILES_DIRS = ('external',)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

APPS = (
    'common', 'sop', 'lht', 'cin', 'dvt', 'cnb', 'knr', 'hjp', 'hsp', 'szr', 'sur', 'psj', 'uds', 'udn', 'sir',
    'dir', 'pir', 'kos',
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.postgres',
    'sphinxsearch',
] + ['legal.{}.apps.{}Config'.format(x, x.capitalize()) for x in APPS]

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'csp.middleware.CSPMiddleware',
)

ROOT_URLCONF = 'legal.urls'

TEMPLATES = (
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
)

WSGI_APPLICATION = 'legal.wsgi.application'

SPHINX_DATABASE_NAME = 'sphinx'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DBNAME,
        'USER': DBUSER,
        'PASSWORD': DBPASSWD,
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
        },
        'TEST': {
        }
    },
    SPHINX_DATABASE_NAME: {
        'ENGINE': 'sphinxsearch.backend.sphinx',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '9307',
    },
}

DATABASE_ROUTERS = (
    'sphinxsearch.routers.SphinxRouter',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

class AddFields(Filter):

    def filter(self, record):
        attrs = ''
        if hasattr(record, 'request'):
            if hasattr(record, 'params'):
                for key in record.params:
                    if key == 'csrfmiddlewaretoken':
                        continue
                    if 'password' in key:
                        val = '?'
                    else:
                        val = '"{}"'.format(record.params[key])
                    attrs += ', {}={}'.format(key, val)
            attrs += ' [{}], {}'.format(
                record.request.META['REMOTE_ADDR'],
                record.request.META.get('HTTP_USER_AGENT', '?'))
        record.append = attrs
        return True

LOGGING_BC = 5

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'django.request': {
            'handlers': ('mail_admins',),
            'level': 'ERROR',
            'propagate': True,
        },
        'logger': {
            'handlers':
                ('error_mail', 'error_file', 'info_file')
                + (('debug_file',) if DEBUG_LOG else []),
            'level': 'DEBUG',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'add_fields': {
            '()': 'legal.settings.AddFields'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ('require_debug_false',),
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'error_mail': {
            'level': 'ERROR',
            'filters': ('require_debug_false', 'add_fields'),
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': join(LOG_DIR, 'error.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 100,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ('add_fields',),
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': join(LOG_DIR, 'info.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 30,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ('add_fields',),
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': join(LOG_DIR, 'debug.log'),
            'encoding': 'utf-8',
            'when': 'D',
            'interval': 10,
            'backupCount': LOGGING_BC,
            'formatter': 'verbose',
            'filters': ('add_fields',),
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

CSRF_FAILURE_VIEW = 'legal.common.views.error403_csrf'

if not (LOCAL or TEST):  # pragma: no cover
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 15768000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = ("'self'", 'www.google-analytics.com')
    CSP_IMG_SRC = ("'self'", 'www.google-analytics.com')
    CSP_FORM_ACTION = ("'self'",)
    CSP_BLOCK_ALL_MIXED_CONTENT = True

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
DECIMAL_SEPARATOR = ','
DATE_FORMAT = 'd.m.Y'
SHORT_DATE_FORMAT = 'd.m.Y'
DATE_INPUT_FORMATS = ('%d.%m.%Y',)

JQUERY_VERSION = '3.3.1'
JQUERY_UI_VERSION = '1.12.1'

DEFAULT_CONTENT_TYPE = 'application/xhtml+xml'
DEFAULT_CHARSET = 'utf-8'
FULL_CONTENT_TYPE = '{}; charset={}'.format(DEFAULT_CONTENT_TYPE, DEFAULT_CHARSET)

LOCALE_PATHS = ()
if not TEST:
    setlocale(LC_ALL, 'cs_CZ.UTF-8')
