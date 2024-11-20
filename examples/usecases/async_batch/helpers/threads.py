import csv
import threading
import time
from multiprocessing import Queue
from queue import Empty

from .config import logger


class ThreadController:
    def __init__(self):
        self.total_chunks = 0
        self.enqueuing = True
        self._counters = {
            'blocks_enqueued': 0,
            'blocks_uploaded': 0,
            'chunks_downloaded': 0,
            'chunks_processed': 0,
        }
        self._locks = {name: threading.RLock() for name in self._counters}
        self._locks['total_chunks'] = threading.RLock()

    def done_enqueuing(self):
        logger.debug('set done_enqueuing')
        self.enqueuing = False

    def is_done_enqueuing(self):
        return not self.enqueuing

    def increment(self, counter_name):
        """Increments the counter specified by `counter_name`."""
        with self._locks[counter_name]:
            self._counters[counter_name] += 1

    def modify_total_chunks(self, change):
        with self._locks['total_chunks']:
            self.total_chunks += change

    def get(self, counter_name):
        """Returns the value of the counter specified by `counter_name`."""
        return self._counters[counter_name] if counter_name in self._counters else getattr(self, counter_name)


def log_pipeline_status(pipeline, filepath, controller, interval=6):
    """Logs pipeline status to a CSV file at specified intervals."""
    logs = [['Batch ID', 'Chunks Processed', 'Time']]
    last_records = 0
    last_time = time.time()

    while not controller.is_done_enqueuing() or controller.get('chunks_processed') < controller.get('total_chunks'):
        status = pipeline.get_status().data
        current_time = time.time()

        logs.append([pipeline.batch_id, status['records_completed'] - last_records, current_time - last_time])  # type: ignore
        last_records = status['records_completed']
        last_time = current_time

        time.sleep(interval)

    with open(f'{filepath}{int(time.time())}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(logs)


def enqueue_chunks(upload_queue, chunk_generator, controller, verbose=False):
    """Enqueues chunks from the generator into the upload queue."""
    while not controller.is_done_enqueuing():
        next_chunks, done = chunk_generator.get_next()
        if len(next_chunks['chunks']) > 0:
            controller.modify_total_chunks(len(next_chunks['chunks']))
            upload_queue.put(next_chunks)
            controller.increment('blocks_enqueued')
        if done:
            controller.done_enqueuing()

    if verbose:
        logger.debug('Enqueue thread complete')


def upload_chunks(pipeline, upload_queue, controller, target=0.5, delay=2, verbose=False):
    """Uploads chunks from the upload queue to the pipeline."""
    while not controller.is_done_enqueuing() or controller.get('blocks_uploaded') < controller.get('blocks_enqueued'):
        if upload_queue.empty():
            time.sleep(delay)
        else:
            if not upload_to_pipeline(pipeline, upload_queue, controller, target, verbose):
                time.sleep(delay)


def upload_to_pipeline(pipeline, upload_queue, controller, target, verbose):
    """Uploads chunks and manages cooldown if buffer exceeds the target."""
    status = pipeline.get_status().data
    if (
        status
        and status['input_buffer_used_bytes']
        / (status['input_buffer_remaining_bytes'] + status['input_buffer_used_bytes'])
        > target
    ):
        return False

    next_chunks = None
    try:
        next_chunks = upload_queue.get(timeout=1)
        status = pipeline.push(chunks=next_chunks['chunks']).data
        controller.increment('blocks_uploaded')
        if verbose:
            logger.debug(f'Upload -> {status}')
        return True
    except Empty:
        return False
    except Exception:
        upload_queue.put(next_chunks)
        return False


def download_chunks(pipeline, download_queue, controller, delay=2, verbose=False):
    """Downloads chunks from the pipeline."""
    while not (
        controller.is_done_enqueuing() and controller.get('chunks_downloaded') == controller.get('total_chunks')
    ):
        try:
            response = pipeline.pull().data
            if response and isinstance(response['data'], list):
                for chunk in response['data']:
                    download_queue.put(chunk)
                    controller.increment('chunks_downloaded')

            if verbose:
                logger.debug(f'Downloaded chunks. Remaining: {response["status"]["chunks_available"]}')
            time.sleep(delay)
        except Exception:
            time.sleep(delay)


def process_chunks(download_queue, chunk_processor, controller, verbose=False):
    """Processes chunks from the download queue."""
    while not controller.is_done_enqueuing() or controller.get('chunks_processed') < controller.get('total_chunks'):
        chunk = download_queue.get()
        chunk_processor.process(chunk)
        controller.increment('chunks_processed')

    if verbose:
        logger.debug('Processing complete')


def run_threads(
    pipeline,
    chunk_generator,
    chunk_processor,
    threads_up,
    threads_down,
    target=0.5,
    delay=2.0,
    verbose=False,
    logging=False,
    log_path='',
):
    """Runs the enqueuing, uploading, downloading, and processing threads."""
    start_time = time.time()
    controller = ThreadController()
    upload_queue = Queue()
    download_queue = Queue()

    # Create threads for each operation
    threads = {
        'enqueue': threading.Thread(target=enqueue_chunks, args=(upload_queue, chunk_generator, controller, verbose)),
        'upload': [
            threading.Thread(target=upload_chunks, args=(pipeline, upload_queue, controller, target, delay, verbose))
            for _ in range(threads_up)
        ],
        'download': [
            threading.Thread(target=download_chunks, args=(pipeline, download_queue, controller, delay, verbose))
            for _ in range(threads_down)
        ],
        'process': threading.Thread(target=process_chunks, args=(download_queue, chunk_processor, controller, verbose)),
    }

    if logging:
        threads['logging'] = threading.Thread(target=log_pipeline_status, args=(pipeline, log_path, controller))

    # Start all threads
    threads['enqueue'].start()
    for t_up in threads['upload']:
        t_up.start()
    for t_down in threads['download']:
        t_down.start()
    threads['process'].start()
    if logging:
        threads['logging'].start()

    # Wait for threads to finish
    threads['enqueue'].join()
    for t_up in threads['upload']:
        t_up.join()
    for t_down in threads['download']:
        t_down.join()
    threads['process'].join()
    if logging:
        threads['logging'].join()

    if verbose:
        elapsed_time = time.time() - start_time
        logger.debug(f'Run completed in {elapsed_time:.2f} seconds')
