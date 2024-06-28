#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()


def execute_sync(services: Spark.Services):
    inputs = []  # inputs data
    response = services.execute('my-folder/my-service', inputs=inputs)
    print(response.data)


if __name__ == '__main__':
    spark = Spark.Client()
    with spark.services as services:
        execute_sync(services)
