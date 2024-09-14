#!/usr/bin/env -S rye run python
from typing import cast

import cspark.sdk as Spark
from dotenv import load_dotenv


def print_logs():
    logger = Spark.get_logger(context='Demo')
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')
    logger.critical('critical message')


def retrieve_token():
    load_dotenv()

    spark = Spark.Client()
    oauth = cast(Spark.OAuth, spark.config.auth.oauth)
    oauth.retrieve_token(spark.config)  # also return `AccessToken` object.
    print(f'access token: {oauth.access_token}')


if __name__ == '__main__':
    retrieve_token()
    print_logs()
