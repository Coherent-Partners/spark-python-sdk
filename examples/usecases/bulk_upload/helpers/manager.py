import asyncio
from datetime import datetime
from json import dumps
from pathlib import Path

from cspark.sdk import Client, SparkError

from .config import logger
from .reporter import Reporter


class Manager:
    def __init__(self, config: dict):
        self._bulk_size: int = config.get('bulk_size', 5)
        self._outdir: str = config.get('outdir', 'reports')
        self._reporter = Reporter(self._outdir)
        self._client = Client(timeout=90_000, logger={'context': logger.name, 'level': config.get('logging')})

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

        tasks = [asyncio.ensure_future(self._upload_service(svc)) for svc in group]
        return await asyncio.gather(*tasks)

    async def _upload_service(self, service: dict):
        report = {'file_name': service['file_name'], 'folder': service['using']['folder'], 'service': service['name']}
        try:
            with self._client.services as client:
                # FIXME: add support for async upload (await client.create(...))
                response = client.create(name=service['name'], file=open(service['file'], 'rb'), **service['using'])
                upload_stats = Path(self._outdir) / f'{service["name"]}.json'
                upload_stats.write_text(dumps(response, indent=2))

            logger.debug(f'uploaded service {service["name"]} successfully')
            report['success'] = True
        except SparkError as e:
            logger.warning(f'failed to upload service {service["name"]}: {e}')
            report['success'] = False
        finally:
            report['processed_at'] = datetime.now().isoformat()
            self._reporter.add(report)
        return report
