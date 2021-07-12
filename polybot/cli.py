"""Command line interface for polybot"""

import re
import logging
import importlib
from argparse import ArgumentParser, Namespace

import requests
import yaml

from polybot.planning import OptimizationProblem
from polybot.version import __version__
from polybot.models import Sample
from polybot.config import settings

logger = logging.getLogger(__name__)


def upload(args: Namespace):
    """Upload a file"""

    # Read in the file
    sample = Sample.parse_file(args.file)
    logger.info(f'Read in sample {sample.id} from {args.file}')

    # Make the upload package
    url = f'{args.url}/ingest'
    logger.info(f'Uploading file to {url}')
    if args.dry_run:
        logger.warning('Not submitting request for a dry run.')
        return

    result = requests.post(url, json=sample.dict())
    logger.info(f'Request status: {result.status_code}')
    if result.status_code == 200:
        print(result.json())
    else:
        print(f'Failed with a status: {result.json()}')


def launch_planner(args: Namespace):
    """Launch a planning service"""

    # Load in the optimization description
    if args.opt_config.endswith('.yaml') or args.opt_config.endswith('.yml'):
        with open(args.opt_config) as fp:
            opt_info = OptimizationProblem.parse_obj(yaml.load(fp, Loader=yaml.SafeLoader))
    else:
        opt_info = OptimizationProblem.parse_file(args.opt_config)

    logger.info(f'Loaded optimization configuration from {args.opt_config}')

    # Retrieve the target class
    if re.match(r'(?:\w+\.?)+\w:\w+', args.planning_class) is None:
        raise ValueError(f'Planning class name "{args.planning_class}" not in required format: module.path:ClassName')
    module_name, class_name = args.planning_class.split(":")
    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name)
    logger.info(f'Loaded planning class: {cls}')

    # Start the planner process
    client_q = settings.make_client_queue()
    planner = cls(client_q, opt_info, **opt_info.planner_options, daemon=True)
    planner.start()  # Run in a separate thread

    # Wait until the planner finishes or timeout is reached
    try:
        planner.join(timeout=args.timeout)
    finally:
        planner.done.set()  # Tells the planner to shutdown


def create_parser() -> ArgumentParser:
    """Create the argument parser for the CLI tool"""

    parser = ArgumentParser()
    parser.add_argument('--verbose', action='store_true', help='Turn on logging')
    sub_parser = parser.add_subparsers(title='Subcommands', required=True,
                                       help='Available subcommands for polybot')

    # Create the version command
    version_parser = sub_parser.add_parser('version', help='Print the version number')
    version_parser.set_defaults(function=lambda x: print(f'polybot version: {__version__}'))

    # Create the upload functionality
    upload_parser = sub_parser.add_parser('upload', help='Upload files to polybot')
    upload_parser.add_argument('--dry-run', action='store_true',
                               help='Ready but do not upload file')
    upload_parser.add_argument('--url', default='http://localhost:8152/', help='URL of the web service')
    upload_parser.add_argument('file', help='Path to the file to upload', type=str)
    upload_parser.set_defaults(function=upload)

    # Launch the planning service
    planner_parser = sub_parser.add_parser('planner', help='Launch the planning service')
    planner_parser.add_argument('--planning-class', '-p', default='polybot.planning:RandomPlanner',
                                help='Class defining the planning algorithm in format: module.path:ClassName')
    planner_parser.add_argument('--timeout', default=None, type=float, help='Maximum runtime for the planning service. '
                                                                            'Used for debugging.')
    planner_parser.add_argument("opt_config", help="Path to the optimization configuration file.")
    planner_parser.set_defaults(function=launch_planner)
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
    args.host_url = settings.robot_url
    logger.info(f'Connecting to server at {args.host_url}')

    # Act on the parser
    args.function(args)
