import csv
import json
import os
import uuid

import cspark.sdk as Spark

from .config import Config, logger


class ChunkGenerator:
    def __init__(self, indir, blocksize=None, chunksize=None, maxrecords=None):
        """Initializes the ChunkGenerator with the specified parameters."""
        # Use config values or defaults if not provided
        self.num_chunk = blocksize or Config.NUM_CHUNK  # number of chunks per submission
        self.chunk_size = chunksize or Config.CHUNK_SIZE  # number of records per chunk
        self.max_records = maxrecords or Config.TOTAL_RECORDS_PER_FILE  # maximum records to process
        self.record_index = 0  # current record index within the current file
        self.current_file_index = 0  # current file index
        self.files = self._get_file_paths(indir)  # List of input files
        self.headers, self.data = [], []  # Data will be loaded file by file
        self.done = False  # Track when all files and records have been processed

        # Load the first file
        if self.files:
            self._load_current_file()

    def _get_file_paths(self, indir):
        """Get a list of CSV files in the specified directory."""
        return sorted([os.path.join(indir, f) for f in os.listdir(indir) if f.endswith('.csv')])

    def _load_data(self, filepath):
        """Loads CSV data from the given file path."""
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # First row contains headers
            data = list(reader)  # Remaining rows contain data

        return headers, data

    def _load_current_file(self):
        """
        Loads the current file based on the current file index.
        Resets the record index for the new file.
        """
        if self.current_file_index < len(self.files):
            filepath = self.files[self.current_file_index]
            self.headers, self.data = self._load_data(filepath)
            self.record_index = 0  # Reset the record index for the new file

    def get_next(self):
        """
        Generates the next batch of chunks based on the current record index.
        Returns a dictionary with the generated chunks and a done flag.
        """
        chunks = []

        # If we've already processed all files, return done
        if self.done:
            return {'chunks': []}, True

        # Continue generating chunks while there are records to process
        while len(chunks) < self.num_chunk and not self.done:
            if not self.data or self.record_index >= len(self.data):  # Load the next file if there is no data left
                self.current_file_index += 1
                if self.current_file_index < len(self.files):
                    self._load_current_file()
                else:
                    self.done = True
                    break

            remaining_records = len(self.data) - self.record_index

            # Determine how many chunks can be created from remaining records
            num_chunks_available = min(
                self.num_chunk - len(chunks), (remaining_records + self.chunk_size - 1) // self.chunk_size
            )

            for _ in range(num_chunks_available):
                next_cursor = min(self.record_index + self.chunk_size, len(self.data))

                # Create a Spark ChunkData object for the current chunk
                chunk_data = Spark.ChunkData(
                    inputs=[self.headers] + self.data[self.record_index : next_cursor],
                    parameters={},
                    summary={'ignore_error': False, 'return_all_records': True},
                )

                # Create a BatchChunk and add it to the list of chunks
                chunks.append(Spark.BatchChunk(id=str(uuid.uuid4()), data=chunk_data, size=self.chunk_size))

                # Update the record index for the next iteration
                self.record_index += self.chunk_size

                # If all records from this file have been processed, clear data
                if self.record_index >= len(self.data):
                    self.data = []  # Indicate that the current file has been fully processed
                    break

        self._persist_chunk(Config.OUTPUT_DIR, chunks)  # Persist the chunks to disk

        return {'chunks': chunks}, self.done

    def _persist_chunk(self, outdir, chunks: list[Spark.BatchChunk]):
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        for count, chunk in enumerate(chunks):
            filename = f'{chunk.id}_input.csv'
            filepath = os.path.join(outdir, filename)

            try:
                with open(filepath, mode='w', newline='') as file:
                    writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(chunk.data.inputs)
                logger.info(f'Saved chunk {count} to {filepath}')
            except Exception as e:
                logger.error(f'Error saving file {filepath}: {e}')


class ChunkProcessor:
    def __init__(self, verbose=False, outdir=None):
        """
        Initializes the ChunkProcessor.
        :param verbose: Whether to log additional information
        :param output_dir: The directory where processed chunks will be saved
        """
        self.count = 0  # To keep track of the number of processed chunks
        self.verbose = verbose
        self.headers = []
        self.results = []
        self.outdir = outdir or Config.OUTPUT_DIR
        os.makedirs(self.outdir, exist_ok=True)

    @property
    def is_empty(self):
        """Checks if there are results to save."""
        return len(self.results) == 0

    def process(self, chunk):
        """
        Processes a chunk of data, appending results for later saving.
        :param chunk: The chunk of data to process
        """
        self.count += 1
        self._log_info(f'Processing chunk {self.count}')

        if not self._validate_chunk(chunk):
            return

        try:
            self.headers, *rows = chunk['outputs']
            self.results.extend(self._process_row(row) for row in rows)
        except Exception as e:
            logger.error(f'fail to serialize chunk: {e}')

        # Save results every NUM_CHUNK chunks
        if self.count % Config.NUM_CHUNK == 0:
            self.save()

    def save(self):
        """Saves the results into a CSV file."""
        filepath = os.path.join(self.outdir, f'{self.count}_output.csv')
        self._save_to_csv(filepath)
        self.results = []  # Clear results after saving

    def _process_row(self, row):
        """
        Processes a single row, converting list or dict items to JSON strings if necessary.
        :param row: A single row to process
        :return: Processed row
        """
        return [json.dumps(item) if isinstance(item, (list, dict)) else item for item in row]

    def _validate_chunk(self, chunk):
        """
        Validates that the chunk contains valid data for processing.
        :param chunk: The chunk to validate
        :return: True if valid, False otherwise
        """
        if not chunk or 'outputs' not in chunk or len(chunk['outputs']) < 2:
            logger.warning(f'Invalid chunk at count {self.count}')
            return False
        return True

    def _save_to_csv(self, filepath):
        """
        Saves the processed results to a CSV file.
        :param filepath: The file path where the CSV will be saved
        """
        try:
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(self.headers)  # Write headers
                writer.writerows(self.results)  # Write processed rows
            self._log_info(f'Saved chunk {self.count + 1} to {filepath}')
        except Exception as e:
            logger.error(f'Unable to save file {filepath}: {e}')

    def _log_info(self, message):
        """Logs a message if verbose mode is enabled."""
        if self.verbose:
            logger.info(message)
