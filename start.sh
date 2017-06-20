#!/bin/sh

set -e

exec /app/virtualenv/bin/fakesmtpd -b 0.0.0.0 | tee /app/log/fakesmtpd
