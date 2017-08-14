# -*- coding: utf-8 -*-
#
# knr/presets.py
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

PS_PLACES = (
    ('US', 'Ústavní soud',
     'Joštova 625/8, 602 00 Brno, Česko',
     49.1975999, 16.6044449),
    ('NS', 'Nejvyšší soud ČR',
     'Burešova 571/20, 602 00 Brno, Česko',
     49.2051937, 16.6022015),
    ('NSS', 'Nejvyšší správní soud',
     'Moravské nám. 611/6, 602 00 Brno, Česko',
     49.1974319, 16.6068056),
    ('VS-P', 'Vrchní soud v Praze',
     'nám. Hrdinů 1300/11, 140 00 Praha 4, Česko',
     50.0577151, 14.4371596),
    ('VS-O', 'Vrchní soud v Olomouci',
     'Masarykova tř. 609/1, 779 00 Olomouc, Česko',
     49.5958761, 17.2668042),
    ('MS-P', 'Městský soud v Praze',
     'Spálená 6/2, 120 00 Praha 2, Česko',
     50.0788207, 14.4195592),
    ('OS-P1', 'Obvodní soud pro Prahu 1',
     'Ovocný trh 587/14, 110 00 Praha 1, Česko',
     50.0868809, 14.4258119),
    ('OS-P2', 'Obvodní soud pro Prahu 2',
     'Francouzská 808/19, 120 00 Praha 2, Česko',
     50.0735248, 14.4409348),
    ('OS-P3', 'Obvodní soud pro Prahu 3',
     'Jagellonská 1734/5, 130 00 Praha 3, Česko',
     50.0794811, 14.4524109),
    ('OS-P4', 'Obvodní soud pro Prahu 4',
     '28. pluku 1533/29b, 100 00 Praha 10, Česko',
     50.0721831, 14.4649207),
    ('OS-P5', 'Obvodní soud pro Prahu 5',
     'Legerova 1877/7, 120 00 Praha 2, Česko',
     50.0702271, 14.4282708),
    ('OS-P6', 'Obvodní soud pro Prahu 6',
     '28. pluku 1533/29b, 100 00 Praha 10, Česko',
     50.0721831, 14.4649207),
    ('OS-P7', 'Obvodní soud pro Prahu 7',
     'Ovocný trh 587/14, 110 00 Praha 1, Česko',
     50.0868809, 14.4258119),
    ('OS-P8', 'Obvodní soud pro Prahu 8',
     '28. pluku 1533/29b, 100 00 Praha 10, Česko',
     50.0721831, 14.4649207),
    ('OS-P9', 'Obvodní soud pro Prahu 9',
     '28. pluku 1533/29b, 100 00 Praha 10, Česko',
     50.0721831, 14.4649207),
    ('OS-P10', 'Obvodní soud pro Prahu 10',
     '28. pluku 1533/29b, 100 00 Praha 10, Česko',
     50.0721831, 14.4649207),
    ('KS-P', 'Krajský soud v Praze',
     'Náměstí Kinských 234/5, 150 00 Praha 5-Smíchov, Česko',
     50.0788991, 14.4050324),
    ('OS-PY', 'Okresní soud Praha-východ',
     'Na poříčí 20, 110 00 Praha 1, Česko',
     50.0898654, 14.4335763),
    ('OS-PZ', 'Okresní soud Praha-západ',
     'Karmelitská 377/19, 118 00 Praha 1, Česko',
     50.0865039, 14.4037926),
    ('OS-BN', 'Okresní soud v Benešově',
     'Masarykovo nám. 223, 256 01 Benešov, Česko',
     49.7827177, 14.6901729),
    ('OS-BE', 'Okresní soud v Berouně',
     'Wagnerovo nám. 1249/3, 266 01 Beroun, Česko',
     49.9654347, 14.069906),
    ('OS-KL', 'Okresní soud v Kladně',
     'nám. Edvarda Beneše 1997, 272 01 Kladno, Česko',
     50.1427187, 14.0961442),
    ('OS-KO', 'Okresní soud v Kolíně',
     'Kmochova 144, 280 02 Kolín, Česko',
     50.0264444, 15.1988467),
    ('OS-KH', 'Okresní soud v Kutné Hoře',
     'náměstí Národního odboje 58/6, 284 01 Kutná Hora, Česko',
     49.9479468, 15.2627764),
    ('OS-ME', 'Okresní soud v Mělníku',
     'Krombholcova, 276 01 Mělník, Česko',
     50.3496114, 14.4837625),
    ('OS-MB', 'Okresní soud v Mladé Boleslavi',
     'nám. Republiky 10, 293 01 Mladá Boleslav, Česko',
     50.4112661, 14.9149387),
    ('OS-NB', 'Okresní soud v Nymburce',
     'Soudní 996/10, 288 02 Nymburk, Česko',
     50.1853843, 15.0434616),
    ('OS-PB', 'Okresní soud v Příbrami',
     'Milínská 167, 261 01 Příbram, Česko',
     49.6867282, 14.0096433),
    ('OS-RA', 'Okresní soud v Rakovníku',
     'Sixtovo nám. 76, 269 01 Rakovník, Česko',
     50.1058046, 13.7242744),
    ('KS-CB', 'Krajský soud v Českých Budějovicích',
     'Zátkovo nábř. 10/2, 370 07 České Budějovice, Česko',
     48.9713874, 14.4740319),
    ('OS-CB', 'Okresní soud v Českých Budějovicích',
     'Lidická tř. 98/20, 370 01 České Budějovice, Česko',
     48.9668957, 14.4746671),
    ('OS-CK', 'Okresní soud v Českém Krumlově',
     'Linecká 284, 381 01 Český Krumlov, Česko',
     48.8081871, 14.3172228),
    ('OS-JH', 'Okresní soud v Jindřichově Hradci',
     'Klášterská 123/II, 377 01 Jindřichův Hradec, Česko',
     49.1482805, 15.0008156),
    ('OS-PE', 'Okresní soud v Pelhřimově',
     'tř. Legií 876, 393 01 Pelhřimov, Česko',
     49.4288899, 15.2209146),
    ('OS-PI', 'Okresní soud v Písku',
     'Velké nám. 121/17, 397 01 Písek, Česko',
     49.308018, 14.1468606),
    ('OS-PT', 'Okresní soud v Prachaticích',
     'Pivovarská 3, 383 01 Prachatice, Česko',
     49.0144219, 13.9984651),
    ('OS-ST', 'Okresní soud ve Strakonicích',
     'Smetanova 455, 386 01 Strakonice, Česko',
     49.2663581, 13.9047092),
    ('OS-TA', 'Okresní soud v Táboře',
     'nám. Mikuláše z Husi 43/4, 390 01 Tábor, Česko',
     49.4138739, 14.6548034),
    ('KS-PM', 'Krajský soud v Plzni',
     'Veleslavínova 21/40, 301 00 Plzeň, Česko',
     49.7491176, 13.3765335),
    ('OS-PM', 'Okresní soud Plzeň-město',
     'Veleslavínova 21/40, 301 00 Plzeň, Česko',
     49.7491176, 13.3765335),
    ('OS-PJ', 'Okresní soud Plzeň-jih',
     'Sady 5. května 2396/11, 301 00 Plzeň, Česko',
     49.7504426, 13.377753),
    ('OS-PS', 'Okresní soud Plzeň-sever',
     'Edvarda Beneše 1127/1, 320 00 Plzeň, Česko',
     49.7367405, 13.372298),
    ('OS-DO', 'Okresní soud v Domažlicích',
     'Paroubkova 228, 344 01 Domažlice, Česko',
     49.4453454, 12.9255328),
    ('OS-CH', 'Okresní soud v Chebu',
     'Lidická 1066/1, 350 02 Cheb, Česko',
     50.0729478, 12.3660544),
    ('OS-KV', 'Okresní soud v Karlových Varech',
     'Moskevská 1163/17, 360 01 Karlovy Vary, Česko',
     50.2284624, 12.8671638),
    ('OS-KT', 'Okresní soud v Klatovech',
     'Dukelská 138, 339 01 Klatovy, Česko',
     49.4010289, 13.2868676),
    ('OS-RO', 'Okresní soud v Rokycanech',
     'Jiráskova 67, 337 01 Rokycany, Česko',
     49.7406085, 13.5950782),
    ('OS-SO', 'Okresní soud v Sokolově',
     'K. H. Borovského 57, 356 01 Sokolov, Česko',
     50.1796893, 12.6462417),
    ('OS-TC', 'Okresní soud v Tachově',
     'nám. Republiky 71, 347 01 Tachov, Česko',
     49.795848, 12.6335028),
    ('KS-UL', 'Krajský soud v Ústí nad Labem',
     'Národního odboje 1274/26, 400 03 Ústí nad Labem, Česko',
     50.658658, 14.0490253),
    ('OS-UL', 'Okresní soud v Ústí nad Labem',
     'Kramoly 641/37, 400 03 Ústí nad Labem, Česko',
     50.6585721, 14.0501592),
    ('OS-CL', 'Okresní soud v České Lípě',
     'Děčínská 389/4, 470 06 Česká Lípa, Česko',
     50.6870543, 14.5303395),
    ('OS-DC', 'Okresní soud v Děčíně',
     'Masarykovo nám. 1/1, 405 02 Děčín, Česko',
     50.7800854, 14.2124466),
    ('OS-CV', 'Okresní soud v Chomutově',
     'Partyzánská 427, 430 01 Chomutov, Česko',
     50.4610816, 13.4227718),
    ('OS-JN', 'Okresní soud v Jablonci nad Niso',
     'Mírové nám. 5, 466 01 Jablonec nad Nisou, Česko',
     50.7246373, 15.1707567),
    ('OS-LB', 'Okresní soud v Liberci',
     'U soudu 3, 460 01 Liberec, Česko',
     50.7703119, 15.0489964),
    ('OS-LT', 'Okresní soud v Litoměřicích',
     'Na Valech 525/12, 412 01 Litoměřice, Česko',
     50.5355807, 14.1357596),
    ('OS-LN', 'Okresní soud v Lounech',
     'Mírové nám. 1, 440 01 Louny, Česko',
     50.357333, 13.7981718),
    ('OS-MO', 'Okresní soud v Mostě',
     'Moskevská 2, 434 01 Most, Česko',
     50.5053369, 13.6536194),
    ('OS-TP', 'Okresní soud v Teplicích',
     'U soudu 1450, 415 01 Teplice, Česko',
     50.6371636, 13.8193634),
    ('KS-HK', 'Krajský soud v Hradci Králové',
     'Československé armády 218/57, 500 02 Hradec Králové, Česko',
     50.2105378, 15.8390654),
    ('OS-HK', 'Okresní soud v Hradci Králové',
     'Ignáta Herrmanna 227/2, 500 02 Hradec Králové, Česko',
     50.2074197, 15.8315334),
    ('OS-HB', 'Okresní soud v Havlíčkově Brodě',
     'Husova, 580 01 Havlíčkův Brod, Česko',
     49.6096803, 15.5731501),
    ('OS-CR', 'Okresní soud v Chrudimi',
     'Všehrdovo nám. 45, 537 01 Chrudim, Česko',
     49.9522212, 15.7955363),
    ('OS-JC', 'Okresní soud v Jičíně',
     'Šafaříkova 842, 506 01 Jičín, Česko',
     50.4349893, 15.3548238),
    ('OS-NA', 'Okresní soud v Náchodě',
     'Palachova 1303, 547 01 Náchod, Česko',
     50.4141979, 16.1651597),
    ('OS-PU', 'Okresní soud v Pardubicích',
     'Na Třísle, 530 02 Pardubice, Česko',
     50.0391395, 15.7811342),
    ('OS-RK', 'Okresní soud v Rychnově nad Kněžnou',
     'Svatohavelská 93, 516 01 Rychnov nad Kněžnou, Česko',
     50.1646411, 16.2745213),
    ('OS-SM', 'Okresní soud v Semilech',
     'Nádražní 25, 513 01 Semily, Česko',
     50.601197, 15.3261877),
    ('OS-SY', 'Okresní soud ve Svitavách',
     'Dimitrovova 679/33, 568 02 Svitavy, Česko',
     49.7536882, 16.4611924),
    ('OS-TU', 'Okresní soud v Trutnově',
     'Nádražní 106, 541 01 Trutnov, Česko',
     50.5642875, 15.9099397),
    ('OS-UO', 'Okresní soud v Ústí nad Orlicí',
     'Husova 975, 562 01 Ústí nad Orlicí, Česko',
     49.9744658, 16.3913088),
    ('KS-B', 'Krajský soud v Brně',
     'Rooseveltova 648/16, 602 00 Brno, Česko',
     49.1967243, 16.6119663),
    ('MS-B', 'Městský soud v Brně',
     'Polní 994/39, 639 00 Brno, Česko',
     49.182955, 16.6002415),
    ('OS-BO', 'Okresní soud Brno-venkov',
     'Polní 994/39, 639 00 Brno, Česko',
     49.182955, 16.6002415),
    ('OS-BL', 'Okresní soud v Blansku',
     'Hybešova 2047/5, 678 01 Blansko, Česko',
     49.3586559, 16.64796),
    ('OS-BV', 'Okresní soud v Břeclavi',
     'Národních hrdinů 17/11, 690 02 Břeclav, Česko',
     48.7612437, 16.8817585),
    ('OS-HO', 'Okresní soud v Hodoníně',
     'Velkomoravská 2269/4, 695 01 Hodonín, Česko',
     48.8513298, 17.1246175),
    ('OS-JI', 'Okresní soud v Jihlavě',
     'Legionářů 5277/9a, 586 01 Jihlava, Česko',
     49.401119, 15.5823214),
    ('OS-KM', 'Okresní soud v Kroměříži',
     'Soudní 1279/11, 767 01 Kroměříž, Česko',
     49.2963069, 17.3858637),
    ('OS-PV', 'Okresní soud v Prostějově',
     'Havlíčkova 2936/16, 796 01 Prostějov, Česko',
     49.4756337, 17.1142131),
    ('OS-TR', 'Okresní soud v Třebíči',
     'Bráfova tř. 502/57, 674 01 Třebíč, Česko',
     49.2120408, 15.8883249),
    ('OS-UH', 'Okresní soud v Uherském Hradišti',
     'Svatováclavská 568, 686 01 Uherské Hradiště, Česko',
     49.0660404, 17.4614185),
    ('OS-VY', 'Okresní soud ve Vyškově',
     'Kašíkova 314/28, 682 01 Vyškov, Česko',
     49.2764243, 16.9927397),
    ('OS-ZL', 'Okresní soud ve Zlíně',
     'Soudní 3, 760 01 Zlín, Česko',
     49.2263899, 17.6644193),
    ('OS-ZN', 'Okresní soud ve Znojmě',
     'nám. Republiky 585/1, 669 02 Znojmo, Česko',
     48.8525877, 16.0518005),
    ('OS-ZR', 'Okresní soud ve Žďáru nad Sázavou',
     'Strojírenská 2210/28, 591 01 Žďár nad Sázavou, Česko',
     49.557696, 15.9372312),
    ('KS-O', 'Krajský soud v Ostravě',
     'Havlíčkovo nábř. 1835/34, 702 00 Ostrava, Česko',
     49.8386855, 18.2941287),
    ('OS-OT', 'Okresní soud v Ostravě',
     'U soudu 6187/4, 708 00 Ostrava, Česko',
     49.8264103, 18.1872699),
    ('OS-BR', 'Okresní soud v Bruntále',
     'Partyzánská 1453/11, 792 01 Bruntál, Česko',
     49.9877683, 17.4671728),
    ('OS-FM', 'Okresní soud ve Frýdku-Místk',
     'Na Poříčí 3206, 738 01 Frýdek-Místek, Česko',
     49.6792216, 18.3487804),
    ('OS-JE', 'Okresní soud v Jeseníku',
     'Dukelská 761/2a, 790 01 Jeseník, Česko',
     50.2259305, 17.2038333),
    ('OS-KA', 'Okresní soud v Karviné',
     'park Bedřicha Smetany 176/5, 733 01 Karviná, Česko',
     49.8520098, 18.546543),
    ('OS-NJ', 'Okresní soud v Novém Jičíně',
     'Tyršova 1010/3, 741 01 Nový Jičín, Česko',
     49.5926243, 18.0096585),
    ('OS-OL', 'Okresní soud v Olomouci',
     'tř. Svobody 685/16, 779 00 Olomouc, Česko',
     49.5923178, 17.248863),
    ('OS-OP', 'Okresní soud v Opavě',
     'Olomoucká 297/27, 746 01 Opava, Česko',
     49.9384931, 17.8930096),
    ('OS-PR', 'Okresní soud v Přerově',
     'Smetanova 2016/2, 750 02 Přerov, Česko',
     49.4501867, 17.4504758),
    ('OS-SU', 'Okresní soud v Šumperk',
     'Milana Rastislava Štefánika 784/12, 787 01 Šumperk, Česko',
     49.9635693, 16.9749035),
    ('OS-VS', 'Okresní soud ve Vsetíně',
     'Horní nám. 5, 755 01 Vsetín, Česko',
     49.3412346, 17.9984571),
    ('OS-KA-H', 'Okresní soud v Karviné, pobočka v Havířově',
     'Dlouhá tř. 1647/46A, 736 01 Havířov, Česko',
     49.7750691, 18.4527658),
    ('KS-B-Z', 'Krajský soud v Brně, pobočka ve Zlíně',
     'Dlouhé Díly 351, 763 02 Zlín, Česko',
     49.2126923, 17.6168836),
    ('KS-UL-L', 'Krajský soud v Ústí nad Labem, pobočka v Liberci',
     'U soudu 3, 460 01 Liberec, Česko',
     50.7703119, 15.0489964),
    ('KS-B-J', 'Krajský soud v Brně, pobočka v Jihlavě',
     'tř. Legionářů 5277/9a, 586 01 Jihlava, Česko',
     49.401119, 15.5845102),
    ('KS-CB-T', 'Krajský soud v Českých Budějovicích, pobočka v Táboře',
     'kapitána Jaroše, 390 03 Tábor, Česko',
     49.4192378, 14.6482676),
    ('KS-HK-PU', 'Krajský soud v Hradci Králové, pobočka v Pardubicích',
     'Sukova tř. 1556, 530 02 Pardubice, Česko',
     50.0388511, 15.7700938),
    ('KS-O-OL', 'Krajský soud v Ostravě, pobočka v Olomouci',
     'Masarykova tř. 609/1, 779 00 Olomouc, Česko',
     49.5958761, 17.2668042),
    ('OS-VS-VM', 'Okresní soud ve Vsetíně, pobočka ve Valašském Meziříčí',
     'Legií 1374, 757 01 Valašské Meziříčí, Česko',
     49.4692995, 17.9826684),
    ('OS-BR-KN', 'Okresní soud v Bruntále, pobočka v Krnově',
     'Revoluční 965/60, 794 01 Krnov, Česko',
     50.0883338, 17.6892831),
    ('KS-PM-KV', 'Krajský soud v Plzni, pobočka v Karlových Varech',
     'Moskevská 1163/17, 360 01 Karlovy Vary, Česko',
     50.2284624, 12.8671638),
)

PS_FORMULAS = (
    ('2016', 'Vyhláška č. 385/2015 Sb.', 3.80, (('BA95', 29.70), ('BA98', 33.00), ('NM', 29.50))),
    ('2015', 'Vyhláška č. 328/2014 Sb.', 3.70, (('BA95', 35.90), ('BA98', 38.30), ('NM', 36.10))),
    ('2014', 'Vyhláška č. 435/2013 Sb.', 3.70, (('BA95', 35.70), ('BA98', 37.90), ('NM', 36.00))),
    ('2013', 'Vyhláška č. 472/2012 Sb.', 3.60, (('BA95', 36.10), ('BA98', 38.60), ('NM', 36.50))),
    ('2012', 'Vyhláška č. 429/2011 Sb.', 3.70, (('BA95', 34.90), ('BA98', 36.80), ('NM', 34.70))),
    ('2011', 'Vyhláška č. 377/2010 Sb.', 3.70, (('BA91', 31.40), ('BA95', 31.60), ('BA98', 33.40), ('NM', 30.80))),
    ('2010', 'Vyhláška č. 462/2009 Sb.', 3.90, (('BA91', 28.50), ('BA95', 28.70), ('BA98', 30.70), ('NM', 27.20))),
    ('2009', 'Vyhláška č. 451/2008 Sb.', 3.90, (('BA91', 26.30), ('BA95', 26.80), ('BA98', 29.00), ('NM', 28.50))),
    ('2007', 'Vyhláška č. 577/2006 Sb.', 3.80, (('BA91', 27.90), ('BA95', 28.10), ('BA98', 31.10), ('NM', 28.10))),
    ('2008', 'Vyhláška č. 357/2007 Sb.', 4.10, (('BA91', 30.60), ('BA95', 30.90), ('BA98', 33.10), ('NM', 31.20))),
    ('2006', 'Vyhláška č. 496/2005 Sb.', 3.80, (('BA91', 30.10), ('BA95', 30.40), ('BA98', 34.40), ('NM', 29.50))),
    ('2005', 'Vyhláška č. 647/2004 Sb.', 3.80, (('BA91', 27.50), ('BA95', 27.40), ('BA98', 31.00), ('NM', 26.60))),
)