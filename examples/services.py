import json

import cspark.sdk as Spark
from dotenv import load_dotenv


def create(services: Spark.Services):
    response = services.create(
        name='service-name',
        folder='my-folder',
        track_user=True,
        file=open('my-service.xlsx', 'rb'),
        max_retries=10,
        retry_interval=3,
    )
    print(json.dumps(response['publication'], indent=2))


def execute(services: Spark.Services):
    inputs = {}  # inputs data
    response = services.execute('my-folder/my-service', inputs=inputs)
    print(response.data)


def transform(services: Spark.Services):
    inputs = {}  # inputs data
    response = services.transform('my-folder/my-service', inputs=inputs, using='my-transform', encoding='gzip')
    print(response.data)


def get_schema(services: Spark.Services):
    response = services.get_schema('my-folder/my-service')
    print(response.data)


def get_metadata(services: Spark.Services):
    response = services.get_metadata('my-folder/my-service')
    print(response.data)


def get_versions(services: Spark.Services):
    response = services.get_versions('my-folder/my-service')
    print(response.data)


def download(services: Spark.Services):
    response = services.download('my-folder/my-service', type='configured')
    with open('my-excel-file.xlsx', 'wb') as file:
        file.write(response.buffer)
        print(f'file downloaded successfully 🎉')


def recompile(services: Spark.Services):
    response = services.recompile('my-folder/my-service')
    print(response.data)


def validate(services: Spark.Services):
    inputs = {}  # inputs data to validate
    response = services.validate('my-folder/my-service', inputs=inputs, validation_type='dynamic')
    print(response.data)


def delete(services: Spark.Services):
    response = services.delete('my-folder/my-service')
    print(response.data)


if __name__ == '__main__':
    load_dotenv()

    try:
        spark = Spark.Client()
        with spark.services as services:
            create(services)
            execute(services)
            transform(services)
            get_schema(services)
            get_metadata(services)
            get_versions(services)
            download(services)
            recompile(services)
            validate(services)
            delete(services)
    except Spark.SparkSdkError as err:
        print(err.message)
        if err.cause:
            print(err.details)
    except Spark.SparkApiError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(exc)
