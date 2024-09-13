import logging

# { verbose: 0, debug: 1, log: 2, warn: 3, error: 4, fatal: 5, none: 6 };
DEFAULT_LOG_FORMAT = '[%(name)s] %(asctime)s %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%m/%d/%Y, %I:%M:%S %p'


def get_logger(
    name: str,
    disable: bool = False,
    level: int = logging.DEBUG,
    format: str = DEFAULT_LOG_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    # disable existing loggers
    logging.getLogger('httpx').disabled = True

    # prepare main logger
    logger = logging.getLogger(name)
    logger.setLevel(disable and logging.CRITICAL or level)

    if not logger.handlers:  # Avoid adding multiple handlers
        formatter = logging.Formatter(format, datefmt)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
