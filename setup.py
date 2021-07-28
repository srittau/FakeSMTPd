#!/usr/bin/env python3

import os.path
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="FakeSMTPd",
    version="2021.7.1",
    description="SMTP server for testing mail functionality",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Sebastian Rittau",
    author_email="srittau@rittau.biz",
    url="https://github.com/srittau/fakesmtpd",
    packages=["fakesmtpd", "fakesmtpd_test"],
    scripts=[os.path.join("bin", "fakesmtpd")],
    tests_require=["asserts >= 0.6, < 0.12"],
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Communications :: Email :: Mail Transport Agents",
        "Topic :: Software Development :: Testing",
    ],
)
