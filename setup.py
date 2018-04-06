#!/usr/bin/env python3

import os.path
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="FakeSMTPd",
    version="0.2.0",
    description="SMTP server for testing mail functionality",
    long_description=read("README.md"),
    author="Sebastian Rittau",
    author_email="srittau@rittau.biz",
    url="https://github.com/srittau/fakesmtpd",
    packages=["fakesmtpd", "fakesmtpd_test"],
    scripts=[os.path.join("bin", "fakesmtpd")],
    tests_require=["asserts >= 0.6"],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications :: Email :: Mail Transport Agents",
        "Topic :: Software Development :: Testing",
    ],
)
