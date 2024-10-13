import argparse
import typing
import json
import jsonpath_ng

from deezer_arl.consumer.consumer import Consumer


class Json(Consumer):

    file: str
    path: str

    def __init__(
        self,
        file=None,
        path=None
    ):
        self.file = file
        self.path = path

    async def consume(self, arls: typing.List[str]) -> bool:
        with open(self.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            parser = jsonpath_ng.parse(self.path)
            res = parser.find(data)
            for i, match in enumerate(res):
                match.full_path.update(data, arls[i%len(arls)])

        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser('JsonConsumer')
        parser.add_argument('--file', help="File to update")
        parser.add_argument('--path', help="JSON path to update")
        return parser
