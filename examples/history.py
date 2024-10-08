import cspark.sdk as Spark
from dotenv import load_dotenv


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

    spark = Spark.Client(timeout=90_000)
    try:
        with spark.logs as logs:
            # rehydrate(logs)
            download(logs)
    except Spark.SparkSdkError as err:
        print(err.message)
        if err.cause:
            print(err.details)
    except Spark.SparkApiError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
