import json

import cspark.sdk as Spark
from dotenv import load_dotenv


def retrieve_log(logs: Spark.History):
    call_id = 'uuid'
    response = logs.get(call_id)
    with open(f'{call_id}.json', 'w') as file:
        json.dump(response.data, file, indent=2)
        print(f'Detailed log for call ID {call_id} retrieved successfully 🎉')


def rehydrate(logs: Spark.History):
    response = logs.rehydrate('my-folder/my-service', call_id='uuid')
    with open('rehydrated.xlsx', 'wb') as file:
        file.write(response.buffer)  # response.data contains the download URL.
        print(f'file rehydrated successfully 🎉')


def download(logs: Spark.History):
    response = logs.download(
        folder='my-folder',
        service='my-service',
        call_ids=['uuid1', 'uuid2', 'uuid3'],
        type='json',
        max_retries=5,
        retry_interval=3,
    )
    with open('my-log-history.zip', 'wb') as file:
        file.write(response.buffer)  # response.data contains the download URL.
        print(f'log file downloaded successfully 🎉')


if __name__ == '__main__':
    load_dotenv()

    try:
        with Spark.Client(timeout=90_000).logs as logs:
            retrieve_log(logs)
            rehydrate(logs)
            download(logs)
    except Spark.SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
