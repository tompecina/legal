# -*- coding: utf-8 -*-
#
# common/widgets.py
#
# copyright (c) 2011-17 tomáš pecina <tomas@pecina.cz>
#
# this file is part of legal.pecina.cz, a web-based toolbox for lawyers.
#
# this application is free software: you can redistribute it and/or
# modify it under the terms of the gnu general public license as
# published by the free software foundation, either version 3 of the
# license, or (at your option) any later version.
#
# this application is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the
# gnu general public license for more details.
#
# you should have received a copy of the gnu general public license
# along with this program.  if not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.utils.safestring import mark_safe


class Aw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '15', 'maxlength': '25'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Saw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '8', 'maxlength': '8'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Sew(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '50'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Msew(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '35'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Ssew(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '20'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Abbrw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '12'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Genw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '60'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Gpsw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '12', 'maxlength': '20'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Consw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '4', 'maxlength': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Taw(forms.Textarea):

    def __init__(self, **kwargs):
        attrs = {'rows': '8', 'cols': '80'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)

    def render(self, *args, **kwargs):
        return mark_safe(
            super().render(*args, **kwargs).replace('>\n', '>', 1))


class Currw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '3', 'maxlength': '3', 'class': 'toupper'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Ratew(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '15', 'maxlength': '25'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Fxw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '6', 'maxlength': '10'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Sdw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '50', 'maxlength': '50'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Shw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '4', 'maxlength': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Yw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '4'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Hw(forms.HiddenInput):

    pass


class Emw(forms.TextInput):

    def __init__(self, **kwargs):
        attrs = {'size': '40'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(**kwargs)


class Rs(forms.RadioSelect):

    pass


class CurrencyWidget(forms.widgets.MultiWidget):

    template_name = 'currencywidget.html'

    std_curr = ('EUR', 'CHF', 'GBP', 'JPY', 'RUB', 'USD')

    def __init__(self, czk=True, attrs=None):
        self._currlist = (('CZK',) if czk else ()) + self.std_curr
        super().__init__(
            (forms.Select(
                choices=[(x, x) for x in self._currlist] + [('OTH', 'Jiná:')],
                attrs={'class': 'currsel'}),
             Currw()),
            attrs)

    def decompress(self, value):
        if value in self._currlist:
            return (value, None)
        return ('OTH', value)


class Dw(forms.DateInput):

    def __init__(self, **kwargs):
        attrs = {'size': '10', 'maxlength': '12'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        self._today = kwargs.pop('today', False)
        super().__init__(**kwargs)

    def render(self, name, *args, **kwargs):
        res = super().render(name, *args, **kwargs)
        if self._today:
            return mark_safe(
                '<span class="dw-today">{0}<input type="submit" name="submit_set_{1}" value="Dnes" class="today" id="id_set_{1}"></span>'
                .format(res, name))
        return res
