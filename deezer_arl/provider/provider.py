import re
import sys
import typing
import os
import json
import argparse
import logging
from abc import ABC, abstractmethod

DATA_DIR = os.path.join(os.getcwd(), 'data')

logger = logging.getLogger(__name__)

class Provider(ABC):

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __eq__(self, provider: 'Provider') -> bool:
        pass

    @abstractmethod
    async def fetch(self) -> typing.List[str]:
        pass

    @classmethod
    @abstractmethod
    def parser(cls) -> argparse.ArgumentParser:
        pass

    @classmethod
    def _extract_arls(cls, haystack: str) -> typing.List[str]:
        return re.findall(r'[a-f0-9]{192}', haystack)

class Manager:

    ProvidersPath = os.path.join(DATA_DIR, 'providers.json')

    def get(self, index: typing.Optional[int] = None) -> typing.Set[Provider]:
        try:
            with open(Manager.ProvidersPath, 'r', encoding="utf-8") as f:
                providers = json.load(f)
        except FileNotFoundError:
            providers = []

        return [
            getattr(
                sys.modules[provider['module']],
                provider['class']
            )(**provider['args'])
            for provider in providers[
                index
                if index is not None
                else 0:len(providers)
            ]
        ]

    async def add(self, provider: typing.Union[str, Provider], **kwargs):
        if isinstance(provider, str):
            module = 'deezer_arl.provider.' + provider.lower()
            provider = getattr(sys.modules[module], provider)(**kwargs)

        assert isinstance(provider, Provider)
        assert isinstance(await provider.fetch(), list)

        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR, 755)

        try:
            with open(Manager.ProvidersPath, 'r', encoding="utf-8") as f:
                providers = json.load(f)
        except FileNotFoundError:
            providers = []

        providers.append({
            'module': type(provider).__module__,
            'class': type(provider).__name__,
            'args': kwargs
        })

        with open(Manager.ProvidersPath, 'w', encoding="utf-8") as f:
            json.dump(providers, f, indent=2)

        logger.info('Added new provider: %s', provider)

    def remove(self, index: int):
        try:
            with open(Manager.ProvidersPath, 'r', encoding="utf-8") as f:
                providers = json.load(f)
        except FileNotFoundError:
            providers = []

        provider = providers[index]
        del providers[index]

        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR, 755)

        with open(Manager.ProvidersPath, 'w', encoding="utf-8") as f:
            json.dump(providers, f, indent=2)

        logger.info('Removed provider: %s', provider)
