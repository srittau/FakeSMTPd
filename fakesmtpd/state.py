import datetime
from typing import Optional, List


class State:

    def __init__(self) -> None:
        self.greeted = False
        self.date: Optional[datetime.datetime] = None
        self.reverse_path: Optional[str] = None
        self.forward_path: Optional[List[str]] = None
        self.mail_data: Optional[str] = None

    def clear(self) -> None:
        self.reverse_path: Optional[str] = None
        self.forward_path: Optional[List[str]] = None
        self.mail_data: Optional[str] = None

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
            self.greeted and
            self.reverse_path is None and
            self.forward_path is None and
            self.mail_data is None
        )

    @property
    def rcpt_allowed(self) -> bool:
        return (
            self.greeted and
            self.reverse_path is not None and
            self.mail_data is None
        )

    @property
    def data_allowed(self) -> bool:
        return (
            self.greeted and
            self.reverse_path is not None and
            self.forward_path is not None and
            self.mail_data is None
        )
