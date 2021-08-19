from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from fakesmtpd.commands import (
    handle_ehlo,
    handle_helo,
    handle_mail,
    handle_rcpt,
)
from fakesmtpd.smtp import (
    SMTP_DOMAIN_LIMIT,
    SMTP_LOCAL_PART_LIMIT,
    SMTP_PATH_LIMIT,
    SMTPStatus,
)
from fakesmtpd.state import State


@pytest.fixture(autouse=True)
def getfqdn(mocker: MockerFixture) -> Mock:
    return mocker.patch(
        "fakesmtpd.commands.getfqdn",
        return_value="smtp.example.com",
    )


class TestEHLO:
    def test_domain(self, getfqdn: Mock) -> None:
        state = State()
        state.greeted = False
        getfqdn.return_value = "smtp.example.org"
        code, message = handle_ehlo(state, "example.com")
        assert code == SMTPStatus.OK
        assert message == "smtp.example.org Hello example.com"
        assert state.greeted

    def test_address_literal(self, getfqdn: Mock) -> None:
        state = State()
        state.greeted = False
        getfqdn.return_value = "smtp.example.org"
        code, message = handle_ehlo(state, "[192.168.99.22]")
        assert code == SMTPStatus.OK
        assert message == "smtp.example.org Hello [192.168.99.22]"
        assert state.greeted

    def test_empty_argument(self) -> None:
        code, message = handle_ehlo(State(), "")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Missing arguments"

    def test_invalid_argument(self) -> None:
        code, message = handle_ehlo(State(), "*")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"


class TestHELO:
    def test_set_greeted(self) -> None:
        state = State()
        state.greeted = False
        handle_helo(state, "example.com")
        assert state.greeted

    def test_response(self, getfqdn: Mock) -> None:
        getfqdn.return_value = "smtp.example.org"
        code, message = handle_helo(State(), "example.com")
        assert code == SMTPStatus.OK
        assert message == "smtp.example.org Hello example.com"

    def test_no_argument(self) -> None:
        code, message = handle_helo(State(), "")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Missing arguments"

    def test_invalid_domain(self) -> None:
        code, message = handle_helo(State(), "*")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"


class TestMAIL:
    def test_with_mailbox(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert code == SMTPStatus.OK
        assert message == "Sender OK"
        assert state.reverse_path == "foo@example.com"

    def test_empty_path(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(state, "FROM:<>")
        assert code == SMTPStatus.OK
        assert message == "Sender OK"
        assert state.reverse_path == ""

    def test_with_arguments(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(
            state, "FROM:<foo@example.com> foo=bar abc"
        )
        assert code == SMTPStatus.OK
        assert message == "Sender OK"
        assert state.reverse_path == "foo@example.com"

    def test_with_arguments_and_quoted_local_part(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(
            state, 'FROM:<"foo bar"@example.com> foo=bar'
        )
        assert code == SMTPStatus.OK
        assert message == "Sender OK"
        assert state.reverse_path == '"foo bar"@example.com'

    def test_empty(self) -> None:
        code, message = handle_mail(State(), "")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_invalid_path(self) -> None:
        code, message = handle_mail(State(), "FROM:INVALID")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_path_too_long(self) -> None:
        code, message = handle_mail(
            State(), f"FROM:<{'a' * 60}@{'a' * (SMTP_PATH_LIMIT - 61)}>"
        )
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Path too long"

    def test_local_part_too_long(self) -> None:
        code, message = handle_mail(
            State(), f"FROM:<{'a' * (SMTP_LOCAL_PART_LIMIT + 1)}@example.com>"
        )
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Path too long"

    def test_invalid_mailbox(self) -> None:
        code, message = handle_mail(State(), "FROM:<INVALID>")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_path_with_trailing_chars(self) -> None:
        code, message = handle_mail(State(), "FROM:<foo@example.com>foo=bar")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_invalid_argument(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(state, "FROM:<foo@example.com> -foo=bar")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_not_greeted(self) -> None:
        state = State()
        state.greeted = False
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "No EHLO sent"

    def test_has_reverse_path(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"

    def test_has_forward_path(self) -> None:
        state = State()
        state.greeted = True
        state.forward_path = ["bar@example.org"]
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"

    def test_has_mail_data(self) -> None:
        state = State()
        state.greeted = True
        state.mail_data = ""
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"


class TestRCPT:
    def test_response(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert code == SMTPStatus.OK
        assert message == "Receiver OK"

    def test_forward_paths_added(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        handle_rcpt(state, "TO:<foo1@example.com>")
        handle_rcpt(state, "TO:<foo2@example.com>")
        assert state.forward_path == ["foo1@example.com", "foo2@example.com"]

    def test_postmaster(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<postMaster> foo")
        assert code == SMTPStatus.OK
        assert message == "Receiver OK"
        assert state.forward_path == ["postMaster"]

    def test_with_arguments(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<foo@example.com> foo=bar baz")
        assert code == SMTPStatus.OK
        assert message == "Receiver OK"
        assert state.forward_path == ["foo@example.com"]

    def test_empty_argument(self) -> None:
        code, message = handle_rcpt(State(), "")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_empty_path(self) -> None:
        code, message = handle_rcpt(State(), "TO:<>")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_path_too_long(self) -> None:
        code, message = handle_rcpt(
            State(), f"TO:<{'a' * 60}@{'a' * (SMTP_PATH_LIMIT - 61)}>"
        )
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Path too long"

    def test_local_part_too_long(self) -> None:
        code, message = handle_rcpt(
            State(), f"TO:<{'a' * (SMTP_LOCAL_PART_LIMIT + 1)}@example.com>"
        )
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Path too long"

    def test_domain_too_long(self) -> None:
        code, message = handle_rcpt(
            State(), f"TO:<foo@{'a' * (SMTP_DOMAIN_LIMIT + 1)}>"
        )
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Path too long"

    def test_path_with_trailing_chars(self) -> None:
        code, message = handle_rcpt(State(), "TO:<foo@example.com>foo=bar")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_invalid_argument(self) -> None:
        code, message = handle_rcpt(State(), "TO:<foo@example.com> -foo")
        assert code == SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS
        assert message == "Syntax error in arguments"

    def test_not_greeted(self) -> None:
        state = State()
        state.greeted = False
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"

    def test_no_reverse_path(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = None
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"

    def test_mail_data(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        state.mail_data = ""
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert code == SMTPStatus.BAD_SEQUENCE
        assert message == "Bad command sequence"
