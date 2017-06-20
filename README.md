# FakeSMTPd

[![Build Status](https://travis-ci.org/srittau/FakeSMTPd.svg?branch=master)](https://travis-ci.org/srittau/FakeSMTPd)

FakeSMTPd is an SMTP server for testing mail functionality. Any mail sent via
this server will be printed to stdout, but will not be forwarded any further.

Usage
-----

`fakesmtpd [OPTIONS]`

Supported options:

  * `-b, --bind [ADDRESS]` IP addresses to listen on, defaults to 127.0.0.1
  * `-p, --port [PORT]` SMTP port to listen on
