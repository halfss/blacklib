#!/usr/bin/env python

from setuptools import setup,find_packages

setup(
    name="ops",
    version='0.1',
    description="ops lib",
    author="halfss",
    install_requires=[
        "SQLAlchemy",
        "MySQL-python",
        "tornado",
        "eventlet",
        "redis",
        "requests",
        "netaddr"
    ],

    scripts=[
        "bin/ops_salt",
        "bin/ops_api",
    ],

    packages=find_packages(),
    data_files=[
        ('/etc/ops',['etc/ops.conf']),
        ('/var/log/ops',[]),
    ],
)
