import csv
import os

from .config import logger


class Reporter:
    def __init__(self, outdir: str):
        os.makedirs(outdir, exist_ok=True)
        self._outdir = outdir
        self._fieldnames = ['file_name', 'folder', 'service', 'success', 'processed_at']
        self._reports = []

    def add(self, report: dict):
        self._reports.append(report)

    def write_as_csv(self, filepath: str = 'report.csv'):
        filepath = os.path.join(self._outdir, filepath)
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames)
            writer.writeheader()
            writer.writerows(self._reports)
        logger.info(f'report has been written to: {filepath}')
