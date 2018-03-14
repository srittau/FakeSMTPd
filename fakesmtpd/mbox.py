import sys
from typing import IO

from fakesmtpd.state import State


def print_mbox_mail(filename: str, state: State) -> None:
    """Print a mail in RFC 4155 default mbox format."""
    if filename == "-":
        write_mbox_mail(sys.stdout, state)
    else:
        with open(filename, "a") as f:
            write_mbox_mail(f, state)


def write_mbox_mail(stream: IO[str], state: State) -> None:
    assert state.date is not None
    assert state.forward_path is not None
    assert state.mail_data is not None
    stream.write(f"From {state.reverse_path} {state.date.ctime()}\n")
    for receiver in state.forward_path:
        stream.write(f"X-FakeSMTPd-Receiver: {receiver}\n")
    stream.write(state.mail_data.replace("\r\n", "\n"))
    stream.write("\n")
    stream.flush()
