import re
from socket import getfqdn
from typing import Tuple

from fakesmtpd.smtp import SMTPStatus
from fakesmtpd.state import State

Reply = Tuple[SMTPStatus, str]


def handle_data(state: State, arguments: str) -> Reply:
    if arguments:
        return handle_unexpected_arguments()
    if not state.data_allowed:
        return handle_bad_command_sequence()
    return (
        SMTPStatus.START_MAIL_INPUT,
        "Enter mail text. End with . on a separate line.",
    )


def handle_ehlo(state: State, arguments: str) -> Reply:
    if not arguments.strip():
        return handle_missing_arguments()
    state.greeted = True
    return SMTPStatus.OK, f"{getfqdn()} Hello {arguments}"


def handle_helo(state: State, arguments: str) -> Reply:
    if not arguments.strip():
        return handle_missing_arguments()
    state.greeted = True
    return SMTPStatus.OK, f"{getfqdn()} Hello {arguments}"


def handle_mail(state: State, arguments: str) -> Reply:
    m = re.match(r"^FROM:<(.*)>", arguments, re.IGNORECASE)
    if not m:
        return handle_wrong_arguments()
    if not state.greeted:
        return handle_no_greeting()
    if not state.mail_allowed:
        return handle_bad_command_sequence()
    state.clear()
    state.reverse_path = m.group(1)
    return SMTPStatus.OK, "Sender OK"


def handle_noop(state: State, arguments: str) -> Reply:
    return SMTPStatus.OK, "OK"


def handle_quit(state: State, arguments: str) -> Reply:
    if arguments:
        return handle_unexpected_arguments()
    msg = "{} Service closing transmission channel".format(getfqdn())
    return SMTPStatus.SERVICE_CLOSING, msg


def handle_rcpt(state: State, arguments: str) -> Reply:
    m = re.match(r"^TO:<(.*)>", arguments, re.IGNORECASE)
    if not m:
        return handle_wrong_arguments()
    if not state.rcpt_allowed:
        return handle_bad_command_sequence()
    state.add_forward_path(m.group(1))
    return SMTPStatus.OK, "Receiver OK"


def handle_rset(state: State, arguments: str) -> Reply:
    if arguments:
        return handle_unexpected_arguments()
    state.clear()
    return SMTPStatus.OK, "OK"


def handle_vrfy(state: State, arguments: str) -> Reply:
    return SMTPStatus.CANNOT_VRFY, "Verify not allowed"


def handle_unknown_command(state: State, arguments: str) -> Reply:
    return SMTPStatus.COMMAND_UNRECOGNIZED, "Command unrecognized"


def handle_unexpected_arguments() -> Reply:
    return SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments"


def handle_missing_arguments() -> Reply:
    return SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments"


def handle_wrong_arguments() -> Reply:
    return SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Syntax error in arguments"


def handle_bad_command_sequence() -> Reply:
    return SMTPStatus.BAD_SEQUENCE, "Bad command sequence"


def handle_no_greeting() -> Reply:
    return SMTPStatus.BAD_SEQUENCE, "No EHLO sent"


_handlers = {
    "DATA": handle_data,
    "EHLO": handle_ehlo,
    "HELO": handle_helo,
    "MAIL": handle_mail,
    "NOOP": handle_noop,
    "QUIT": handle_quit,
    "RCPT": handle_rcpt,
    "RSET": handle_rset,
    "VRFY": handle_vrfy,
}


def handle_command(state: State, command: str, arguments: str) -> Reply:
    try:
        handler = _handlers[command]
    except KeyError:
        handler = handle_unknown_command
    return handler(state, arguments)
