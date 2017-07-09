# -*- coding: utf-8 -*-
#
# common/views.py
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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.contrib import auth
from django.contrib.auth.models import User
from django.urls import reverse
from django.apps import apps
from django.db import connection
from django import forms, get_version
from http import HTTPStatus
from random import getrandbits, choice
from datetime import datetime, timedelta
from platform import python_version
from os import uname
from knr.models import Place, Car, Formula
from szr.models import Proceedings
from sur.models import Party
from sir.models import Insolvency
from dir.models import Debtor
from .settings import APPS
from .forms import UserAddForm, LostPwForm, MIN_PWLEN
from .utils import send_mail, getbutton, logger
from .glob import inerr, localsubdomain, localurl
from .models import PwResetLink

@require_http_methods(['GET'])
def robots(request):
    logger.debug('robots.txt requested', request)
    return render(
        request,
        'robots.txt',
        content_type='text/plain; charset=utf-8')

@require_http_methods(['GET', 'POST'])
def unauth(request):
    logger.debug('Unauthorized access', request)
    var = {'page_title': 'Neoprávněný přístup'}
    return render(
        request,
        'unauth.html',
        var,
        status=HTTPStatus.UNAUTHORIZED)

@require_http_methods(['GET', 'POST'])
def error(request):
    logger.debug(
        'Internal server error page generated',
        request)
    var = {
        'page_title': 'Interní chyba aplikace',
        'suppress_topline': True,
    }
    return render(
        request,
        'error.html',
        var,
        status=HTTPStatus.INTERNAL_SERVER_ERROR)

@require_http_methods(['GET', 'POST'])
def logout(request):
    logger.debug(
        'Logout page accessed using method {}'.format(request.method),
        request)
    uid = request.user.id
    uname = request.user.username
    auth.logout(request)
    if uname:
        logger.info(
            'User "{}" ({:d}) logged out'.format(uname, uid),
            request)
    return redirect('home')

@require_http_methods(['GET', 'POST'])
@login_required
def pwchange(request):
    logger.debug(
        'Password change page accessed using method {}'.format(request.method),
        request,
        request.POST)
    var = {'page_title': 'Změna hesla'}
    u = request.user
    uid = u.id
    uname = request.user.username
    if request.method == 'POST':
        if request.POST.get('back'):
            return redirect('home')
        fields = ['oldpassword', 'newpassword1', 'newpassword2']
        for f in fields:
            var[f] = request.POST.get(f, '')
        if not u.check_password(var['oldpassword']):
            var['error_message'] = 'Nesprávné heslo'
            var['oldpassword'] = ''
        elif var['newpassword1'] != var['newpassword2']:
            var['error_message'] = 'Zadaná hesla se neshodují'
            var['newpassword1'] = var['newpassword2'] = ''
        elif len(var['newpassword1']) < MIN_PWLEN:
            var['error_message'] = 'Nové heslo je příliš krátké'
            var['newpassword1'] = var['newpassword2'] = ''
        else:
            u.set_password(var['newpassword1'])
            u.save()
            logger.info(
                'User "{}" ({:d}) changed password'.format(uname, uid),
                request)
            return redirect('/accounts/pwchanged/')
    return render(request, 'pwchange.html', var)

@require_http_methods(['GET', 'POST'])
def lostpw(request):
    logger.debug(
        'Lost password page accessed using method {}'.format(request.method),
        request,
        request.POST)
    err_message = None
    page_title = 'Ztracené heslo'
    if request.method == 'GET':
        f = LostPwForm()
    elif request.POST.get('back'):
        return redirect('login')
    else:
        f = LostPwForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            u = User.objects.filter(username=cd['username'])
            if u.exists() and u[0].email:
                link = '{:032x}'.format(getrandbits(16 * 8))
                PwResetLink(user_id=u[0].id, link=link).save()
                text = \
                    'Vážený uživateli,\n' \
                    'někdo požádal o obnovení hesla pro Váš účet "{0}" na ' \
                    'serveru {1} ({2}).\n\n' \
                    'Pokud skutečně chcete své heslo obnovit, použijte, ' \
                    'prosím, následující jednorázový odkaz:\n\n' \
                    '  {2}{3}\n\n' \
                    'V případě, že jste o obnovení hesla nežádali, ' \
                    'můžete tuto zprávu ignorovat.\n\n' \
                    'Server {1} ({2})\n'.format(
                        u[0].username,
                        localsubdomain,
                        localurl,
                        reverse('resetpw', args=[link]))
                send_mail('Link pro obnoveni hesla', text, [u[0].email])
                logger.info(
                    'Password recovery link for user "{}" ({:d}) sent' \
                        .format(u[0].username, u[0].id),
                    request)
            return redirect('/accounts/pwlinksent/')
        else:
            logger.debug('Invalid form', request)
            err_message = 'Prosím, opravte označená pole ve formuláři'
    return render(
        request,
        'lostpw.html',
        {'f': f,
         'page_title': page_title,
         'err_message': err_message,
        })

LINKLIFE = timedelta(1)
PWCHARS = 'ABCDEFGHJKLMNPQRSTUVWXabcdefghijkmnopqrstuvwx23456789'
PWLEN = 10

@require_http_methods(['GET'])
def resetpw(request, link):
    logger.debug('Password reset page accessed', request)
    PwResetLink.objects \
        .filter(timestamp_add__lt=(datetime.now() - LINKLIFE)).delete()
    p = get_object_or_404(PwResetLink, link=link)
    u = p.user
    newpassword = ''
    for i in range(PWLEN):
        newpassword += choice(PWCHARS)
    u.set_password(newpassword)
    u.save()
    p.delete()
    logger.info(
        'Password for user "{}" ({:d}) reset'.format(u.username, u.id),
        request)
    return render(
        request,
        'pwreset.html',
        {'page_title': 'Heslo bylo obnoveno',
         'newpassword': newpassword,
        })
    
def getappinfo():
    appinfo = []
    for id in APPS:
        c = apps.get_app_config(id)
        version = c.version
        if version:
            appinfo.append(
                {'id': id,
                 'name': c.verbose_name,
                 'version': version,
                 'url': (id + ':mainpage')})
    return appinfo

@require_http_methods(['GET'])
def home(request):
    logger.debug('Home page accessed', request)
    return render(
        request,
        'home.html',
        {'page_title': 'Právnické výpočty',
         'apps': getappinfo(), 'suppress_home': True})

@require_http_methods(['GET'])
def about(request):
    logger.debug('About page accessed', request)
    env = [
        {'name': 'Python', 'version' : python_version()},
        {'name': 'Django', 'version' : get_version()},
        {'name': 'MySQL',
         'version' : '{:d}.{:d}.{:d}'.format(*connection.mysql_version)},
        {'name': 'Platforma', 'version' : '{0}-{2}'.format(*uname())},
    ]
    return render(
        request,
        'about.html',
        {'page_title': 'O aplikaci', 'apps': getappinfo(), 'env': env})

def getappstat():
    appstat = []
    for id in APPS:
        c = apps.get_app_config(id)
        if c.stat:
            appstat.append(
                {'abbr': c.name,
                 'name': c.verbose_name,
                 'stat': c.stat(),
                })
    logger.debug('Statistics combined')
    return appstat

@require_http_methods(['GET'])
def stat(request):
    logger.debug('Statistics page accessed', request)
    return render(
        request,
        'stat.html',
        {'page_title': 'Statistické údaje',
         'apps': getappstat(),
        })

@require_http_methods(['GET'])
@login_required
def user(request):
    logger.debug('User information page accessed', request)
    user = request.user
    user.places = Place.objects.filter(uid=user).count()
    user.cars = Car.objects.filter(uid=user).count()
    user.formulas = Formula.objects.filter(uid=user).count()
    user.proceedings = Proceedings.objects.filter(uid=user).count()
    user.parties = Party.objects.filter(uid=user).count()
    user.insolvencies = Insolvency.objects.filter(uid=user).count()
    user.debtors = Debtor.objects.filter(uid=user).count()
    return render(
        request,
        'user.html',
        {'page_title': 'Informace o uživateli', 'user': user})

@require_http_methods(['GET', 'POST'])
def useradd(request):
    logger.debug(
        'User add page accessed using method {}'.format(request.method),
        request,
        request.POST)
    err_message = None
    if request.method == 'GET':
        f = UserAddForm()
    else:
        f = UserAddForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            user = User.objects.create_user(
                cd['username'],
                cd['email'],
                cd['password1'])
            if user:
                user.first_name = cd['first_name']
                user.last_name = cd['last_name']
                user.save()
                logout(request)
                logger.info(
                    'New user "{}" ({:d}) created' \
                        .format(user.username, user.id),
                    request)
                return redirect('useradded')
            logger.error('Failed to create user', request)
            return error(request)  # pragma: no cover
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
            if 'Duplicate username' in f['username'].errors.as_text():
                err_message = 'Toto uživatelské jméno se již používá'
                logger.debug('Duplicate user name', request)
    return render(
        request,
        'useradd.html',
        {'f': f,
         'page_title': 'Registrace nového uživatele',
         'err_message': err_message,
         'suppress_topline': True,
        })

@require_http_methods(['GET'])
def genrender(request, template=None, **kwargs):
    logger.debug(
        'Generic page rendered using template "{}"'.format(template),
        request)
    return render(request, template, kwargs)
