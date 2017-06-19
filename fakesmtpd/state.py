class State:

    def __init__(self) -> None:
        self.greeted = False
        self.clear()

    def clear(self) -> None:
        self.reverse_path = None
        self.forward_path = None
        self.mail_data = None

    @property
    def mail_allowed(self):
        return (
            self.greeted and
            self.reverse_path is None and
            self.forward_path is None and
            self.mail_data is None
        )

    @property
    def rcpt_allowed(self):
        return (
            self.greeted and
            self.reverse_path is not None and
            self.mail_data is None
        )

    @property
    def data_allowed(self):
        return (
            self.greeted and
            self.reverse_path is not None and
            self.forward_path is not None and
            self.mail_data is None
        )
