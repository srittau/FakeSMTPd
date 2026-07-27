# Changelog for FakeSMTPd

## Unreleased

## 2026.7.0 – 2026-07-27

### Added

- Add support for Python 3.15.

### Fixed

- Fixed running the server with Python 3.14 or above.

## 2025.10.0 – 2025-10-23

### Added

- Add support for Python 3.11 through 3.14.

### Removed

- Drop support for Python 3.7 through 3.9.

## 2022.10.1 – 2022-10-23

Switch to calendar-based versioning.

### Added

- Officially support Python 3.9 and 3.10.

### Removed

- Drop support for Python 3.6.

## 1.0.0 – 2020-04-08

No changes.

## 0.2.1 – 2018-04-06

### Changed

- Ensure that lines end with \r\n.

### Fixed

- Log exceptions raised during a connection, instead of aborting.

## 0.2.0 – 2018-04-06

### Changed

- Reject invalid `HELO`, `EHLO`, `MAIL`, and `RCPT` commands.
- Enforce limits per RFC 5321, section 4.5.3.1.

## 0.1.1 – 2017-06-20

### Fixed

- Do not throw an exception when encountering 8 bit characters. Instead
  return an error (in commands) or drop the most significant bit (in mail
  texts).

## 0.1.0 – 2017-06-20

- First release
