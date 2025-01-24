# type: ignore
import json
import time

import cspark.sdk as Spark
from dotenv import load_dotenv


def describe(batches: Spark.Batches):
    print(batches.describe().data)


def create_and_run(batches: Spark.Batches):
    logger = Spark.get_logger(context='Async Batch', datefmt='%Y-%m-%d %H:%M:%S')

    def log_status(status, msg='status check'):
        a, b, c = status['records_available'], status['record_submitted'], status['records_completed']
        logger.info(f'{msg} :: {a} of {b} records submitted ({c} processed)')

    chunks, results = [], []
    with open('path/to/inputs.json', 'r') as f:
        data = json.load(f)
        chunks = Spark.create_chunks(data, chunk_size=150)

    if len(chunks) == 0:
        logger.warning('no input data to process')
        return

    pipeline = None
    try:
        batch = batches.create('my-folder/my-service')
        pipeline = batches.of(batch.data['id'])
        pipeline.push(chunks=chunks)
        time.sleep(5)

        status = pipeline.get_status().data

        while status['records_completed'] < status['record_submitted']:
            status = pipeline.get_status().data
            log_status(status)

            if status['records_available'] > 0:
                result = pipeline.pull()
                log_status(result.data['status'], 'data retrieval status')
                results.extend(r['outputs'] for r in result.data['data'])

            time.sleep(2)
    except Spark.SparkError as err:
        logger.error(err.message)
        logger.info(err.details)
    except Exception as exc:
        logger.critical(f'Unknown error: {exc}')
    finally:
        if pipeline:
            pipeline.dispose()

        with open('path/to/outputs.json', 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f'total processed outputs: {len(results)}\nDone! 🎉')


if __name__ == '__main__':
    load_dotenv()

    spark = Spark.Client(timeout=90_000, logger={'context': 'Async Batch'})
    with spark.batches as batches:
        describe(batches)
        create_and_run(batches)
