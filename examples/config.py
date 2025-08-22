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


def check_health(env='uat.us'):
    response = Spark.Client.health_check(env)
    print(response.data)


def fetch_platform_config():
    load_dotenv()  # load tenant credentials from .env file.

    print(Spark.Config().get())


def test_extended_resource():
    config = Spark.Config()  # same as client options.
    with ExtendedResource(config) as resource:
        response = resource.fetch_config()
        print(response.data)


class ExtendedResource(Spark.ApiResource):
    def fetch_config(self):
        endpoint = 'config/GetAllSparkConfiguration'
        url = Spark.Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)
        self.logger.info(f'fetching Spark configurations...')

        return self.request(url, method='GET')


if __name__ == '__main__':
    try:
        retrieve_token()
        print_logs()
        check_health()
        fetch_platform_config()
        test_extended_resource()
    except Spark.SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
