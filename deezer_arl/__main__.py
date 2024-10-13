import asyncio
import argparse
import logging
import itertools
import re

from deezer_arl import Scraper, Validator
from deezer_arl.provider import Providers, Manager as ProviderManager
from deezer_arl.consumer import Consumers

logging.basicConfig(
    level=logging.INFO,
    format= '[%(asctime)s]:%(name)s:%(levelname)s:%(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(
        prog='deezer-arl',
        description='Locate and validate Deezer ARLs and use them however you like!'
    )

    parser.add_argument('-v', '--verbose', action='store_true')
    subparsers = parser.add_subparsers(required=True, dest='command')

    parser_pull = subparsers.add_parser('pull', help='Scrape and validate ARLs')
    parser_pull_quality_group = parser_pull.add_mutually_exclusive_group()
    parser_pull_quality_group.add_argument(
        '-hq', '--requires-can-stream-hq', 
        action='store_true',
        help='Only consider HQ streaming accounts as valid'
    )
    parser_pull_quality_group.add_argument(
        '-lossless', '--requires-can-stream-lossless', 
        action='store_true',
        help='Only consider lossless streaming accounts as valid'
    )
    parser_pull.add_argument(
        '-C', '--requires-country', 
        nargs='*',
        type=list,
        help='Only consider accounts from specific countries as valid'
    )
    parser_pull.add_argument(
        '--requests-max-concurrent', 
        default=5,
        type=int,
        help='Limit max concurrent validation requests'
    )
    parser_pull.add_argument(
        '--requests-sleep-timeout',
        default=5,
        type=int,
        help='Delay in seconds between each batch of validation requests'
    )
    parser_pull.add_argument(
        '--cache-expiry',
        default=43200,
        type=int,
        help='Number of seconds ARLs remain validated'
    )
    parser_pull.add_argument(
        '--max-arls',
        default=0,
        type=int,
        help='Set the maximum number of ARLs to validate'
    )

    parser_fetch = subparsers.add_parser('fetch', help='Fetch validated ARL')
    parser_fetch.add_argument(
        '-c', '--count', 
        default=1,
        type=int,
        help="Number of unique ARLs to fetch"
    )
    parser_fetch.add_argument(
        '-o', '--output', 
        type=str,
        action='append',
        help='Output ARLs to file instead of the console'
    )

    parser_consume = subparsers.add_parser('consume', help='Specify an ARL consumer to use')
    parser_consume.add_argument(
        '-c', '--count', 
        default=1,
        type=int,
        help="Number of unique ARLs to fetch"
    )
    parser_consume_type_subparser = parser_consume.add_subparsers(
        required=True,
        dest='consumer_type'
    )
    for option, consumer in Consumers.items():
        parser_consume_type_subparser.add_parser(
            option,
            parents=[consumer.parser()],
            add_help=False
        )

    subparsers.add_parser('clean', help='Clean validated ARLs')

    parser_provider = subparsers.add_parser('provider', help='Manage ARL providers')
    parser_provider_subparsers = parser_provider.add_subparsers(
        required=True,
        dest='provider_command'
    )

    parser_provider_add = parser_provider_subparsers.add_parser(
        'add', 
        help='Add a new ARL provider'
    )
    parser_provider_add_subparsers = parser_provider_add.add_subparsers(
        required=True,
        dest='provider_type'
    )
    for provider in Providers:
        parser_provider_add_subparsers.add_parser(
            provider.__name__,
            parents=[provider.parser()],
            add_help=False
        )

    parser_provider_remove = parser_provider_subparsers.add_parser(
        'remove', 
        help='Remove existing ARL provider'
    )
    parser_provider_remove.add_argument('index', type=int, help='Index of provider to remove')

    parser_provider_subparsers.add_parser('list', help='List existing ARL providers')

    args = parser.parse_args()

    if args.verbose:
        logging.root.setLevel(logging.DEBUG)

    if args.command == 'clean':
        Validator.clean()
        logger.info('Wiped ARL validation cache')

    if args.command == 'consume':
        arls = Validator.fetch(args.count)

        consumer_class = Consumers[args.consumer_type]
        consumer_type_parser = parser_consume_type_subparser.choices[args.consumer_type]
        consumer_type_args, _ = consumer_type_parser.parse_known_args()

        consumer = consumer_class(**vars(consumer_type_args))
        await consumer.consume(arls)

    if args.command == 'fetch':
        arls = Validator.fetch(args.count)

        if not args.output and not args.update:
            for arl in arls:
                print(arl)

        if args.output:
            for file in args.output:
                with open(file, 'w', encoding="utf-8") as f:
                    f.writelines(arls)

    if args.command == 'pull':
        m = ProviderManager()
        arls = await Scraper.scrape(m.get())
        await Validator.validate(arls, [validator for validator, enabled in [
                (Validator.session_logged_in, True),
                (Validator.session_can_stream_hq, args.requires_can_stream_hq),
                (Validator.session_can_stream_lossless, args.requires_can_stream_lossless),
                (Validator.session_country(args.requires_country), bool(args.requires_country))
            ] if enabled],
            max_requests=args.requests_max_concurrent,
            sleep_timeout=args.requests_sleep_timeout,
            cache_expiry=args.cache_expiry,
            max_arls=args.max_arls
        )

    if args.command == 'provider':
        m = ProviderManager()

        if args.provider_command == 'add':

            provider_parser = parser_provider_add_subparsers.choices[args.provider_type]
            provider_args, _ = provider_parser.parse_known_args()

            await m.add(args.provider_type, **vars(provider_args))

        if args.provider_command == 'remove':
            m.remove(args.index)

        if args.provider_command == 'list':
            for i, provider in enumerate(m.get()):
                print(f'{i}. {provider}')

if __name__ == '__main__':
    asyncio.run(main())
