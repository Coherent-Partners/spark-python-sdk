import logging
import os

import cspark.sdk as Spark

logging.basicConfig(filename='console.log', filemode='w', format=Spark.DEFAULT_LOGGER_FORMAT)
logger = Spark.get_logger(context='Async Batch')

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

METADATA = {
    # 'min_runners': 200,
    # 'max_runners': 3000,
    'chunks_per_vm': 1,  # chunk per VM
    'runners_per_vm': 2,  # runner thread count
    'accuracy': 1.0,  # zero error tolerance
}


class Config:
    NUM_CHUNK = 2  # number of chunk in single upload
    CHUNK_SIZE = 5  # number of record per chunk
    TOTAL_RECORDS_PER_FILE = 1e1  # number of record per file, this is redundant, by default it's num_chunk * chunk_size
    SERVICE_URI = 'my-folder/volume-cylinder'
    INPUT_DIR = os.path.abspath(os.path.join(CONFIG_DIR, '..', 'inputs'))
    OUTPUT_DIR = os.path.abspath(os.path.join(CONFIG_DIR, '..', 'outputs'))
