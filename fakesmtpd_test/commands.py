from unittest import TestCase
from unittest.mock import patch

from asserts import assert_true, assert_equal

from fakesmtpd.commands import handle_helo, handle_ehlo, handle_mail, \
    handle_rcpt
from fakesmtpd.smtp import SMTPStatus
from fakesmtpd.state import State


class EHLOTest(TestCase):
    def setUp(self) -> None:
        self._get_fqdn_p = patch("fakesmtpd.commands.getfqdn")
        self.getfqdn = self._get_fqdn_p.start()
        self.getfqdn.return_value = "smtp.example.com"

    def tearDown(self) -> None:
        self._get_fqdn_p.stop()

    def test_set_greeted(self) -> None:
        state = State()
        state.greeted = False
        handle_ehlo(state, "example.com")
        assert_true(state.greeted)

    def test_response(self) -> None:
        self.getfqdn.return_value = "smtp.example.org"
        code, message = handle_ehlo(State(), "example.com")
        assert_equal(SMTPStatus.OK, code)
        assert_equal("smtp.example.org Hello example.com", message)

    def test_empty_argument(self) -> None:
        code, message = handle_ehlo(State(), "   ")
        assert_equal(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, code)
        assert_equal("Missing arguments", message)


class HELOTest(TestCase):
    def setUp(self) -> None:
        self._get_fqdn_p = patch("fakesmtpd.commands.getfqdn")
        self.getfqdn = self._get_fqdn_p.start()
        self.getfqdn.return_value = "smtp.example.com"

    def tearDown(self) -> None:
        self._get_fqdn_p.stop()

    def test_set_greeted(self) -> None:
        state = State()
        state.greeted = False
        handle_helo(state, "example.com")
        assert_true(state.greeted)

    def test_response(self) -> None:
        self.getfqdn.return_value = "smtp.example.org"
        code, message = handle_helo(State(), "example.com")
        assert_equal(SMTPStatus.OK, code)
        assert_equal("smtp.example.org Hello example.com", message)

    def test_empty_argument(self) -> None:
        code, message = handle_helo(State(), "   ")
        assert_equal(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, code)
        assert_equal("Missing arguments", message)


class MAILTest(TestCase):
    def test_response(self) -> None:
        state = State()
        state.greeted = True
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert_equal(SMTPStatus.OK, code)
        assert_equal("Sender OK", message)

    def test_reverse_path_set(self) -> None:
        state = State()
        state.greeted = True
        handle_mail(state, "FROM:<foo@example.com>")
        assert_equal("foo@example.com", state.reverse_path)

    def test_empty_argument(self) -> None:
        code, message = handle_mail(State(), "")
        assert_equal(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, code)
        assert_equal("Syntax error in arguments", message)

    def test_not_greeted(self) -> None:
        state = State()
        state.greeted = False
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("No EHLO sent", message)

    def test_has_reverse_path(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)

    def test_has_forward_path(self) -> None:
        state = State()
        state.greeted = True
        state.forward_path = "bar@example.org"
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)

    def test_has_mail_data(self) -> None:
        state = State()
        state.greeted = True
        state.mail_data = ""
        code, message = handle_mail(state, "FROM:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)


class RCPTTest(TestCase):
    def test_response(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert_equal(SMTPStatus.OK, code)
        assert_equal("Receiver OK", message)

    def test_forward_paths_added(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        handle_rcpt(state, "TO:<foo1@example.com>")
        handle_rcpt(state, "TO:<foo2@example.com>")
        assert_equal(["foo1@example.com", "foo2@example.com"],
                     state.forward_path)

    def test_empty_argument(self) -> None:
        code, message = handle_rcpt(State(), "")
        assert_equal(SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, code)
        assert_equal("Syntax error in arguments", message)

    def test_not_greeted(self) -> None:
        state = State()
        state.greeted = False
        state.reverse_path = "bar@example.org"
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)

    def test_no_reverse_path(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = None
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)

    def test_mail_data(self) -> None:
        state = State()
        state.greeted = True
        state.reverse_path = "bar@example.org"
        state.mail_data = ""
        code, message = handle_rcpt(state, "TO:<foo@example.com>")
        assert_equal(SMTPStatus.BAD_SEQUENCE, code)
        assert_equal("Bad command sequence", message)
