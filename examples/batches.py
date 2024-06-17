#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()


def execute_sync(batches: Spark.Batches):
    inputs = []  # inputs data
    response = batches.execute('my-folder/my-service', inputs=inputs)
    print(response.data)


if __name__ == '__main__':
    spark = Spark.Client()
    with spark.batches as batches:
        execute_sync(batches)
