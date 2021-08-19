from __future__ import annotations

import datetime


class State:
    def __init__(self) -> None:
        self.greeted = False
        self.date: datetime.datetime | None = None
        self.reverse_path: str | None = None
        self.forward_path: list[str] | None = None
        self.mail_data: str | None = None

    def clear(self) -> None:
        self.reverse_path = None
        self.forward_path = None
        self.mail_data = None

    def add_forward_path(self, path: str) -> None:
        if self.forward_path is None:
            self.forward_path = []
        self.forward_path.append(path)

    def add_line(self, line: str) -> None:
        if self.mail_data is None:
            self.mail_data = ""
        self.mail_data += line

    @property
    def mail_allowed(self) -> bool:
        return (
            self.greeted
            and self.reverse_path is None
            and self.forward_path is None
            and self.mail_data is None
        )

    @property
    def rcpt_allowed(self) -> bool:
        return (
            self.greeted
            and self.reverse_path is not None
            and self.mail_data is None
        )

    @property
    def data_allowed(self) -> bool:
        return (
            self.greeted
            and self.reverse_path is not None
            and self.forward_path is not None
            and self.mail_data is None
        )
