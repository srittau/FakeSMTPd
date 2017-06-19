from socket import getfqdn
from typing import Tuple

from fakesmtpd.smtp import SMTPStatus


Reply = Tuple[SMTPStatus, str]


def handle_ehlo(arguments: str) -> Reply:
    if not arguments.strip():
        return handle_missing_arguments()
    return SMTPStatus.OK, f"{getfqdn()} Hello {arguments}"


def handle_helo(arguments: str) -> Reply:
    if not arguments.strip():
        return handle_missing_arguments()
    return SMTPStatus.OK, f"{getfqdn()} Hello {arguments}"


def handle_noop(arguments: str) -> Reply:
    return SMTPStatus.OK, "OK"


def handle_quit(arguments: str) -> Reply:
    if arguments:
        return handle_unexpected_arguments()
    msg = "{} Service closing transmission channel".format(getfqdn())
    return SMTPStatus.SERVICE_CLOSING, msg


def handle_unknown_command(arguments: str) -> Reply:
    return SMTPStatus.COMMAND_UNRECOGNIZED, "Command unrecognized"


def handle_unexpected_arguments() -> Reply:
    return SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Unexpected arguments"


def handle_missing_arguments() -> Reply:
    return SMTPStatus.SYNTAX_ERROR_IN_PARAMETERS, "Missing arguments"


_handlers = {
    "EHLO": handle_ehlo,
    "HELO": handle_helo,
    "NOOP": handle_noop,
    "QUIT": handle_quit,
}


def handle_command(command: str, arguments: str) -> Reply:
    try:
        handler = _handlers[command]
    except KeyError:
        handler = handle_unknown_command
    return handler(arguments)
