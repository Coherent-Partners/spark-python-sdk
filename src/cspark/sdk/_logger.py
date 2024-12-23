import logging
from dataclasses import dataclass
from typing import Any, Mapping, Union

from ._constants import DEFAULT_LOGGER_DATEFMT
from ._version import sdk_logger

__all__ = ['get_logger', 'LoggerOptions']


@dataclass
class LoggerOptions:
    context: str = sdk_logger
    disabled: bool = False
    level: int = logging.DEBUG
    datefmt: str = DEFAULT_LOGGER_DATEFMT
    colorful: bool = True
    timestamp: bool = True

    @staticmethod
    def when(options: Union[bool, Mapping[str, Any], 'LoggerOptions']) -> 'LoggerOptions':
        if isinstance(options, bool):
            return LoggerOptions(disabled=not options)
        if isinstance(options, Mapping):
            return LoggerOptions(**options)
        return options


class ColorfulFormatter(logging.Formatter):
    def __init__(self, *, datefmt: str, colorful: bool = True, timestamp: bool = True) -> None:
        super().__init__(datefmt=datefmt)
        self.colorful = colorful
        self.timestamp = timestamp

    def format(self, record: logging.LogRecord) -> str:
        timestamp = '%(asctime)s' if self.timestamp else ''
        if self.colorful:
            colored_heading = '\x1b[38;5;3m[%(name)s]\x1b[39m'  # orange
            colored_timestamp = f'\x1b[34m{timestamp}\x1b[39m'  # blue
            colored_level_and_msg = f'{self.color_by_level(record.levelno, "%(levelname)s - %(message)s")}'
            formatted_msg = f'{colored_heading} {colored_timestamp} {colored_level_and_msg}'
        else:
            formatted_msg = f'[%(name)s] {timestamp} %(levelname)s - %(message)s'

        record.levelname = record.levelname.rjust(8, ' ')  # right align levelname
        formatter = logging.Formatter(formatted_msg, datefmt=self.datefmt)
        return formatter.format(record)

    def color_by_level(self, level: int, msg: str) -> str:
        if level == logging.DEBUG:
            return f'\x1b[95m{msg}\x1b[39m'  # magenta
        elif level == logging.WARNING:
            return f'\x1b[93m{msg}\x1b[39m'  # yellow
        elif level == logging.ERROR:
            return f'\x1b[31m{msg}\x1b[39m'  # red
        elif level == logging.INFO:
            return f'\x1b[32m{msg}\x1b[39m'  # green
        elif level == logging.CRITICAL:
            return f'\x1b[1m{msg}\x1b[0m'  # bold
        else:
            return f'\x1b[32m{msg}\x1b[39m'  # green


def get_logger(
    context: str = sdk_logger,
    disabled: bool = False,
    level: int = logging.DEBUG,
    datefmt: str = DEFAULT_LOGGER_DATEFMT,
    colorful: bool = True,
    timestamp: bool = True,
) -> logging.Logger:
    logging.getLogger('httpx').disabled = True  # disable existing loggers

    logger = logging.getLogger(context)
    logger.setLevel(disabled and logging.CRITICAL or level)

    if not logger.handlers:
        formatter = ColorfulFormatter(datefmt=datefmt, colorful=colorful, timestamp=timestamp)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
