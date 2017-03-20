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
from django import forms
from django.apps import apps
from http import HTTPStatus
from random import getrandbits, choice
from datetime import datetime, timedelta
from .settings import APPS
from .forms import UserAddForm, LostPwForm, MIN_PWLEN
from .utils import send_mail, getbutton, logger
from .glob import inerr, localsubdomain, localurl
from .models import PwResetLink

@require_http_methods(['GET'])
def robots(request):
    logger.debug('robots.txt requested')
    return render(
        request,
        'robots.txt',
        content_type='text/plain; charset=utf-8')

@require_http_methods(['GET', 'POST'])
def unauth(request):
    logger.debug('Unauthorized access')
    var = {'page_title': 'Neoprávněný přístup'}
    return render(
        request,
        'unauth.html',
        var,
        status=HTTPStatus.UNAUTHORIZED)

@require_http_methods(['GET', 'POST'])
def error(request):
    logger.debug('Internal server error page generated')
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
    logger.debug('Logout page accessed using method ' + request.method)
    uid = request.user.id
    uname = request.user.username
    auth.logout(request)
    if uname:
        logger.info('User "%s" (%d) logged out' % (uname, uid))
    return redirect('home')

@require_http_methods(['GET', 'POST'])
@login_required
def pwchange(request):
    logger.debug('Password change page accessed using method ' + request.method)
    var = {'page_title': 'Změna hesla'}
    u = request.user
    uid = u.id
    uname = request.user.username
    if request.method == 'POST':
        if request.POST.get('back'):
            return redirect('home')
        fields = ['oldpw', 'newpw1', 'newpw2']
        for f in fields:
            var[f] = request.POST.get(f, '')
        if not u.check_password(var['oldpw']):
            var['error_message'] = 'Nesprávné heslo'
            var['oldpw'] = ''
        elif var['newpw1'] != var['newpw2']:
            var['error_message'] = 'Zadaná hesla se neshodují'
            var['newpw1'] = var['newpw2'] = ''
        elif len(var['newpw1']) < MIN_PWLEN:
            var['error_message'] = 'Nové heslo je příliš krátké'
            var['newpw1'] = var['newpw2'] = ''
        else:
            u.set_password(var['newpw1'])
            u.save()
            logger.info('User "%s" (%d) changed password' % (uname, uid))
            return redirect('/accounts/pwchanged/')
    return render(request, 'pwchange.html', var)

@require_http_methods(['GET', 'POST'])
def lostpw(request):
    logger.debug('Lost password page accessed using method ' + request.method)
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
                link = '%032x' % getrandbits(16 * 8)
                PwResetLink(user_id=u[0].id, link=link).save()
                text = \
                    ('Vážený uživateli,\n' \
                    'někdo požádal o obnovení hesla pro Váš účet "%s" na ' \
                    'serveru ' + localsubdomain + ' (' + localurl + ').\n\n' \
                    'Pokud skutečně chcete své heslo obnovit, použijte, ' \
                    'prosím, následující jednorázový odkaz:\n\n' \
                    '  ' + localurl + '%s\n\n' \
                    'V případě, že jste o obnovení hesla nežádali, ' \
                    'můžete tuto zprávu ignorovat.\n\n' \
                    'Server ' + localsubdomain + ' (' + localurl + ')\n') % \
                    (u[0].username, reverse('resetpw', args=[link]))
                send_mail('Link pro obnoveni hesla', text, [u[0].email])
                logger.info(
                    'Password recovery link for user "%s" (%d) sent' % \
                    (u[0].username, u[0].id))
            return redirect('/accounts/pwlinksent/')
        else:
            logger.debug('Invalid form')
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
    logger.debug('Password reset page accessed')
    PwResetLink.objects \
        .filter(timestamp_add__lt=(datetime.now() - LINKLIFE)).delete()
    p = get_object_or_404(PwResetLink, link=link)
    u = p.user
    newpw = ''
    for i in range(PWLEN):
        newpw += choice(PWCHARS)
    u.set_password(newpw)
    u.save()
    p.delete()
    logger.info('Password for user "%s" (%d) reset' % (u.username, u.id))
    return render(
        request,
        'pwreset.html',
        {'page_title': 'Heslo bylo obnoveno',
         'newpw': newpw,
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
    logger.debug('Application information generated')
    return appinfo

@require_http_methods(['GET'])
def home(request):
    logger.debug('Home page accessed')
    return render(
        request,
        'home.html',
        {'page_title': 'Právnické výpočty',
         'apps': getappinfo(), 'suppress_home': True})

@require_http_methods(['GET'])
def about(request):
    logger.debug('About page accessed')
    return render(
        request,
        'about.html',
        {'page_title': 'O aplikaci', 'apps': getappinfo()})

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
    logger.debug('Statistics page accessed')
    return render(
        request,
        'stat.html',
        {'page_title': 'Statistické údaje',
         'apps': getappstat(),
        })

@require_http_methods(['GET', 'POST'])
def useradd(request):
    logger.debug('User add page accessed using method ' + request.method)
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
                    'New user "%s" (%d) created' % (user.username, user.id))
                return redirect('useradded')
            logger.error('Failed to create user')
            return error(request)  # pragma: no cover
        else:
            logger.debug('Invalid form')
            err_message = inerr
            if 'Duplicate username' in f['username'].errors.as_text():
                err_message = 'Toto uživatelské jméno se již používá'
                logger.debug('Duplicate user name')
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
    logger.debug('Generic page rendered using template "' + template + '"')
    return render(request, template, kwargs)
