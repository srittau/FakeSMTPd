# FakeSMTPd

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
