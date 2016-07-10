# -*- coding: utf-8 -*-
#
# szr/glob.py
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

registers = ['T', 'C', 'P a Nc', 'D', 'E', 'P', 'Nc', 'ERo', 'Ro', 'EC',
             'EVC', 'EXE', 'EPR', 'PP', 'Cm', 'Sm', 'Ca', 'Cad', 'Az', 'To',
             'Nt', 'Co', 'Ntd', 'Cmo', 'Ko', 'Nco', 'Ncd', 'Ncp', 'ECm',
             'ICm', 'INS', 'K', 'Kv', 'EVCm', 'A', 'Ad', 'Af', 'Na', 'UL',
             'Cdo', 'Odo', 'Tdo', 'Tz' , 'Ncu', 'Ads', 'Afs', 'Ans', 'Ao',
             'Aos', 'Aprk', 'Aprn', 'Aps', 'Ars', 'As', 'Asz', 'Azs', 'Komp',
             'Konf', 'Kse', 'Kseo', 'Kss', 'Ksz', 'Na', 'Nad', 'Nao', 'Ncn',
             'Nk', 'Ntn', 'Obn', 'Plen', 'Plsn', 'Pst', 'Rozk', 'Rs', 'S',
             'Spr', 'Sst', 'Vol']
registers_regex = '^(' + ('|'.join(registers)) + ')$'
supreme_court = 'NSJIMBM'
supreme_administrative_court = 'NSS'
