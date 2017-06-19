from asyncio.streams import StreamReader, StreamWriter
import logging
from socket import getfqdn
from typing import Tuple

from fakesmtpd.commands import handle_command
from fakesmtpd.smtp import SMTPStatus


class ConnectionHandler:

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def handle(self) -> None:
        logging.info("connection opened")
        self._write_reply(
            SMTPStatus.SERVICE_READY,
            "{} FakeSMTPd Service ready".format(getfqdn()))
        while not self.reader.at_eof():
            line = await self.reader.readline()
            decoded = line.decode("ascii").rstrip()
            logging.debug(f"received command: {decoded}")
            command, arguments = self._parse_line(decoded)
            code, text = handle_command(command, arguments)
            logging.debug(f"sending response: {code} {text}")
            self._write_reply(code, text)
            if code == SMTPStatus.SERVICE_CLOSING:
                break
        self.writer.close()
        logging.info("connection closed")

    def _parse_line(self, line: str) -> Tuple[str, str]:
        command = line[:4].upper()
        return command, line[5:]

    def _write_reply(self, code: SMTPStatus, text: str) -> None:
        full_line = f"{code.value} {text}\r\n"
        self.writer.write(full_line.encode("ascii"))


async def handle_connection(reader: StreamReader, writer: StreamWriter) \
        -> None:
    await ConnectionHandler(reader, writer).handle()
