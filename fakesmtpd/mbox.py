from fakesmtpd.state import State


def print_mbox_mail(stream, state: State) -> None:
    """Print a mail in RFC 4155 default mbox format."""
    stream.write(f"From {state.reverse_path} {state.date.ctime()}\n")
    stream.write(state.mail_data.replace("\r\n", "\n"))
    stream.write("\n")
    stream.flush()
