import asyncio
import csv
import json
import logging
import os
import pathlib
import re
import sys
from datetime import datetime
from json import dumps
from pathlib import Path

import yaml
from cspark.sdk import DEFAULT_LOGGER_FORMAT, AsyncClient, get_logger
from dotenv import load_dotenv

logging.basicConfig(filename='console.log', filemode='w', format=DEFAULT_LOGGER_FORMAT)
logger = get_logger(context='Bulk Upload')
default_upload_config = {'versioning': 'patch', 'track_user': True, 'max_retries': 3, 'retry_interval': 3.0}

yaml_config = """
version: 1.0
logging: INFO

outdir: outputs/
allowed_formats: ['.xlsx', '.xls']
max_file_size_mb: 25
bulk_size: 2

upload:
  folder: my-folder
  versioning: patch
  max_retries: 20
  retry_interval: 4.0

services:
  - path/to/your/file.xlsx
  - path/to/your/other/file.xlsx
"""


class ConfigError(ValueError):
    ...


def load_config(content: str = yaml_config) -> dict:
    try:
        config = yaml.safe_load(content)

        if not re.match(r'^1\.\d+$', str(config.get('version'))):  # should match: 1.*
            raise ConfigError('unsupported version (must be 1.*)')

        config['logging'] = getattr(logging, config.get('logging', 'INFO'))
        config['services'] = extract_services(config)
        return config
    except (yaml.YAMLError, json.JSONDecodeError, ConfigError) as err:
        logger.error(f'invalid configuration: {content}\n{err!s}')
        sys.exit(1)


def extract_services(config: dict) -> list[dict]:
    formats = config.get('allowed_formats', ['.xlsx', '.xls'])
    file_size = config.get('max_file_size_mb', 25) * 1024 * 1024  # convert MB to bytes
    upload_cfg = config.get('upload', default_upload_config)

    services = []
    for svc in config.get('services', []):
        if isinstance(svc, str):
            svc = {'name': None, 'file': svc}

        if isinstance(svc, dict):
            svc['using'] = {**upload_cfg, **svc.get('using', {})}
            if not svc['using'].get('folder'):  # type: ignore
                logger.warning(f'folder name is required for service: {svc.get("name")}')
                continue

            file = pathlib.Path(svc['file'])
            if not (file.exists() and file.suffix in formats):
                logger.warning(f'incorrect service file: {svc["file"]}')
                continue
            if file.stat().st_size > file_size:
                logger.warning(f'file size is too large: {file.name}')
                continue

            svc.update({'name': svc.get('name') or file.stem, 'file_name': file.name})
        services.append(svc)

    logger.info(f'found {len(services)} service(s) to upload')
    return services


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


class Manager:
    def __init__(self, config: dict):
        self._bulk_size: int = config.get('bulk_size', 5)
        self._outdir: str = config.get('outdir', 'reports')
        self._reporter = Reporter(self._outdir)
        self._client_opts = {'timeout': 90_000, 'logger': {'context': logger.name, 'level': config.get('logging')}}

    def group(self, services: list[dict], by: int = 5):
        groups = [[]]
        for service in services:
            if len(groups[-1]) >= by:
                groups.append([])
            groups[-1].append(service)
        return groups

    def run(self, group: list[dict]):
        return asyncio.run(self._bulk_upload(group))

    def dispose(self):
        self._reporter.write_as_csv('upload_report.csv')

    async def _bulk_upload(self, group: list[dict]):
        logger.info(f'uploading group of {len(group)} services...')
        async with AsyncClient(**self._client_opts) as client:
            tasks = [asyncio.ensure_future(self._upload_service(svc, client)) for svc in group]
            return await asyncio.gather(*tasks)

    async def _upload_service(self, service: dict, client: AsyncClient):
        report = {'file_name': service['file_name'], 'folder': service['using']['folder'], 'service': service['name']}
        try:
            with open(service['file'], 'rb') as file:
                response = await client.services.create(name=service['name'], file=file, **service['using'])

            upload_stats = Path(self._outdir) / f'{service["name"]}.json'
            upload_stats.write_text(dumps(response, indent=2))

            logger.debug(f'uploaded service {service["name"]} successfully')
            report['success'] = True
        except Exception as e:
            logger.warning(f'failed to upload service {service["name"]}: {e}')
            report['success'] = False
        finally:
            report['processed_at'] = datetime.now().isoformat()
            self._reporter.add(report)
        return report


def main():
    load_dotenv()
    config = load_config()
    manager = Manager(config)
    try:
        services, size = config.get('services', []), config.get('bulk_size', 5)
        for group in manager.group(services, by=size):
            manager.run(group)
    finally:
        manager.dispose()


if __name__ == '__main__':
    main()
