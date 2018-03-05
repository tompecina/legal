# -*- coding: utf-8 -*-
#
# common/widgets.py
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

from locale import strxfrm

from django import forms
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from legal.sir.glob import L2N
from legal.sir.models import Vec
from legal.szr.models import Court
from legal.uds.models import Publisher


class TextWidget(forms.TextInput):

    template_name = 'widgets/text.xhtml'

    def __init__(self, size, *args, **kwargs):
        attrs = {'size': size}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class PasswordWidget(TextWidget):

    input_type = 'password'


class CurrencyWidget(forms.TextInput):

    template_name = 'widgets/text.xhtml'

    def __init__(self, *args, **kwargs):
        attrs = {'size': '3', 'maxlength': '3', 'class': 'toupper'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class HiddenWidget(forms.HiddenInput):

    template_name = 'widgets/hidden.xhtml'


class TextAreaWidget(forms.Textarea):

    template_name = 'widgets/textarea.xhtml'

    def __init__(self, *args, **kwargs):
        attrs = {'rows': '8', 'cols': '80'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class SelectWidget(forms.Select):

    template_name = 'widgets/select.xhtml'
    option_template_name = 'widgets/select_option.xhtml'


class RadioWidget(forms.RadioSelect):

    template_name = 'widgets/radio.xhtml'
    option_template_name = 'widgets/radio_option.xhtml'


class CheckboxWidget(forms.CheckboxInput):

    template_name = 'widgets/checkbox.xhtml'


class SelectCurrencyWidget(forms.widgets.MultiWidget):

    template_name = 'widgets/currency.xhtml'

    std_curr = ('EUR', 'CHF', 'GBP', 'JPY', 'RUB', 'USD')

    def __init__(self, czk=True, attrs=None):
        self._currlist = (('CZK',) if czk else ()) + self.std_curr
        super().__init__(
            (SelectWidget(
                choices=[(x, x) for x in self._currlist] + [('OTH', 'Jiná:')],
                attrs={'class': 'currsel'}),
             CurrencyWidget()),
            attrs)

    def decompress(self, value):
        if value in self._currlist:
            return (value, None)
        return ('OTH', value)


class DateWidget(forms.DateInput):

    template_name = 'widgets/date.xhtml'

    def __init__(self, *args, **kwargs):
        attrs = {'size': '10', 'maxlength': '12'}
        attrs.update(kwargs.get('attrs', {}))
        kwargs['attrs'] = attrs
        self._today = kwargs.pop('today', False)
        super().__init__(*args, **kwargs)

    def render(self, name, *args, **kwargs):
        res = super().render(name, *args, **kwargs)
        if self._today:
            return mark_safe('''\
<span class="dw-today">{0}<input type="submit" name="submit_set_{1}" value="Dnes" class="today" id="id_set_{1}"/>\
</span>'''.format(res, name))
        return res


class CourtWidget(TextWidget):

    def __init__(self, *args, supreme_court=False, supreme_administrative_court=False, ins_courts=False, **kwargs):
        self.supreme_court = supreme_court
        self.supreme_administrative_court = supreme_administrative_court
        self.ins_courts = ins_courts
        super().__init__(10, *args, **kwargs)

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

        return mark_safe(get_template('widgets/select_court.xhtml').render(context))


class PublisherWidget(TextWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(10, *args, **kwargs)

    def render(self, name, value, *args, **kwargs):
        high_courts = Publisher.objects.filter(type='SOUD', high=True).order_by('name')
        high_courts_label = 'Nejvyšší a vrchní soudy'
        high_courts_group = {'label': high_courts_label, 'publishers': high_courts}
        context = {'optgroups': [high_courts_group]}
        reg_courts = Publisher.objects.filter(type='SOUD', high=False, reports__isnull=True).order_by('name')
        reg_courts_group = {'label': 'Krajské soudy', 'publishers': reg_courts}
        context['optgroups'].append(reg_courts_group)
        for reg_court in reg_courts:
            county_courts = sorted(
                list(Publisher.objects.filter(
                    reports=reg_court,
                    subsidiary_region=False,
                    subsidiary_county=False,
                ).order_by('name').values('id', 'name')),
                key=lambda x: strxfrm('Z' if x['name'].endswith('10') else x['name']))
            county_courts_group = {'label': reg_court.name, 'publishers': county_courts}
            context['optgroups'].append(county_courts_group)
        high_attorneys = Publisher.objects.filter(type='ZAST', high=True).order_by('name')
        high_attorneys_label = 'Nejvyšší a vrchní státní zastupitelství'
        high_attorneys_group = {'label': high_attorneys_label, 'publishers': high_attorneys}
        context['optgroups'].append(high_attorneys_group)
        reg_attorneys = Publisher.objects.filter(type='ZAST', high=False, reports__isnull=True).order_by('name')
        reg_attorneys_group = {'label': 'Krajská státní zastupitelství', 'publishers': reg_attorneys}
        context['optgroups'].append(reg_attorneys_group)
        for reg_attorney in reg_attorneys:
            county_attorneys = sorted(
                list(Publisher.objects.filter(
                    reports=reg_attorney,
                    subsidiary_region=False,
                    subsidiary_county=False,
                ).order_by('name').values('id', 'name')),
                key=lambda x: strxfrm('Z' if x['name'].endswith('10') else x['name']))
            county_attorneys_group = {'label': reg_attorney.name, 'publishers': county_attorneys}
            context['optgroups'].append(county_attorneys_group)

        return mark_safe(get_template('widgets/select_publisher.xhtml').render(context))
