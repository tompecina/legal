# -*- coding: utf-8 -*-
#
# common/management/commands/cron.py
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

from django.core.management.base import BaseCommand
from importlib import import_module
import szr.cron
import psj.cron
import udn.cron

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('module', type=str)
        parser.add_argument('method', type=str)
        parser.add_argument('custargs', nargs='*', type=str)
    
    def handle(self, *args, **options):
        module = options['module']
        method = options['method']
        custargs = options['custargs']
        getattr(import_module(module).cron, method)(*custargs)
