from asyncio.streams import StreamReader, StreamWriter
import logging


class ConnectionHandler:

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def handle(self) -> None:
        logging.info("connection opened")
        self.writer.close()
        logging.info("connection closed")


async def handle_connection(reader: StreamReader, writer: StreamWriter) \
        -> None:
    await ConnectionHandler(reader, writer).handle()
