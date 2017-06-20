import datetime
from asyncio.streams import StreamReader, StreamWriter
import logging
from socket import getfqdn
from typing import Tuple, Callable

from fakesmtpd.commands import handle_command
from fakesmtpd.smtp import SMTPStatus
from fakesmtpd.state import State


class UnexpectedEOFError(Exception):

    pass


class ConnectionHandler:

    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 print_mail: Callable[[State], None]) -> None:
        self.reader = reader
        self.writer = writer
        self.print_mail = print_mail
        self.state = State()

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
            code, text = handle_command(self.state, command, arguments)
            logging.debug(f"sending response: {code} {text}")
            self._write_reply(code, text)
            if code == SMTPStatus.SERVICE_CLOSING:
                break
            elif code == SMTPStatus.START_MAIL_INPUT:
                await self._handle_mail_text()
        self.writer.close()
        logging.info("connection closed")

    def _parse_line(self, line: str) -> Tuple[str, str]:
        command = line[:4].upper()
        return command, line[5:]

    async def _handle_mail_text(self):
        try:
            await self._read_mail_text()
        except UnexpectedEOFError:
            pass
        else:
            self._write_reply(SMTPStatus.OK, "OK")
            self.state.date = datetime.datetime.utcnow()
            state = self.state
            self.print_mail(state)
            self.state = State()
            self.state.greeted = state.greeted

    async def _read_mail_text(self) -> None:
        while not self.reader.at_eof():
            line = await self.reader.readline()
            if line == b".\r\n":
                return
            self.state.add_line(line.decode("ascii"))
        raise UnexpectedEOFError()

    def _write_reply(self, code: SMTPStatus, text: str) -> None:
        full_line = f"{code.value} {text}\r\n"
        self.writer.write(full_line.encode("ascii"))
