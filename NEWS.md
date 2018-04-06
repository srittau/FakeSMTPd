Changes in FakeSMTPd 0.2.0
==========================

Improvements
------------

* Reject invalid `HELO`, `EHLO`, `MAIL`, and `RCPT` commands.

Changes in FakeSMTPd 0.1.1
==========================

Bug fixes
---------

* Do not throw an exception when encountering 8 bit characters. Instead
  return an error (in commands) or drop the most significant bit (in mail
  texts).
