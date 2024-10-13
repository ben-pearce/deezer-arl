import os
import logging
import typing
import argparse
from abc import ABC, abstractmethod

DATA_DIR = os.path.join(os.getcwd(), 'data')

logger = logging.getLogger(__name__)

class Consumer(ABC):

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    async def consume(self, arls: typing.List[str]) -> bool:
        pass

    @classmethod
    @abstractmethod
    def parser(cls) -> argparse.ArgumentParser:
        pass
