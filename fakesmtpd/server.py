from __future__ import annotations

import asyncio
import logging
import signal
import sys
from asyncio.streams import StreamReader, StreamWriter
from collections.abc import Awaitable, Callable
from functools import partial
from typing import Optional

from fakesmtpd.args import parse_args
from fakesmtpd.connection import ConnectionHandler
from fakesmtpd.mbox import print_mbox_mail
from fakesmtpd.state import State


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    printer = partial(print_mbox_mail, args.output_filename)
    try:
        run_server(args.bind, args.port, partial(handle_connection, printer))
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


_ServerHandler = Callable[
    [StreamReader, StreamWriter], Optional[Awaitable[None]]
]


def run_server(host: str, port: int, handler: _ServerHandler) -> None:
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    s = asyncio.start_server(handler, host=host, port=port)
    loop.run_until_complete(s)
    loop.run_forever()


async def handle_connection(
    printer: Callable[[State], None],
    reader: StreamReader,
    writer: StreamWriter,
) -> None:
    await ConnectionHandler(reader, writer, printer).handle()
