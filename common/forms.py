# -*- coding: utf-8 -*-
#
# common/forms.py
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

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

MIN_PWLEN = 6

class ValidationError(forms.ValidationError):
    pass

class Form(forms.Form):
    error_css_class = 'err'
    use_required_attribute = False

class UserAddForm(UserChangeForm, UserCreationForm):
    error_css_class = 'err'
    use_required_attribute = False
    captcha = forms.CharField(
        label = 'Kontrolní otázka',
        help_text='Jaké je hlavní město České republiky?')

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['first_name'].label = 'Jméno'
        self.fields['last_name'].required = True
        self.fields['last_name'].label = 'Příjmení'
        self.fields['username'].label = 'Přihlašovací jméno'
        self.fields['username'].help_text = \
            '(nejvýš 30 znaků; pouze písmena, číslice a znaky @/./+/-/_)'
        self.fields['password1'].label = 'Heslo'
        self.fields['password2'].label = 'Potvrzení  hesla'
        self.fields['password2'].help_text = \
            '(zadejte heslo znovu, pro kontrolu)'
        self.fields['email'].label = 'E-mail'
        self.fields['email'].help_text = '(nepovinný)'
        del self.fields['password']
        del self.fields['is_staff']
        del self.fields['is_active']
        del self.fields['is_superuser']
        del self.fields['last_login']
        del self.fields['date_joined']
        del self.fields['groups']
        del self.fields['user_permissions']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username):
            raise ValidationError('Duplicate username')
        return username

    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if len(password1) < MIN_PWLEN:
            raise ValidationError('Password too short')
        return password1

    def clean_captcha(self):
        captcha = self.cleaned_data['captcha']
        if captcha.lower() != 'praha':
            raise ValidationError('Wrong answer')
        return captcha

class LostPwForm(Form):
    username = forms.CharField(
        max_length=150,
        label='Uživatelské jméno')
