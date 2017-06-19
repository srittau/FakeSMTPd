import asyncio
from typing import List
from unittest.case import TestCase
from unittest.mock import patch

from asserts import assert_equal, assert_greater_equal, fail

from fakesmtpd.connection import handle_connection
from fakesmtpd.smtp import SMTPStatus

FAKE_HOST = "mail.example.com"


class FakeStreamReader:

    def __init__(self):
        self.lines: List[str] = []

    # SUT Interface

    async def readline(self) -> bytes:
        if not self.lines:
            return b""
        line = self.lines[0].encode("ascii") + b"\r\n"
        self.lines = self.lines[1:]
        return line

    def at_eof(self) -> bool:
        return not self.lines

    def close(self) -> None:
        pass

    # Test Interface


class FakeStreamWriter:

    def __init__(self) -> None:
        self.open = True
        self.data = b""

    # SUT Interface

    def write(self, data: bytes) -> None:
        self.data += data

    def close(self) -> None:
        self.open = False

    # Test Interface

    def assert_is_closed(self) -> None:
        if self.open:
            fail("writer unexpectedly still open")

    @property
    def lines(self):
        return self.data.decode("ascii").splitlines()

    def assert_last_line_equal(self, line: str) -> None:
        assert_greater_equal(len(self.lines), 1, "no response")
        assert_equal(line, self.lines[-1])

    def assert_last_reply(self, code: SMTPStatus, text: str):
        expected_line = f"{code.value} {text}"
        self.assert_last_line_equal(expected_line)


class ConnectionHandlerTest(TestCase):

    def setUp(self):
        self.reader = FakeStreamReader()
        self.writer = FakeStreamWriter()
        self._getfqdn_patch1 = \
            patch("fakesmtpd.connection.getfqdn", lambda: FAKE_HOST)
        self._getfqdn_patch2 = \
            patch("fakesmtpd.commands.getfqdn", lambda: FAKE_HOST)
        self._getfqdn_patch1.start()
        self._getfqdn_patch2.start()

    def tearDown(self):
        self._getfqdn_patch1.stop()
        self._getfqdn_patch2.stop()

    def _handle(self):
        loop = asyncio.get_event_loop()
        c = handle_connection(self.reader, self.writer)
        loop.run_until_complete(c)

    def test_greeting(self):
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_READY,
            "{} FakeSMTPd Service ready".format(FAKE_HOST))

    def test_invalid_line(self):
        self.reader.lines = ["ab"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.COMMAND_UNRECOGNIZED, "Command unrecognized")

    def test_unrecognized_command(self):
        self.reader.lines = ["XUNK "]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.COMMAND_UNRECOGNIZED, "Command unrecognized")

    def test_noop(self):
        self.reader.lines = ["NOOP"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__any_case(self):
        self.reader.lines = ["NoOp"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_space(self):
        self.reader.lines = ["NOOP "]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_arguments(self):
        self.reader.lines = ["NOOP foo bar"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_quit(self):
        self.reader.lines = ["QUIT"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel")
        self.writer.assert_is_closed()

    def test_quit_with_arguments(self):
        self.reader.lines = ["QUIT foo"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments")
        self.writer.assert_is_closed()

    def test_quit__without_closing_channel(self):
        self.reader.lines = ["QUIT", "NOOP"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel")
        self.writer.assert_is_closed()

    def test_helo(self):
        self.reader.lines = ["HELO client.example.com"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.OK, f"{FAKE_HOST} Hello client.example.com")

    def test_helo__no_domain(self):
        self.reader.lines = ["HELO "]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments")

    def test_ehlo(self):
        self.reader.lines = ["EHLO client.example.com"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.OK, f"{FAKE_HOST} Hello client.example.com")

    def test_ehlo__no_domain(self):
        self.reader.lines = ["EHLO "]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments")
