import codecs
import datetime
import logging
from asyncio.streams import StreamReader, StreamWriter
from socket import getfqdn
from typing import Tuple, Callable

from fakesmtpd.commands import handle_command
from fakesmtpd.smtp import SMTPStatus
from fakesmtpd.state import State


class UnexpectedEOFError(Exception):

    pass


def replace_by_7_bit(error: UnicodeError) -> Tuple[str, int]:
    if isinstance(error, UnicodeDecodeError):
        b = error.object[error.start:error.end]
        c = chr(ord(b) & 0x7f)
        return c, error.end
    else:
        raise NotImplementedError()


codecs.register_error("7bit", replace_by_7_bit)


class ConnectionHandler:
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 print_mail: Callable[[State], None]) -> None:
        self.reader = reader
        self.writer = writer
        self.print_mail = print_mail
        self.state = State()

    async def handle(self) -> None:
        logging.info("connection opened")
        self._write_reply(SMTPStatus.SERVICE_READY,
                          "{} FakeSMTPd Service ready".format(getfqdn()))
        while not self.reader.at_eof():
            line = await self.reader.readline()
            try:
                decoded = line.decode("ascii").rstrip()
            except UnicodeDecodeError:
                self._write_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                  "Unexpected 8 bit character")
                continue
            code = self._handle_line(decoded)
            if code == SMTPStatus.START_MAIL_INPUT:
                await self._handle_mail_text()
            elif code == SMTPStatus.SERVICE_CLOSING:
                break
        self.writer.close()
        logging.info("connection closed")

    def _parse_line(self, line: str) -> Tuple[str, str]:
        command = line[:4].upper()
        return command, line[5:]

    def _handle_line(self, line: str) -> SMTPStatus:
        logging.debug(f"received command: {line}")
        command, arguments = self._parse_line(line)
        code, text = handle_command(self.state, command, arguments)
        logging.debug(f"sending response: {code} {text}")
        self._write_reply(code, text)
        return code

    async def _handle_mail_text(self) -> None:
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
            self.state.add_line(line.decode("ascii", "7bit"))
        raise UnexpectedEOFError()

    def _write_reply(self, code: SMTPStatus, text: str) -> None:
        full_line = f"{code.value} {text}\r\n"
        self.writer.write(full_line.encode("ascii"))
