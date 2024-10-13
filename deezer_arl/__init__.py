import asyncio
import threading
import time
from datetime import datetime, timedelta
import typing
import concurrent
import os
import json
import logging
from deezer import Deezer

from deezer_arl.provider import\
    Providers, Provider, TelegramProvider,\
    WebProvider, Manager as ProviderManager

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.getcwd(), 'data')
DEFAULT_SCRAPE_URL = 'https://rentry.org/firehawk52'

class Scraper:

    DefaultProviders = [
        WebProvider(url=DEFAULT_SCRAPE_URL)
    ]

    @classmethod
    async def scrape(
        cls,
        providers: typing.Optional[typing.List[Provider]] = None
    ) -> typing.Set[str]:
        if not providers:
            providers = Scraper.DefaultProviders

        arls = []
        for provider in providers:
            arls += await provider.fetch()

        return set(arls)


class Validator:

    ValidatedPath = os.path.join(DATA_DIR, 'validated.json')
    InvalidatedPath = os.path.join(DATA_DIR, 'invalidated.json')

    @classmethod
    def session_logged_in(cls, session: dict) -> bool:
        return session['logged_in']

    @classmethod
    def session_can_stream_hq(cls, session: dict) -> bool:
        return Validator.session_logged_in(session) \
            and session['current_user']['can_stream_hq']

    @classmethod
    def session_can_stream_lossless(cls, session: dict) -> bool:
        return Validator.session_logged_in(session) \
            and session['current_user']['can_stream_lossless']

    @classmethod
    def session_country(cls, countries: typing.List[str]) -> typing.Callable[[dict], bool]:
        def validate_country(session: dict) -> bool:
            return Validator.session_logged_in(session)\
                and session['current_user']['country'] in countries
        return validate_country

    @classmethod
    async def validate(
        cls,
        arls: typing.Set[str],
        validators: typing.List[typing.Callable[dict, bool]],
        max_requests: int = 3,
        sleep_timeout: int = 5,
        cache_expiry: int = 43200,
        max_arls:int = 0
    ) -> typing.Dict[str, typing.Dict]:
        now = datetime.now()

        loop = asyncio.get_event_loop()
        sem = threading.Semaphore(max_requests)

        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR, 755)

        try:
            with open(Validator.ValidatedPath, 'r', encoding="utf-8") as f:
                validated = json.load(f)
                validated_expired = {
                    arl: v
                    for arl, v in validated.items()
                    if datetime.fromisoformat(v['expiry']) <= now
                }
        except FileNotFoundError:
            validated = {}
            validated_expired = {}

        try:
            with open(Validator.InvalidatedPath, 'r', encoding="utf-8") as f:
                invalidated = {
                    arl: v
                    for arl, v in json.load(f).items()
                    if datetime.fromisoformat(v['expiry']) > now
                }
        except FileNotFoundError:
            invalidated = {}

        logger.debug(
            "Existing validated ARLs: %d, Existing invalidated ARLs: %d, ARLs to revalidate: %d", 
            len(validated),
            len(invalidated),
            len(validated_expired)
        )

        def deezer_login(arl: str):
            sem.acquire()

            logger.debug('Grabbing session for arl: %s...', arl[0:10])

            d = Deezer()
            d.login_via_arl(arl)
            session = d.get_session()

            logger.debug('ARL session result: %s', session['logged_in'])

            time.sleep(sleep_timeout)
            sem.release()
            return session

        with concurrent.futures.ThreadPoolExecutor() as pool:
            arls = list(arls\
                .difference(set(validated.keys()))\
                .difference(set(invalidated.keys()))\
                .union(set(validated_expired.keys())))

            max_arls = max_arls if max_arls > 0 else len(arls)
            arls = arls[0:max_arls]

            tasks = [loop.run_in_executor(pool, deezer_login, arl) for arl in arls]
            sessions = await asyncio.gather(*tasks)

            for arl, session in zip(arls, sessions):
                if all((predicate(session) for predicate in validators)):
                    validated[arl] = {
                        'validated': str(now),
                        'expiry': str(now + timedelta(seconds=cache_expiry))
                    }
                else:
                    validated.pop(arl, None)
                    invalidated[arl] = {
                        'expiry': str(now + timedelta(days=30))
                    }

        logger.info(
            "Total ARLs validated: %d, Total ARLs invalidated: %d", 
            len(validated),
            len(invalidated)
        )

        with open(Validator.ValidatedPath, 'w', encoding="utf-8") as f:
            json.dump(validated, f, indent=2)
        with open(Validator.InvalidatedPath, 'w', encoding="utf-8") as f:
            json.dump(invalidated, f, indent=2)

        return validated

    @classmethod
    def fetch(cls, count: int):
        now = datetime.now()

        try:
            with open(Validator.ValidatedPath, 'r', encoding="utf-8") as f:
                validated = json.load(f)
                validated = {
                    arl: v
                    for arl, v in validated.items()
                    if datetime.fromisoformat(v['expiry']) > now
                }
        except FileNotFoundError:
            validated = {}

        return list(validated.keys())[0:count]

    @classmethod
    def clean(cls):
        if not os.path.isfile(Validator.ValidatedPath):
            logger.warning('No validated ARLs to clean')
        else:
            logger.debug('Deleting file %s', Validator.ValidatedPath)
            os.remove(Validator.ValidatedPath)
            logger.info('Wiped ARL validation cache')
