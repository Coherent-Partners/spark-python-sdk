#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv


def rehydrate(logs: Spark.History):
    response = logs.rehydrate('my-folder/my-service', call_id='uuid')
    with open('rehydrated.xlsx', 'wb') as file:
        file.write(response.buffer)  # response.data contains the download URL.
        print(f'file rehydrated successfully 🎉')


if __name__ == '__main__':
    load_dotenv()

    spark = Spark.Client()
    with spark.logs as logs:
        rehydrate(logs)
