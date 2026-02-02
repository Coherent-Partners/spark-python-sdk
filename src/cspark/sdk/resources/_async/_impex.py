from __future__ import annotations

import asyncio
from json import dumps
from typing import BinaryIO, List, Mapping, Optional, Union

from httpx import AsyncClient

from ..._config import Config
from ..._constants import SPARK_SDK
from ..._errors import RetryTimeoutError, SparkError
from ..._utils import get_retry_timeout
from .._base import Uri, UriParams
from .._impex import _build_service_mappings
from ._base import AsyncApiResource

__all__ = ['AsyncImpEx', 'AsyncExport', 'AsyncImport', 'AsyncMigration', 'AsyncWasm', 'AsyncFiles']


class AsyncImpEx(AsyncApiResource):
    def __init__(self, config: Config, http_client: AsyncClient):
        self.config = config
        self._client = http_client

    @staticmethod
    def only(config: Config, http_client: AsyncClient):
        return AsyncImpEx(config, http_client)

    @staticmethod
    def migration(exports: Config, imports: Config, http_client: AsyncClient):
        return AsyncMigration(exports=exports, imports=imports, http_client=http_client)

    @property
    def exports(self):
        return AsyncExport(self.config, self._client)

    @property
    def imports(self):
        return AsyncImport(self.config, self._client)

    async def describe(self, as_json: bool = False):
        """Describes the export and import jobs across the tenant."""
        if as_json:
            return {'exports': (await self.exports.describe()).data, 'imports': (await self.imports.describe()).data}
        return await asyncio.gather(self.exports.describe(), self.imports.describe())

    async def exp(
        self,
        *,
        folders: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        version_ids: Optional[List[str]] = None,
        file_filter: Optional[str] = None,
        version_filter: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        exporter = AsyncExport(self.config, self._client)
        response = await exporter.initiate(
            folders=folders,
            services=services,
            version_ids=version_ids,
            file_filter=file_filter,
            version_filter=version_filter,
            source_system=source_system,
            correlation_id=correlation_id,
        )
        status = await exporter.get_status(
            job_id=response.data['id'],  # type: ignore
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        files = isinstance(status.data, dict) and status.data.get('outputs', {}).get('files', []) or []
        if len(files) == 0:
            error = SparkError.sdk('export job failed to produce any files', status)
            exporter.logger.error(error.message)
            raise error

        return await exporter.download([f['file'] for f in files])

    async def imp(
        self,
        destination: Union[str, List[str], Mapping[str, str], List[Mapping[str, str]]],
        file: BinaryIO,
        *,
        if_present: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        importer = AsyncImport(self.config, self._client)
        response = await importer.initiate(
            destination=destination,
            file=file,
            if_present=if_present,
            source_system=source_system,
            correlation_id=correlation_id,
        )
        status = await importer.get_status(
            job_id=response.data['id'],  # type: ignore
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        services = isinstance(status.data, dict) and status.data.get('outputs', {}).get('services', []) or []
        if isinstance(status.data, dict) and status.data.get('errors'):
            error = SparkError.sdk('import job failed with errors', status)
            importer.logger.error(error.message)
            raise error
        elif len(services) == 0:
            importer.logger.warning('import job completed without any services')
        else:
            importer.logger.info(f'{len(services)} service(s) imported')

        return status

    # aliases for export and import to avoid breaking changes.
    export = exp
    import_ = imp


class AsyncExport(AsyncApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    async def describe(self):
        """Describes the export jobs across the tenant."""
        url = Uri.of(None, endpoint=f'export/status', **self.base_uri)
        return await self.request(url, method='GET')

    async def initiate(
        self,
        *,
        folders: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        version_ids: Optional[List[str]] = None,
        file_filter: Optional[str] = None,
        version_filter: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        metadata = {
            'file_filter': file_filter or 'migrate',
            'version_filter': version_filter or 'latest',
            'source_system': source_system or SPARK_SDK,
            'correlation_id': correlation_id,
        }
        inputs = {
            k: v
            for k, v in {
                'folders': folders,
                'services': services,
                'version_ids': version_ids,
            }.items()
            if v
        }

        if len(inputs) == 0:
            error = SparkError.sdk('at least one of folders, services, or version_ids must be provided')
            self.logger.error(error.message)
            raise error

        url = Uri.of(None, endpoint='export', **self.base_uri)
        response = await self.request(url, method='POST', body={'inputs': inputs, **metadata})
        if isinstance(response.data, dict):
            self.logger.info(f'export job created <{response.data["id"]}>')
        return response

    async def get_status(
        self,
        *,
        job_id: Optional[str] = None,
        url: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        if job_id is None and url is None:
            error = SparkError.sdk('either job_id or url must be provided')
            self.logger.error(error.message)
            raise error

        max_retries = max_retries or self.config.max_retries
        retry_interval = retry_interval or self.config.retry_interval
        status_url = Uri.of(None, endpoint=f'export/{job_id}/status', **self.base_uri) if job_id else url

        retries = 0
        while retries < max_retries:
            response = await self.request(status_url)  # type: ignore
            if isinstance(response.data, dict) and response.data.get('status') in ['completed', 'closed']:
                self.logger.info(f'export job <{job_id}> completed')
                return response

            retries += 1
            self.logger.info(f'waiting for export job to complete (attempt {retries} of {max_retries})')
            delay = get_retry_timeout(retries, retry_interval)
            await asyncio.sleep(delay)

        err_msg = f'export job status timed out after {retries} attempts'
        self.logger.error(err_msg)
        raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)

    async def cancel(self, job_id: str):
        url = Uri.of(None, endpoint=f'export/{job_id}', **self.base_uri)
        response = await self.request(url, method='PATCH', body={'export_status': 'cancelled'})
        if isinstance(response.data, dict):
            self.logger.info(f'export job <${response.data["id"]}> has been cancelled')
        return response

    async def download(self, urls: Union[str, List[str]]):
        downloads = []

        urls = urls if isinstance(urls, list) else [urls]
        for url in urls:
            if not url:
                self.logger.warning('skipping empty download url')
                continue
            try:
                downloads.append(await self.request(url))
            except Exception as cause:
                self.logger.warning(f'failed to download file <{url}>', cause)

        return downloads


class AsyncImport(AsyncApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    async def describe(self):
        """Describes the import jobs across the tenant."""
        url = Uri.of(None, endpoint=f'import/status', **self.base_uri)
        return await self.request(url, method='GET')

    async def initiate(
        self,
        destination: Union[str, List[str], Mapping[str, str], List[Mapping[str, str]]],
        file: BinaryIO,
        *,
        if_present: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        files = {'file': ('package.zip', file, 'application/zip')}
        metadata = {
            'inputs': {'services_modify': _build_service_mappings(destination)},
            'services_existing': if_present or 'add_version',
            'source_system': source_system or SPARK_SDK,
            'correlation_id': correlation_id,
        }

        url = Uri.of(None, endpoint='import', **self.base_uri)
        response = await self.request(url, method='POST', form={'importRequestEntity': dumps(metadata)}, files=files)
        if isinstance(response.data, dict):
            self.logger.info(f'import job created <{response.data["id"]}>')
        return response

    async def get_status(
        self,
        *,
        job_id: Optional[str] = None,
        url: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        if job_id is None and url is None:
            error = SparkError.sdk('either job_id or url must be provided')
            self.logger.error(error.message)
            raise error

        max_retries = max_retries or self.config.max_retries
        retry_interval = retry_interval or self.config.retry_interval
        status_url = Uri.of(None, endpoint=f'import/{job_id}/status', **self.base_uri) if job_id else url

        retries = 0
        while retries < max_retries:
            response = await self.request(status_url)  # type: ignore
            if isinstance(response.data, dict) and response.data.get('status') in ['completed', 'closed']:
                self.logger.info(f'import job <{job_id}> completed')
                return response

            retries += 1
            self.logger.info(f'waiting for import job to complete (attempt {retries} of {max_retries})')
            delay = get_retry_timeout(retries, retry_interval)
            await asyncio.sleep(delay)

        err_msg = f'import job status timed out after {retries} attempts'
        self.logger.error(err_msg)
        raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)


class AsyncMigration:
    def __init__(self, *, exports: Config, imports: Config, http_client: AsyncClient):
        self.configs = {'exports': exports, 'imports': imports}
        self.http_client = http_client

    @property
    def exports(self):
        return AsyncExport(self.configs['exports'], self.http_client)

    @property
    def imports(self):
        return AsyncImport(self.configs['imports'], self.http_client)

    async def migrate(self):
        raise NotImplementedError('not implemented yet')


class AsyncWasm(AsyncApiResource):
    async def download(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        service_id: Optional[str] = None,
        version_id: Optional[str] = None,
        public: Optional[bool] = False,
    ):
        uri_params = Uri.validate(uri or UriParams(folder, service, service_id, version_id=version_id, public=public))
        endpoint = f'getnodegenzipbyId/{uri_params.encode()}'
        resource = 'nodegen' + ('/public' if uri_params.public else '')
        url = Uri.partial(resource, base_url=self.config.base_url.full, endpoint=endpoint)

        return await self.request(url)


class AsyncFiles(AsyncApiResource):
    async def download(self, url: str):
        return await self.request(url)
