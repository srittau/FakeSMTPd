# FakeSMTPd

[![License](https://img.shields.io/pypi/l/FakeSMTPd.svg)](https://pypi.python.org/pypi/FakeSMTPd/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fakesmtpd)
[![GitHub Release](https://img.shields.io/github/release/srittau/fakesmtpd/all.svg)](https://github.com/srittau/FakeSMTPd/releases/)
[![pypi Release](https://img.shields.io/pypi/v/FakeSMTPd.svg)](https://pypi.python.org/pypi/FakeSMTPd/)
[![Build Status](https://travis-ci.org/srittau/FakeSMTPd.svg?branch=master)](https://travis-ci.org/srittau/FakeSMTPd)

FakeSMTPd is an SMTP server for testing mail functionality. Any mail sent via
this server will be saved, but will not be forwarded any further.

Mail is printed to stdout by default in default mbox format, as defined in
[RFC 4155](https://www.ietf.org/rfc/rfc4155.txt). The SMTP mail receivers
are added in X-FakeSMTPd-Receiver headers.

Usage
-----

`fakesmtpd [OPTIONS]`

Supported options:

  * `-o`, `--output-filename [FILENAME]` mbox file for output, default: stdout
  * `-b`, `--bind [ADDRESS]` IP addresses to listen on, default: 127.0.0.1
  * `-p`, `--port [PORT]` SMTP port to listen on

Docker image [available](https://hub.docker.com/r/srittau/fakesmtpd/).
