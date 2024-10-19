import typing
import itertools
import os
import argparse
from datetime import timedelta, datetime

from telethon import TelegramClient
from telethon.tl.types import PeerChannel

from deezer_arl.provider.provider import Provider

DATA_DIR = os.path.join(os.getcwd(), 'data', 'providers', 'telegram')

class Telegram(Provider):

    _api_id: str
    _api_hash: str
    channel_id: typing.Optional[int]
    entity_id: typing.Optional[str]
    offset_days: int

    def __init__(
        self,
        api_id=None,
        api_hash=None,
        channel_id=None,
        entity_id=None,
        offset_days: int = 30
    ):
        self._api_id = api_id
        self._api_hash = api_hash
        self.channel_id = channel_id
        self.entity_id = entity_id
        self.offset_days = offset_days

    def __hash__(self):
        return hash((self.channel_id, self.entity_id))

    def __repr__(self):
        return f'Telegram(channel=\'{self.channel_id}\', entity=\'{self.entity_id}\')'

    def __eq__(self, provider: Provider) -> bool:
        if not isinstance(provider, type(self)):
            return False
        return self.channel_id == provider.channel_id and\
            self.entity_id == provider.entity_id

    async def fetch(self) -> typing.List[str]:
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR, 755)

        async with TelegramClient(
            os.path.join(DATA_DIR, self._api_id),
            self._api_id,
            self._api_hash
        ) as client:
            if self.entity_id is not None:
                entity = await client.get_entity(self.entity_id)
            else: entity = PeerChannel(self.channel_id)
            corpus = str()
            async for message in client.iter_messages(
                entity,
                offset_date=datetime.today() - timedelta(days=self.offset_days),
                reverse=True
            ):
                if message.text is not None:
                    corpus += message.text + '\n'
            return Provider._extract_arls(corpus)
        return []

    @classmethod
    def parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser('Telegram')
        parser.add_argument('--api-id', type=str, help="Telegram API ID")
        parser.add_argument('--api-hash', type=str, help="Telegram API hash")
        parser_entity_group = parser.add_mutually_exclusive_group()
        parser_entity_group.add_argument(
            '-ci', '--channel-id',
            type=int,
            help="Telegram channel to scrape"
        )
        parser_entity_group.add_argument(
            '-ei', '--entity-id',
            type=str,
            help="Telegram entity to scrape"
        )
        parser.add_argument('-o', '--offset-days', type=int, default=30, help="Days to scrape")
        return parser
