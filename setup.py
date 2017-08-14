#! /usr/bin/env python

# -*- coding: utf-8 -*-

from distutils.core import setup


APPS = [
    'common', 'sop', 'lht', 'cin', 'dvt', 'cnb', 'knr', 'hjp', 'hsp', 'szr', 'sur', 'psj', 'udn', 'sir', 'dir',
    'pir', 'kos', 'cache']

FULL_APPS = ['legal.{}'.format(p) for p in APPS]

package_data = {f: ['templates/*.html', 'static/*.scss', 'static/*.js', 'static/*.dtd', 'static/*.xsd'] for f in FULL_APPS}

setup(
    name='legal',
    version='1.0',
    description='Tools for Czech Lawyers',
    author='Tomáš Pecina',
    author_email='tomas@pecina.cz',
    url='https://legal.pecina.cz/',
    packages=['legal'] + FULL_APPS,
    package_data=package_data,
    data_files=[
        ('legal', [
            'README',
            'LICENSE']),
        ('fonts', [
            'fonts/URWBookman-BoldItalic.ttf',
            'fonts/URWBookman-Bold.ttf',
            'fonts/URWBookman-Italic.ttf',
            'fonts/URWBookman-Regular.ttf']),
    ],
)
