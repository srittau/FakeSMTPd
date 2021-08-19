from __future__ import annotations

import asyncio
import datetime

import pytest
from pytest_mock import MockerFixture

from fakesmtpd.connection import CRLF_LENGTH, ConnectionHandler
from fakesmtpd.smtp import SMTP_COMMAND_LIMIT, SMTP_TEXT_LINE_LIMIT, SMTPStatus
from fakesmtpd.state import State

FAKE_HOST = "mail.example.com"


class FakeStreamReader:
    def __init__(self) -> None:
        self.lines: list[str] = []

    # SUT Interface

    async def readuntil(self, separator: bytes = b"\n") -> bytes:
        assert separator == b"\r\n"
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
            pytest.fail("writer unexpectedly still open")

    @property
    def lines(self) -> list[str]:
        return self.data.decode("ascii").splitlines()

    def assert_last_line_equal(self, line: str) -> None:
        assert len(self.lines) >= 1, "no response"
        assert self.lines[-1] == line

    def assert_last_reply(self, code: SMTPStatus, text: str) -> None:
        expected_line = f"{code.value} {text}"
        self.assert_last_line_equal(expected_line)


class TestConnectionHandler:
    @pytest.fixture(autouse=True)
    def getfqdn(self, mocker: MockerFixture) -> None:
        mocker.patch("fakesmtpd.connection.getfqdn", lambda: FAKE_HOST)
        mocker.patch("fakesmtpd.commands.getfqdn", lambda: FAKE_HOST)

    def _handle(self, lines: list[str] = []) -> FakeStreamWriter:
        reader = FakeStreamReader()
        reader.lines = lines
        writer = FakeStreamWriter()
        loop = asyncio.get_event_loop()
        handler = ConnectionHandler(reader, writer, self._print_mail)
        loop.run_until_complete(handler.handle())
        return writer

    def _print_mail(self, state: State) -> None:
        self.printed_state = state

    def test_greeting(self) -> None:
        writer = self._handle()
        writer.assert_last_reply(
            SMTPStatus.SERVICE_READY,
            "{} FakeSMTPd Service ready".format(FAKE_HOST),
        )

    def test_invalid_line(self) -> None:
        writer = self._handle(["ab"])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR,
            "Command unrecognized",
        )

    def test_unrecognized_command(self) -> None:
        writer = self._handle(["XUNK "])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR,
            "Command unrecognized",
        )

    def test_command_line_too_long(self) -> None:
        arg_length = (
            SMTP_COMMAND_LIMIT - 5 - CRLF_LENGTH
        )  # command + space + <CRLF>
        writer = self._handle([f"NOOP {'X' * (arg_length + 1)}"])
        writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR, "Line too long.")

    def test_command_line_length_ok(self) -> None:
        arg_length = (
            SMTP_COMMAND_LIMIT - 5 - CRLF_LENGTH
        )  # command + space + <CRLF>
        writer = self._handle([f"NOOP {'X' * arg_length}"])
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop(self) -> None:
        writer = self._handle(["NOOP"])
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__any_case(self) -> None:
        writer = self._handle(["NoOp"])
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_space(self) -> None:
        writer = self._handle(["NOOP "])
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_noop__with_arguments(self) -> None:
        writer = self._handle(["NOOP foo bar"])
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_quit(self) -> None:
        writer = self._handle(["QUIT"])
        writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel",
        )
        writer.assert_is_closed()

    def test_quit_with_arguments(self) -> None:
        writer = self._handle(["QUIT foo"])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments"
        )
        writer.assert_is_closed()

    def test_quit__without_closing_channel(self) -> None:
        writer = self._handle(["QUIT", "NOOP"])
        writer.assert_last_reply(
            SMTPStatus.SERVICE_CLOSING,
            f"{FAKE_HOST} Service closing transmission channel",
        )
        writer.assert_is_closed()

    def test_helo(self) -> None:
        writer = self._handle(["HELO client.example.com"])
        writer.assert_last_reply(
            SMTPStatus.OK, f"{FAKE_HOST} Hello client.example.com"
        )

    def test_helo__no_domain(self) -> None:
        writer = self._handle(["HELO "])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments"
        )

    def test_ehlo(self) -> None:
        writer = self._handle(["EHLO client.example.com"])
        writer.assert_last_reply(
            SMTPStatus.OK, f"{FAKE_HOST} Hello client.example.com"
        )

    def test_ehlo__no_domain(self) -> None:
        writer = self._handle(["EHLO "])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments"
        )

    def test_mail(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FrOm:<foo@example.com>",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_mail_with_helo(self) -> None:
        writer = self._handle(
            [
                "HELO client.example.com",
                "MAIL FROM:<foo@example.com>",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_mail_no_from(self) -> None:
        writer = self._handle(
            ["EHLO client.example.com", "MAIL ABC:<foo@example.com>"]
        )
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Syntax error in arguments"
        )

    def test_mail_invalid_sender(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:foo@example.com",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Syntax error in arguments"
        )

    def test_mail_without_ehlo(self) -> None:
        writer = self._handle(["MAIL FROM:<foo@example.com>"])
        writer.assert_last_reply(SMTPStatus.BAD_SEQUENCE, "No EHLO sent")

    def test_mail_twice(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "MAIL FROM:<foo@example.com>",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.BAD_SEQUENCE, "Bad command sequence"
        )

    def test_rcpt(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT tO:<bar@example.com>",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "Receiver OK")

    def test_rcpt_multiple(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:<bar1@example.com>",
                "RCPT TO:<bar2@example.com>",
                "RCPT TO:<bar3@example.com>",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "Receiver OK")

    def test_rcpt_no_to(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT <bar@example.com>",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Syntax error in arguments"
        )

    def test_rcpt_invalid_address(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:foo@example.com",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Syntax error in arguments"
        )

    def test_rcpt_without_mail(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "RCPT TO:<foo@example.com>",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.BAD_SEQUENCE, "Bad command sequence"
        )

    def test_data(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:<bar@example.com>",
                "DATA",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.START_MAIL_INPUT,
            "Enter mail text. End with . on a separate line.",
        )

    def test_data_with_arguments(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:<bar@example.com>",
                "DATA foo",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments"
        )

    def test_data_without_rcpt(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "DATA",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.BAD_SEQUENCE, "Bad command sequence"
        )

    def test_complete_mail(self) -> None:
        writer = self._handle(
            [
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
        )
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_two_transactions(self) -> None:
        writer = self._handle(
            [
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
        )
        writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_rset(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RSET",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "OK")

    def test_rset_with_argument(self) -> None:
        writer = self._handle(["RSET foo"])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments"
        )

    def test_transaction_after_rset(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RSET",
                "MAIL FROM:<foo@example.com>",
            ]
        )
        writer.assert_last_reply(SMTPStatus.OK, "Sender OK")

    def test_rcpt_after_rset(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RSET",
                "RCPT TO:<bar@example.com>",
            ]
        )
        writer.assert_last_reply(
            SMTPStatus.BAD_SEQUENCE, "Bad command sequence"
        )

    def test_vrfy(self) -> None:
        writer = self._handle(["VRFY client.example.com"])
        writer.assert_last_reply(SMTPStatus.CANNOT_VRFY, "Verify not allowed")

    def test_mail_printed(self) -> None:
        self._handle(
            [
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
        )
        assert self.printed_state is not None
        assert isinstance(self.printed_state.date, datetime.datetime)
        assert self.printed_state.reverse_path == "foo@example.com"
        assert self.printed_state.forward_path == [
            "bar1@example.com",
            "bar2@example.com",
        ]
        assert self.printed_state.mail_data == (
            "From: foo@example.com\r\n"
            "To: bar@example.com\r\n"
            "Subject: Foobar\r\n"
            "\r\n"
            "Line 1  \r\n"
            "Line 2\r\n"
        )

    def test_8bit_command(self) -> None:
        writer = self._handle(["EHLO cl\xe4ent.example.com"])
        writer.assert_last_reply(
            SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected 8 bit character"
        )

    def test_8bit_text(self) -> None:
        self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:<bar1@example.com>",
                "DATA",
                "From: f\xf6o@example.com",
                "",
                "B\xe4r",
                ".",
            ]
        )
        assert self.printed_state is not None
        assert self.printed_state.mail_data == (
            "From: f\x76o@example.com\r\n" "\r\n" "B\x64r\r\n"
        )

    def test_data_line_too_long(self) -> None:
        writer = self._handle(
            [
                "EHLO client.example.com",
                "MAIL FROM:<foo@example.com>",
                "RCPT TO:<bar@example.com>",
                "DATA",
                "a" * (SMTP_TEXT_LINE_LIMIT - 1),
            ]
        )
        writer.assert_last_reply(SMTPStatus.SYNTAX_ERROR, "Line too long.")
