Changes in FakeSMTPd 0.2.1
==========================

Improvements
------------

* Ensure that lines end with \r\n.

Bug fixes
---------

* Log exceptions raised during a connection, instead of aborting.

Changes in FakeSMTPd 0.2.0
==========================

Improvements
------------

* Reject invalid `HELO`, `EHLO`, `MAIL`, and `RCPT` commands.
* Enforce limits per RFC 5321, section 4.5.3.1.

Changes in FakeSMTPd 0.1.1
==========================

Bug fixes
---------

* Do not throw an exception when encountering 8 bit characters. Instead
  return an error (in commands) or drop the most significant bit (in mail
  texts).
