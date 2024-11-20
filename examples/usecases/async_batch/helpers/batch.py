import os
import signal
import sys
import time

import cspark.sdk as Spark
from dotenv import load_dotenv

from .chunk import ChunkGenerator, ChunkProcessor
from .config import METADATA, Config, logger
from .threads import run_threads


def create_output_dir(directory):
    """Creates the output directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def process_chunks(pipeline, processor):
    """Processes the CSV chunks using a single ChunkGenerator for the input directory."""
    start_time = time.time()

    generator = ChunkGenerator(Config.INPUT_DIR)

    run_threads(
        pipeline=pipeline,
        chunk_generator=generator,
        chunk_processor=processor,
        threads_up=1,
        threads_down=1,
        target=0.9,
        delay=1.5,
        verbose=True,
        logging=False,
    )

    logger.debug('Done processing all records')

    if not processor.is_empty:
        processor.save()

    return time.time() - start_time


def run_batch():
    """Runs the batch processing logic."""
    signal.signal(signal.SIGINT, lambda s, f: handle_interrupt(s, f, pipeline))

    load_dotenv()
    spark = Spark.Client(logger={'context': 'Async Batch'})

    pipeline = None
    try:
        with spark.batches as batches:
            batch = batches.create(Config.SERVICE_URI, **METADATA).data
            pipeline = batches.of(batch['id'])  # type: ignore
            logger.debug(f'Creating batch with ID "{pipeline.batch_id}"...')

            processor = ChunkProcessor(False, Config.OUTPUT_DIR)
            elapsed_time = process_chunks(pipeline, processor)

            status = pipeline.get_status().data
            avg = status['records_completed'] / elapsed_time  # type: ignore
            logger.debug(f'{avg} records per second (on average)')

    except Exception as exc:
        logger.error(exc)
        if pipeline and pipeline.state == 'open':
            logger.debug('Canceling the pipeline due to an error...')
            pipeline.cancel()
    finally:
        if pipeline and pipeline.state == 'open':
            pipeline.close()


def handle_interrupt(signal, frame, pipeline):  # noqa: ARG001
    """Handles the Ctrl + C (SIGINT) signal."""
    logger.debug('\nCtrl + C detected. Attempting to cancel the pipeline...')
    if pipeline:
        pipeline.cancel()
        logger.debug('Pipeline canceled.')
    sys.exit(0)
