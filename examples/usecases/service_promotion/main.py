import io
import json
import typing

import cspark.sdk as Spark

FROM_SPARK_SETTINGS = '{"env":"uat.us","tenant":"my-tenant","timeout":90000,"max_retries":20,"retry_interval":3,"services":["source-folder/my-service"]}'
FROM_BEARER_TOKEN = 'uat bearer token'
TO_SPARK_SETTINGS = '{"env":"us","tenant":"my-tenant","timeout":90000,"max_retries":40,"retry_interval":3,"services":{"source":"source-folder/my-service","target":"target-folder/my-service"}}'
TO_OAUTH_CREDS = '{"client_id":"my-client-id","client_secret":"my-client-secret"}'
CICD_HANDLER = Spark.__title__  # GitHub Actions, Jenkins, etc.
FILE_PATH = 'package.zip'

# ---------------- You do NOT need to modify below this line ----------------
logger = Spark.get_logger()


def exp(settings: str, auth: str):
    options = json.loads(settings)
    services = options.pop('services')
    spark = Spark.Client(**options, token=auth)

    downloadables = spark.impex.export(services=services, source_system=CICD_HANDLER)
    total = len(downloadables)
    if total == 0:
        raise Spark.SparkError('no files to download')
    logger.info(f'✅ {total} service(s) exported')

    return downloadables


def imp(settings: str, auth: str, file: typing.BinaryIO):
    options = json.loads(settings)
    destination = options.pop('services')
    spark = Spark.Client(**options, oauth=json.loads(auth))

    imported = spark.impex.imp(destination, file=file, source_system=CICD_HANDLER)
    outputs = imported.data.get('outputs', {}) if isinstance(imported.data, dict) else {}
    total = len(outputs['services']) if 'services' in outputs else 0
    if total == 0:
        raise Spark.SparkError('no services imported')
    logger.info(f'✅ {total} service(s) imported')

    return imported


def main():
    try:
        exported = exp(FROM_SPARK_SETTINGS, FROM_BEARER_TOKEN)

        with open(FILE_PATH, 'wb') as file:  # save exported file to disk for inspection
            file.write(exported[0].buffer)
            logger.info(f'🎉 exported service(s) downloaded successfully as {FILE_PATH}')

        imp(TO_SPARK_SETTINGS, TO_OAUTH_CREDS, file=io.BytesIO(exported[0].buffer))
    except Spark.SparkError as err:
        logger.error(err.message)
        if err.cause:
            logger.error(err.details)
    except Exception as exc:
        logger.critical(f'Unknown error: {exc}')


if __name__ == '__main__':
    main()
