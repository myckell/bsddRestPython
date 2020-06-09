# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='bsddRestPython',
    version='0.1.0',
    description='requesting data from buildingSMART-Data-Dictionary with Python',
    long_description=readme,
    author='Michael Zibell',
    author_email='m.zibell@icloud.com',
    url='https://github.com/myckell/bsddRestPython',
    license=license,
    packages=find_packages(exclude=('docs'))
)
