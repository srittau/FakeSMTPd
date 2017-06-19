import asyncio
import logging
import signal

from fakesmtpd.connection import handle_connection

SMTP_PORT = 25


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    s = asyncio.start_server(handle_connection, port=SMTP_PORT)
    loop.run_until_complete(s)
    loop.run_forever()
