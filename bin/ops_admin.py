#-*- coding:utf-8 -*-
# python lib
import os
import sys

SETUP = """#!/usr/bin/env python

from setuptools import setup,find_packages

setup(
    name="%s",
    version='0.1',
    description="%s",
    install_requires=[
        "SQLAlchemy",
        "tornado",
        "redis",
    ],
    
    scripts=[
    ],

    packages=find_packages(),
    data_files=[
    ],
"""

def startapp():
    args = sys.argv
    if len(args) != 3:
        print "Usage: ops_admin startapp [appname]"
        return
    if os.path.isdir(args[2]):
        print "%s is exists." % args[2]
        return
    if args[1] == "startapp":
        for _dir in ['api/contrib', 'db', 'service']:
            os.makedirs(os.path.join(args[2], args[2], _dir))
        for _prodir in ['bin', 'etc']:
            os.makedirs(os.path.join(args[2], _dir))
    else:
        print "Usage: ops_admin startapp [appname]"
        return

def create_app(name):
    pass

if __name__ == '__main__':
    startapp()
