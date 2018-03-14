import asyncio
from asyncio.streams import StreamReader, StreamWriter
from typing import List, Optional, cast
from unittest import TestCase
from unittest.mock import patch

from asserts import assert_equal, assert_greater_equal, fail, \
    assert_is_not_none, assert_datetime_about_now_utc

from fakesmtpd.connection import ConnectionHandler
from fakesmtpd.smtp import SMTPStatus
from fakesmtpd.state import State

FAKE_HOST = "mail.example.com"


class FakeStreamReader:
    def __init__(self) -> None:
        self.lines: List[str] = []

    # SUT Interface

    async def readline(self) -> bytes:
        if not self.lines:
            return b""
        line = self.lines[0].encode("latin1") + b"\r\n"
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
    def lines(self) -> List[str]:
        return self.data.decode("ascii").splitlines()

    def assert_last_line_equal(self, line: str) -> None:
        assert_greater_equal(len(self.lines), 1, "no response")
        assert_equal(line, self.lines[-1])

    def assert_last_reply(self, code: SMTPStatus, text: str) -> None:
        expected_line = f"{code.value} {text}"
        self.assert_last_line_equal(expected_line)


class ConnectionHandlerTest(TestCase):
    def setUp(self) -> None:
        self.reader = FakeStreamReader()
        self.writer = FakeStreamWriter()
        self._getfqdn_patch1 = \
            patch("fakesmtpd.connection.getfqdn", lambda: FAKE_HOST)
        self._getfqdn_patch2 = \
            patch("fakesmtpd.commands.getfqdn", lambda: FAKE_HOST)
        self._getfqdn_patch1.start()
        self._getfqdn_patch2.start()
        self.printed_state: Optional[State] = None

    def tearDown(self) -> None:
        self._getfqdn_patch1.stop()
        self._getfqdn_patch2.stop()

    def _handle(self) -> None:
        loop = asyncio.get_event_loop()
        handler = ConnectionHandler(
            cast(StreamReader, self.reader), cast(StreamWriter, self.writer),
            self._print_mail)
        loop.run_until_complete(handler.handle())

    def _print_mail(self, state: State) -> None:
        self.printed_state = state

    def test_greeting(self) -> None:
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_READY,
            "{} FakeSMTPd Service ready".format(FAKE_HOST))

    def test_invalid_line(self) -> None:
        self.reader.lines = ["ab"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.COMMAND_UNRECOGNIZED,
                                      "Command unrecognized")

    def test_unrecognized_command(self) -> None:
        self.reader.lines = ["XUNK "]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.COMMAND_UNRECOGNIZED,
                                      "Command unrecognized")

    def test_noop(self) -> None:
        self.reader.lines = ["NOOP"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__any_case(self) -> None:
        self.reader.lines = ["NoOp"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_space(self) -> None:
        self.reader.lines = ["NOOP "]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_arguments(self) -> None:
        self.reader.lines = ["NOOP foo bar"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_quit(self) -> None:
        self.reader.lines = ["QUIT"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel")
        self.writer.assert_is_closed()

    def test_quit_with_arguments(self) -> None:
        self.reader.lines = ["QUIT foo"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Unexpected arguments")
        self.writer.assert_is_closed()

    def test_quit__without_closing_channel(self) -> None:
        self.reader.lines = ["QUIT", "NOOP"]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel")
        self.writer.assert_is_closed()

    def test_helo(self) -> None:
        self.reader.lines = ["HELO client.example.com"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK,
                                      f"{FAKE_HOST} Hello client.example.com")

    def test_helo__no_domain(self) -> None:
        self.reader.lines = ["HELO "]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Missing arguments")

    def test_ehlo(self) -> None:
        self.reader.lines = ["EHLO client.example.com"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK,
                                      f"{FAKE_HOST} Hello client.example.com")

    def test_ehlo__no_domain(self) -> None:
        self.reader.lines = ["EHLO "]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Missing arguments")

    def test_mail(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FrOm:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_mail_with_helo(self) -> None:
        self.reader.lines = [
            "HELO client.example.com",
            "MAIL FROM:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_mail_no_from(self) -> None:
        self.reader.lines = \
            ["EHLO client.example.com", "MAIL ABC:<foo@example.com>"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Syntax error in arguments")

    def test_mail_invalid_sender(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:foo@example.com",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Syntax error in arguments")

    def test_mail_without_ehlo(self) -> None:
        self.reader.lines = ["MAIL FROM:<foo@example.com>"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE, "No EHLO sent")

    def test_mail_twice(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "MAIL FROM:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE,
                                      "Bad command sequence")

    def test_rcpt(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT tO:<bar@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Receiver OK")

    def test_rcpt_multiple(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar1@example.com>",
            "RCPT TO:<bar2@example.com>",
            "RCPT TO:<bar3@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Receiver OK")

    def test_rcpt_no_to(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT <bar@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Syntax error in arguments")

    def test_rcpt_invalid_address(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:foo@example.com",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Syntax error in arguments")

    def test_rcpt_without_mail(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "RCPT TO:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE,
                                      "Bad command sequence")

    def test_data(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar@example.com>",
            "DATA",
        ]
        self._handle()
        self.writer.assert_last_reply(
            SMTPStatus.START_MAIL_INPUT,
            "Enter mail text. End with . on a separate line.")

    def test_data_with_arguments(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar@example.com>",
            "DATA foo",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Unexpected arguments")

    def test_data_without_rcpt(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "DATA",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE,
                                      "Bad command sequence")

    def test_complete_mail(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar@example.com>",
            "DATA",
            "From: foo@example.com",
            "To: bar@example.com",
            "Subject: Foobar",
            "",
            "Line 1",
            "Line 2",
            ".",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_two_transactions(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar@example.com>",
            "DATA",
            "From: foo@example.com",
            "To: bar@example.com",
            "Subject: Foobar",
            "",
            ".",
            "MAIL FROM:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_rset(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RSET",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_rset_with_argument(self) -> None:
        self.reader.lines = ["RSET foo"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Unexpected arguments")

    def test_transaction_after_rset(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RSET",
            "MAIL FROM:<foo@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_rcpt_after_rset(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RSET",
            "RCPT TO:<bar@example.com>",
        ]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE,
                                      "Bad command sequence")

    def test_vrfy(self) -> None:
        self.reader.lines = ["VRFY client.example.com"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.CANNOT_VRFY,
                                      "Verify not allowed")

    def test_mail_printed(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar1@example.com>",
            "RCPT TO:<bar2@example.com>",
            "DATA",
            "From: foo@example.com",
            "To: bar@example.com",
            "Subject: Foobar",
            "",
            "Line 1  ",
            "Line 2",
            ".",
        ]
        self._handle()
        assert_is_not_none(self.printed_state)
        assert self.printed_state is not None
        assert_datetime_about_now_utc(self.printed_state.date)
        assert_equal("foo@example.com", self.printed_state.reverse_path)
        assert_equal(["bar1@example.com", "bar2@example.com"],
                     self.printed_state.forward_path)
        assert_equal("From: foo@example.com\r\n"
                     "To: bar@example.com\r\n"
                     "Subject: Foobar\r\n"
                     "\r\n"
                     "Line 1  \r\n"
                     "Line 2\r\n", self.printed_state.mail_data)

    def test_8bit_command(self) -> None:
        self.reader.lines = ["EHLO cl\xe4ent.example.com"]
        self._handle()
        self.writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS,
                                      "Unexpected 8 bit character")

    def test_8bit_text(self) -> None:
        self.reader.lines = [
            "EHLO client.example.com",
            "MAIL FROM:<foo@example.com>",
            "RCPT TO:<bar1@example.com>",
            "DATA",
            "From: f\xf6o@example.com",
            "",
            "B\xe4r",
            ".",
        ]
        self._handle()
        assert self.printed_state is not None
        assert_equal("From: f\x76o@example.com\r\n"
                     "\r\n"
                     "B\x64r\r\n", self.printed_state.mail_data)
