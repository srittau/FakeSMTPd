import asyncio
import logging

from fakesmtpd.connection import handle_connection

SMTP_PORT = 25


logging.basicConfig(level=logging.INFO)


def main() -> None:
    loop = asyncio.get_event_loop()
    s = asyncio.start_server(handle_connection, port=SMTP_PORT)
    loop.run_until_complete(s)
    loop.run_forever()
