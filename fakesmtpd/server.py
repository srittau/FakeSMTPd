import argparse
import asyncio
import logging
import signal
import sys
from typing import List

from fakesmtpd.connection import handle_connection

SMTP_PORT = 25


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    port = parse_args(sys.argv)
    try:
        run_server(port)
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def parse_args(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="SMTP server for testing mail functionality")
    parser.add_argument(
        "--port", "-p", type=int, nargs="?", default=SMTP_PORT,
        help="SMTP port to listen on")
    args = parser.parse_args()
    return args.port


def run_server(port: int) -> None:
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    s = asyncio.start_server(handle_connection, port=port)
    loop.run_until_complete(s)
    loop.run_forever()
