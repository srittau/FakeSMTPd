import datetime

from asserts import assert_equal
from io import StringIO
from unittest import TestCase

from fakesmtpd.mbox import write_mbox_mail
from fakesmtpd.state import State


class WriteMboxMailTest(TestCase):

    def test_print(self) -> None:
        out = StringIO()
        state = State()
        state.date = datetime.datetime(2017, 6, 4, 14, 34, 15)
        state.reverse_path = "sender@example.com"
        state.forward_path = ["receiver1@example.com", "receiver2@example.com"]
        state.mail_data = "Subject: Foo\r\n\r\nText\r\n"
        write_mbox_mail(out, state)
        assert_equal("From sender@example.com Sun Jun  4 14:34:15 2017\n"
                     "X-FakeSMTPd-Receiver: receiver1@example.com\n"
                     "X-FakeSMTPd-Receiver: receiver2@example.com\n"
                     "Subject: Foo\n"
                     "\n"
                     "Text\n"
                     "\n", out.getvalue())
