# -*- coding: utf-8 -*-
#
# common/widgets.py
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

from django import forms
from django.utils.safestring import mark_safe

class aw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '15', 'maxlength': '25'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(aw, self).__init__(**kwargs)

class saw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '8', 'maxlength': '8'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(saw, self).__init__(**kwargs)

class sew(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '50'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(sew, self).__init__(**kwargs)

class msew(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '35'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(msew, self).__init__(**kwargs)

class ssew(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '20'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(ssew, self).__init__(**kwargs)

class abbrw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '12'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(abbrw, self).__init__(**kwargs)

class genw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '60'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(genw, self).__init__(**kwargs)

class gpsw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '12', 'maxlength': '20'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(gpsw, self).__init__(**kwargs)

class consw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '4', 'maxlength': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(consw, self).__init__(**kwargs)

class taw(forms.Textarea):
    def __init__(self, **kwargs):
        attrs = {'rows': '8', 'cols': '80'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(taw, self).__init__(**kwargs)

    def render(self, *args, **kwargs):
        return mark_safe(super(taw, self)
            .render(*args, **kwargs).replace('>\n', '>', 1))

class currw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '3', 'maxlength': '3', 'class': 'toupper'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(currw, self).__init__(**kwargs)

class ratew(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '15', 'maxlength': '25'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(ratew, self).__init__(**kwargs)

class fxw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '6', 'maxlength': '10'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(fxw, self).__init__(**kwargs)

class sdw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '50', 'maxlength': '50'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(sdw, self).__init__(**kwargs)

class shw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '4', 'maxlength': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(shw, self).__init__(**kwargs)

class yw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(yw, self).__init__(**kwargs)

class hw(forms.HiddenInput):
    pass

class emw(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = {'size': '40'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super(emw, self).__init__(**kwargs)

rs = forms.RadioSelect

class CurrencyWidget(forms.widgets.MultiWidget):
    std_curr = ['EUR', 'CHF', 'GBP', 'JPY', 'RUB', 'USD']

    def __init__(self, czk=True, attrs=None):
        self._currlist = ((['CZK'] if czk else []) + self.std_curr)
        super(CurrencyWidget, self).__init__(
            (forms.Select(
                choices=([[x, x] for x in self._currlist] + \
                         [['OTH', 'Jiná:']]),
                attrs={'class': 'currsel'}),
             currw()),
            attrs)

    def decompress(self, value):
        if value in self._currlist:
            return [value, None]
        return ['OTH', value]

    def format_output(self, rw):
        return '&nbsp;'.join(rw).replace('\n', '')

class dw(forms.DateInput):
    def __init__(self, **kwargs):
        attrs = {'size': '10', 'maxlength': '12'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        self._today = kwargs.pop('today', False)
        super(dw, self).__init__(**kwargs)

    def render(self, name, *args, **kwargs):
        r = super(dw, self).render(name, *args, **kwargs)
        if self._today:
            return mark_safe(
                '{0}&nbsp;<input type="submit" name="submit_set_{1}" ' \
                'value="Dnes" class="today" id="id_set_{1}" />' \
                    .format(r, name))
        return r
