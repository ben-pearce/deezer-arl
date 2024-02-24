import typing

from deezer_arl.provider.provider import Provider
from deezer_arl.provider.telegram import Telegram as TelegramProvider
from deezer_arl.provider.web import Web as WebProvider
from deezer_arl.provider.provider import Manager

Providers = [TelegramProvider, WebProvider]
