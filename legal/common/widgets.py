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

from locale import strxfrm

from django import forms
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from legal.szr.models import Court
from legal.sir.glob import L2N
from legal.sir.models import Vec


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
                '<span class="dw-today">{0}<input type="submit" name="submit_set_{1}" value="Dnes" class="today" '
                'id="id_set_{1}"></span>'.format(res, name))
        return res


class CourtWidget(forms.TextInput):

    def __init__(self, supreme_court=False, supreme_administrative_court=False, ins_courts=False, **kwargs):
        self.supreme_court = supreme_court
        self.supreme_administrative_court = supreme_administrative_court
        self.ins_courts = ins_courts
        super().__init__(**kwargs)

    def render(self, name, value, *args, **kwargs):
        context = {'ins_courts': self.ins_courts, 'value': value}
        if self.ins_courts:
            context['courts'] = sorted(
                [{'id': x, 'name': L2N[x]} for x in Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()],
                key=lambda x: strxfrm(x['name']))
        else:
            sel = ['VSPHAAB', 'VSSEMOL']
            if self.supreme_court:
                sel.append('NSJIMBM')
            if self.supreme_administrative_court:
                sel.append('NSS')
            high_courts = Court.objects.filter(id__in=sel).order_by('name')
            high_label = (
                'Nejvyšší a vrchní soudy'
                if self.supreme_administrative_court or self.supreme_administrative_court
                else 'Vrchní soudy')
            high_group = {'label': high_label, 'courts': high_courts}
            context['optgroups'] = [high_group]
            reg_courts = (
                Court.objects.filter(id__startswith='KS').union(Court.objects.filter(id='MSPHAAB')).order_by('name'))
            reg_group = {'label': 'Krajské soudy', 'courts': reg_courts}
            context['optgroups'].append(reg_group)
            for reg_court in reg_courts:
                county_courts = sorted(
                    list(Court.objects.filter(reports=reg_court).order_by('name').values('id', 'name')),
                    key=lambda x: strxfrm('Z' if x['name'].endswith('10') else x['name']))
                county_group = {'label': reg_court.name, 'courts': county_courts}
                context['optgroups'].append(county_group)

        return mark_safe(get_template('select_court.html').render(context))
