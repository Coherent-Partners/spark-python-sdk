#!/usr/bin/env -S rye run python
import json
import time
from typing import Any, Dict, cast

import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()


def describe(batches: Spark.Batches):
    print(batches.describe().data)


def create_and_run(batches: Spark.Batches):
    def print_status(status, msg):
        a, b, c = status['records_available'], status['record_submitted'], status['records_completed']
        print(f'{msg} :: {a} of {b} records submitted ({c} processed)')

    chunks = []
    with open('path/to/data.json', 'r') as f:
        data = json.load(f)
        chunks = Spark.create_chunks(data, chunk_size=200)

    if len(chunks) == 0:
        print('no data to process')
        return

    batch = batches.create('my-folder/my-service')
    print('batch created', batch.data)

    if not isinstance(batch.data, dict):
        return

    pipeline = batches.of(batch.data['id'])
    try:
        submission = pipeline.push(chunks=chunks)
        print('submission data', submission.data)
        time.sleep(1)

        status = cast(Dict[str, Any], pipeline.get_status().data)
        print_status(status, 'first status check')

        while status['records_completed'] < status['record_submitted']:
            status = cast(Dict[str, Any], pipeline.get_status().data)
            print_status(status, 'subsequent status check')

            if status['records_available'] > 0:
                result = pipeline.pull()
                print('result data', result.data)

            time.sleep(2)
    except Exception as e:
        print(e)
    finally:
        state = pipeline.dispose()
        print(state.data)
        print('done!')


if __name__ == '__main__':
    spark = Spark.Client()
    with spark.batches as b:
        describe(b)
        create_and_run(b)
