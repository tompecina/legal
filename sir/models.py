# -*- coding: utf-8 -*-
#
# sir/models.py
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

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import (
    MinLengthValidator, MinValueValidator, MaxValueValidator, RegexValidator)
from common.utils import composeref
from common.glob import text_opts, ic_regex, rc_regex, psc_regex

class DruhAdresy(models.Model):
    desc = models.CharField(
        max_length=10)

    def __str__(self):
        return self.desc

class Adresa(models.Model):
    druhAdresy = models.ForeignKey(
        DruhAdresy,
        on_delete=models.CASCADE)
    mesto = models.CharField(
        null=True,
        max_length=255,
        db_index=True)
    ulice = models.CharField(
        null=True,
        max_length=255)
    cisloPopisne = models.CharField(
        null=True,
        max_length=10)
    okres = models.CharField(
        null=True,
        max_length=30)
    zeme = models.CharField(
        null=True,
        max_length=255)
    psc = models.CharField(
        null=True,
        max_length=5,
        validators=[RegexValidator(regex=psc_regex)],
        db_index=True)
    telefon = models.CharField(
        null=True,
        max_length=30)
    fax = models.CharField(
        null=True,
        max_length=30)
    textAdresy = models.CharField(
        null=True,
        max_length=255)
    timestamp = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return self.mesto

class DruhRoleVRizeni(models.Model):
    desc = models.CharField(
        max_length=10)

    def __str__(self):
        return self.desc

class Osoba(models.Model):
    idOsobyPuvodce = models.CharField(
        max_length=20)
    idOsoby = models.CharField(
        max_length=20)
    druhRoleVRizeni = models.ForeignKey(
        DruhRoleVRizeni,
        on_delete=models.CASCADE)
    nazevOsoby = models.CharField(
        max_length=255,
        db_index=True)
    nazevOsobyObchodni = models.CharField(
        null=True,
        max_length=255)
    jmeno = models.CharField(
        null=True,
        max_length=40,
        db_index=True)
    titulPred = models.CharField(
        null=True,
        max_length=50)
    titulZa = models.CharField(
        null=True,
        max_length=50)
    ic = models.CharField(
        null=True,
        max_length=9,
        validators=[RegexValidator(regex=ic_regex)],
        db_index=True)
    dic = models.CharField(
        null=True,
        max_length=14,
        db_index=True)
    datumNarozeni = models.DateField(
        null=True,
        db_index=True)
    rc = models.CharField(
        max_length=10,
        null=True,
        validators=[RegexValidator(regex=rc_regex)],
        db_index=True)
    adresy = models.ManyToManyField(
        Adresa)
    timestamp = models.DateTimeField(
        auto_now=True)
    
    class Meta:
        unique_together = ('idOsoby', 'idOsobyPuvodce')

    def __str__(self):
        return self.nazevOsoby

class DruhStavRizeni(models.Model):
    desc = models.CharField(
        max_length=10)

    def __str__(self):
        return self.desc

class Vec(models.Model):
    idOsobyPuvodce = models.CharField(
        max_length=20,
        db_index=True)
    senat = models.SmallIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        db_index=True)
    bc = models.PositiveIntegerField()
    rocnik = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2008)],
        db_index=True)
    druhStavRizeni = models.ForeignKey(
        DruhStavRizeni,
        null=True,
        on_delete=models.CASCADE)
    firstAction = models.DateField(
        db_index=True)
    lastAction = models.DateField(
        db_index=True)
    datumVyskrtnuti = models.DateField(
        null=True,
        db_index=True)
    link = models.URLField(
        null=True)
    osoby = models.ManyToManyField(
        Osoba)
    timestamp = models.DateTimeField(
        auto_now=True)

    class Meta:
        unique_together = ('rocnik', 'bc', 'idOsobyPuvodce')
        index_together = ('firstAction', 'rocnik', 'bc', 'idOsobyPuvodce')

    def __str__(self):
        return '%s, %s' % \
            (self.idOsobyPuvodce,
             composeref(
                 self.senat,
                 'INS',
                 self.bc,
                 self.rocnik))

class Counter(models.Model):
    id = models.CharField(
        max_length=30,
        primary_key=True)
    number = models.IntegerField()

    def __str__(self):
        return str(self.number)

class Transaction(models.Model):
    id = models.PositiveIntegerField(
        primary_key=True)
    datumZalozeniUdalosti = models.DateTimeField()
    datumZverejneniUdalosti = models.DateTimeField()
    dokumentUrl = models.URLField(
        null=True)
    spisovaZnacka = models.CharField(
        max_length=50)
    typUdalosti = models.CharField(
        max_length=255)
    popisUdalosti = models.CharField(
        max_length=255)
    oddil = models.CharField(
        max_length=10,
        null=True)
    cisloVOddilu = models.IntegerField(
        null=True)
    poznamkaText = models.TextField(
        null=True)
    timestamp = models.DateTimeField(
        auto_now=True)
    
    def __str__(self):
        return str(self.id) + ', ' + self.spisovaZnacka

class Error(models.Model):
    id = models.PositiveIntegerField(
        primary_key=True)
    datumZalozeniUdalosti = models.DateTimeField()
    datumZverejneniUdalosti = models.DateTimeField()
    dokumentUrl = models.URLField(
        null=True)
    spisovaZnacka = models.CharField(
        max_length=50)
    typUdalosti = models.CharField(
        max_length=255)
    popisUdalosti = models.CharField(
        max_length=255)
    oddil = models.CharField(
        max_length=10,
        null=True)
    cisloVOddilu = models.IntegerField(
        null=True)
    poznamkaText = models.TextField(
        null=True)
    timestamp = models.DateTimeField(
        auto_now=True)
    
    def __str__(self):
        return str(self.id) + ', ' + self.spisovaZnacka

class Insolvency(models.Model):
    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    year = models.IntegerField(
        validators=[MinValueValidator(1990)])
    desc = models.CharField(
        max_length=255,
        blank=True)
    detailed = models.BooleanField(
        default=False)
    timestamp = models.DateTimeField(
        auto_now=True)

    class Meta:
        index_together = ('number', 'year')

    def __str__(self):
        return 'INS %d/%d' % (self.number, self.year)

class Tracked(models.Model):
    uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    desc = models.CharField(
        max_length=255,
        db_index=True)
    vec = models.ForeignKey(
        Vec,
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(
        auto_now=True)

    def __str__(self):
        return self.desc
