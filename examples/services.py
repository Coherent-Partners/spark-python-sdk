#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()


def execute(services: Spark.Services):
    inputs = {}  # inputs data
    response = services.execute('my-folder/my-service', inputs=inputs)
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


if __name__ == '__main__':
    spark = Spark.Client()
    with spark.services as services:
        execute(services)
        get_schema(services)
        get_metadata(services)
        get_versions(services)
