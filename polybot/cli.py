"""Command line interface for polybot"""

import logging
from argparse import ArgumentParser, Namespace

import requests

from polybot.version import __version__
from polybot.models import Sample

logger = logging.getLogger(__name__)


def upload(args: Namespace):
    """Upload a file"""

    # Read in the file
    sample = Sample.parse_file(args.file)
    logger.info(f'Read in sample {sample.id} from {args.file}')

    # Make the upload package
    url = f'{args.host_url}/ingest'
    logger.info(f'Uploading file to {url}')
    if args.dry_run:
        logger.warning('Not submitting request for a dry run.')
        return

    result = requests.post(url, json=sample.json())
    logger.info(f'Request status: {result.status_code}')
    if result.status_code == 200:
        print(result.json())
    else:
        print(f'Failed with a status: {result.json()}')


def create_parser() -> ArgumentParser:
    """Create the argument parser for the CLI tool"""

    parser = ArgumentParser()
    parser.add_argument('--version', action='store_true', help='Print version number and exit')
    parser.add_argument('--verbose', action='store_true', help='Turn on logging')
    parser.add_argument('--host', help='URL of polybot service', type=str, default='localhost')
    parser.add_argument('--port', help='Port of polybot service', type=int, default=5000)
    sub_parser = parser.add_subparsers(title='Subcommands',
                                       help='Available subcommands for polybot')

    # Create the upload functionality
    upload_parser = sub_parser.add_parser('upload', help='Upload files to polybot')
    upload_parser.add_argument('--dry-run', action='store_true',
                               help='Ready but do not upload file')
    upload_parser.add_argument('file', help='Path to the file to upload', type=str)
    upload_parser.set_defaults(function=upload)
    return parser


def main(args=None):
    """Run the command line interface"""

    # Make and run the parser
    parser = create_parser()
    args = parser.parse_args(args)

    # Make the logger if desired
    if args.verbose:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
    logger.info(f'Running polybot CLI app. Version: {__version__}')
    args.host_url = f'http://{args.host}:{args.port}'
    logger.info(f'Connecting to server at {args.host_url}')

    # Act on the parser
    if args.version:
        print(f'polybot version: {__version__}')
        return
    args.function(args)
