import asyncio
from asyncio.streams import StreamReader, StreamWriter
import logging
import signal
import sys
from typing import Optional

from functools import partial

from fakesmtpd.args import parse_args
from fakesmtpd.connection import ConnectionHandler
from fakesmtpd.mbox import print_mbox_mail


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args(sys.argv)
    try:
        run_server(args.bind, args.port)
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def run_server(host: Optional[str], port: int) -> None:
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    s = asyncio.start_server(handle_connection, host=host, port=port)
    loop.run_until_complete(s)
    loop.run_forever()


async def handle_connection(reader: StreamReader, writer: StreamWriter) \
        -> None:
    print_it = partial(print_mbox_mail, sys.stdout)
    await ConnectionHandler(reader, writer, print_it).handle()
