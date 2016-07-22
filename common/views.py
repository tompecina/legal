# -*- coding: utf-8 -*-
#
# common/views.py
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

from django.shortcuts import render, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.contrib import auth
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import forms
from django.apps import apps
from http import HTTPStatus
from random import getrandbits, choice
from datetime import datetime, timedelta
from .settings import APPS
from .forms import UserAddForm, LostPwForm, MIN_PWLEN
from .utils import send_mail, inerr, getbutton
from .models import PwResetLink
from knr.presets import udbreset

@require_http_methods(['GET'])
def robots(request):
    return render(
        request,
        'robots.txt',
        content_type='text/plain; charset=utf-8')

@require_http_methods(['GET', 'POST'])
def unauth(request):
    var = {'page_title': 'Neoprávněný přístup'}
    return render(
        request,
        'unauth.html',
        var,
        status=HTTPStatus.UNAUTHORIZED)

@require_http_methods(['GET', 'POST'])
def error(request):
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
    auth.logout(request)
    return redirect('home')

@require_http_methods(['GET', 'POST'])
@login_required
def pwchange(request):
    var = {'page_title': 'Změna hesla'}
    u = request.user
    uid = u.id
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
            if request.user.username != 'guest':
                u.save()
            return redirect('/accounts/pwchanged/')
    return render(request, 'pwchange.html', var)

@require_http_methods(['GET', 'POST'])
def lostpw(request):
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
            if u and u[0].email:
                link = '%032x' % getrandbits(16 * 8)
                PwResetLink(user_id=u[0].id, link=link).save()
                text = \
                    'Vážený uživateli,\n' \
                    'někdo požádal o obnovení hesla pro Váš účet "%s" na ' \
                    'serveru legal.pecina.cz (https://legal.pecina.cz).\n\n' \
                    'Pokud skutečně chcete své heslo obnovit, použijte, ' \
                    'prosím, následující jednorázový odkaz:\n\n' \
                    '  https://legal.pecina.cz%s\n\n' \
                    'V případě, že jste o obnovení hesla nežádali, ' \
                    'můžete tuto zprávu ignorovat.\n\n' \
                    'Server legal.pecina.cz (https://legal.pecina.cz)\n' % \
                    (u[0].username, reverse('resetpw', args=[link]))
                send_mail('Link pro obnoveni hesla', text, [u[0].email])
            return redirect('/accounts/pwlinksent/')
        else:
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
    PwResetLink.objects \
        .filter(timestamp__lt=(datetime.now() - LINKLIFE)).delete()
    p = PwResetLink.objects.filter(link=link)
    if not p:
        raise Http404
    u = p[0].user
    newpw = ''
    for i in range(PWLEN):
        newpw += choice(PWCHARS)
    u.set_password(newpw)
    u.save()
    p[0].delete()
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
    return appinfo

@require_http_methods(['GET'])
def home(request):
    return render(
        request,
        'home.html',
        {'page_title': 'Právnické výpočty',
         'apps': getappinfo(), 'suppress_home': True})

@require_http_methods(['GET'])
def about(request):
    return render(
        request,
        'about.html',
        {'page_title': 'O aplikaci', 'apps': getappinfo()})

@require_http_methods(['GET', 'POST'])
def useradd(request):
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
                udbreset(user.id)
                logout(request)
                user = authenticate(
                    username=cd['username'],
                    password=cd['password1'])
                if user:
                    login(request, user)
                    return redirect('home')
            return error(request)  # pragma: no cover
        else:
            err_message = inerr
            if 'Duplicate username' in f['username'].errors.as_text():
                err_message = 'Toto uživatelské jméno se již používá'
    return render(
        request,
        'useradd.html',
        {'f': f,
         'page_title': 'Registrace nového uživatele',
         'err_message': err_message,
         'suppress_topline': True,
        })

@require_http_methods(['GET'])
def genrender(request, prefix, template, page_title=None):
    if prefix:  # pragma: no cover
        template = prefix + '_' + template
    return render(request, template + '.html', {'page_title': page_title})
