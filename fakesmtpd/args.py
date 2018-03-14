import argparse
from smtplib import SMTP_PORT  # type: ignore
from typing import Any


def parse_args() -> Any:
    parser = argparse.ArgumentParser(
        description="SMTP server for testing mail functionality")
    parser.add_argument(
        "--output-filename", "-o", nargs="?", default="-",
        help="output mbox file, default stdout")
    parser.add_argument(
        "--bind", "-b", nargs="?", default="127.0.0.1",
        help="IP address range to listen to")
    parser.add_argument(
        "--port", "-p", type=int, nargs="?", default=SMTP_PORT,
        help="SMTP port to listen on")
    return parser.parse_args()
