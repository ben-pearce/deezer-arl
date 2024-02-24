import typing
import aiohttp
import argparse
from deezer_arl.provider.provider import Provider

class Web(Provider):

    url: str

    def __init__(
        self,
        url=None
    ):
        self.url = url

    def __hash__(self):
        return hash(self.url)

    def __repr__(self):
        return f'Web(url=\'{self.url}\')'

    def __eq__(self, provider: Provider) -> bool:
        if not isinstance(provider, type(self)):
            return False
        return self.url == provider.url

    async def fetch(self) -> typing.List[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as resp:
                return Provider._extract_arls(await resp.text())
        return []

    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser('Web')
        parser.add_argument('--url', help="URL to scrape")
        return parser
