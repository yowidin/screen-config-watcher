from argparse import ArgumentParser

import logging
from typing import Optional


class Log:
    INSTANCE = None  # type: Optional[Log]
    LOGGER_NAME = 'scw'
    FORMAT_STRING = '[%(asctime)s][%(levelname)s][%(name)s] %(message)s'

    def __init__(self, level: int):
        self.formatter = logging.Formatter(Log.FORMAT_STRING)
        self.level = level

        self.logger = logging.getLogger(Log.LOGGER_NAME)
        self.logger.setLevel(level)
        self.logger.propagate = False

        commands_logger = logging.getLogger('obwsc')
        commands_logger.setLevel(level)
        commands_logger.propagate = False

        self._add_handler(self.logger, logging.StreamHandler())
        self._add_handler(commands_logger, logging.StreamHandler())

    def _add_handler(self, logger, handler):
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

    @staticmethod
    def add_args(parser: ArgumentParser):
        verbosity = parser.add_mutually_exclusive_group()
        verbosity.add_argument('-v', dest='info', action='store_true', help='Log info messages')
        verbosity.add_argument('-vv', dest='debug', action='store_true', help='Log debug messages')

    @staticmethod
    def setup(args):
        if args.info:
            level = logging.INFO
        elif args.debug:
            level = logging.DEBUG
        else:
            level = logging.ERROR

        if Log.INSTANCE is None:
            Log.INSTANCE = Log(level)
        else:
            raise RuntimeError('Logger already initialized')

    @staticmethod
    def disable_external_loggers():
        assert Log.INSTANCE is not None
        for log_name, log_obj in logging.Logger.manager.loggerDict.items():
            if not log_name.startswith(Log.LOGGER_NAME):
                log_obj.disabled = True

    @staticmethod
    def debug(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.debug(*args, **kwargs)

    @staticmethod
    def info(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.info(*args, **kwargs)

    @staticmethod
    def warning(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.warning(*args, **kwargs)

    @staticmethod
    def error(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.error(*args, **kwargs)

    @staticmethod
    def exception(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.exception(*args, **kwargs)

    @staticmethod
    def fatal(*args, **kwargs):
        assert Log.INSTANCE is not None
        Log.INSTANCE.logger.fatal(*args, **kwargs)
