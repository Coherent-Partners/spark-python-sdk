import io
import sys

import cspark.sdk as Spark
from main import exp, imp

logger = Spark.get_logger()


def main():
    if len(sys.argv) != 5:
        logger.error('Usage: python impex.py <FROM_SETTINGS> <FROM_TOKEN> <TO_SETTINGS> <TO_OAUTH>')
        sys.exit(1)

    FROM_SPARK_SETTINGS, FROM_BEARER_TOKEN, TO_SPARK_SETTINGS, TO_OAUTH_CREDS = sys.argv[1:]

    try:
        exported = exp(FROM_SPARK_SETTINGS, FROM_BEARER_TOKEN)
        imp(TO_SPARK_SETTINGS, TO_OAUTH_CREDS, file=io.BytesIO(exported[0].buffer))
    except Spark.SparkError as err:
        logger.error(err.message)
        if err.cause:
            logger.error(err.details)
    except Exception as exc:
        logger.critical(f'Unknown error: {exc}')


if __name__ == '__main__':
    main()
