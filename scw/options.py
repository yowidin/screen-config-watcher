from argparse import ArgumentParser
from typing import Callable, Optional, List

import os
import sys

from scw.log import Log
from scw.config import Config


class Options:
    def __init__(self, dry_run: bool, config: Config):
        self.dry_run = dry_run
        self.config = config

    @staticmethod
    def _get_default_working_dir() -> str:
        result = os.path.dirname(sys.argv[0])

        # Handle the case where we are compiled into a standalone package
        if sys.platform == 'darwin' and 'Contents/MacOS' in result:
            # We are inside an macOS bundle
            result = os.path.abspath(os.path.join(result, '..', '..', '..'))
        else:
            result = os.getcwd()

        return result

    @staticmethod
    def parse(name: str, extra_args_fn: Optional[Callable[[ArgumentParser], None]] = None,
              cmd_args: Optional[List[str]] = None):
        parser = ArgumentParser(name)

        Log.add_args(parser)

        parser.add_argument('--config', '-c',
                            default=os.path.join(Options._get_default_working_dir(), 'config.toml'),
                            required=False, help='Path to the TOML configuration file')
        parser.add_argument('--dry-run', '-d', action='store_true', required=False,
                            help="Don't actually change anything (useful for preparing the presets, use together "
                                 "with -vv).")

        if extra_args_fn is not None:
            extra_args_fn(parser)

        args = parser.parse_args(args=cmd_args)

        Log.setup(args)

        if os.path.exists(args.config) and os.path.isfile(args.config):
            config = Config.load_from_file(args.config)
        else:
            raise RuntimeError(f'Configuration file not found: {args.config}')

        return Options(args.dry_run, config), args
