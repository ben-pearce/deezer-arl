import argparse
import typing
import re
import itertools
from deezer_arl.consumer.consumer import Consumer


class File(Consumer):

    files: str

    def __init__(
        self,
        files=None
    ):
        self.files = files

    async def consume(self, arls: typing.List[str]) -> bool:
        circle = itertools.cycle(arls)
        for file in self.files:
            with open(file, 'r', encoding="utf-8") as fin:
                data = re.sub(r'([a-f0-9]{192})', lambda _: next(circle), fin.read())
            with open(file, 'w', encoding="utf-8") as fout:
                fout.write(data)

    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser('FileConsumer')
        parser.add_argument(
            '--files',
            type=str,
            action='append',
            help='Find and update ARLs in file'
        )
        return parser
