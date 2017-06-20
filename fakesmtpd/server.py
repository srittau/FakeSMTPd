import asyncio
import logging
import signal
import sys

from fakesmtpd.args import parse_args
from fakesmtpd.connection import handle_connection


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args(sys.argv)
    try:
        run_server(args.port)
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def run_server(port: int) -> None:
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    s = asyncio.start_server(handle_connection, port=port)
    loop.run_until_complete(s)
    loop.run_forever()
