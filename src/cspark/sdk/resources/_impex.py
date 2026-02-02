from __future__ import annotations

import json
import time
from typing import BinaryIO, List, Mapping, Optional, Union

from httpx import Client

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import RetryTimeoutError, SparkError
from .._utils import get_retry_timeout
from ._base import ApiResource, Uri, UriParams

__all__ = ['ImpEx', 'Export', 'Import', 'Migration', 'Wasm', 'Files']


class ImpEx:
    def __init__(self, config: Config, http_client: Client):
        self.config = config
        self._client = http_client

    @staticmethod
    def only(config: Config, http_client: Client):
        return ImpEx(config, http_client)

    @staticmethod
    def migration(exports: Config, imports: Config, http_client: Client):
        return Migration(exports=exports, imports=imports, http_client=http_client)

    @property
    def exports(self):
        return Export(self.config, self._client)

    @property
    def imports(self):
        return Import(self.config, self._client)

    def exp(
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
        exporter = Export(self.config, self._client)
        response = exporter.initiate(
            folders=folders,
            services=services,
            version_ids=version_ids,
            file_filter=file_filter,
            version_filter=version_filter,
            source_system=source_system,
            correlation_id=correlation_id,
        )
        status = exporter.get_status(
            job_id=response.data['id'],  # type: ignore
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        files = isinstance(status.data, dict) and status.data.get('outputs', {}).get('files', []) or []
        if len(files) == 0:
            error = SparkError.sdk('export job failed to produce any files', status)
            exporter.logger.error(error.message)
            raise error

        return exporter.download([f['file'] for f in files])

    def imp(
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
        importer = Import(self.config, self._client)
        response = importer.initiate(
            destination=destination,
            file=file,
            if_present=if_present,
            source_system=source_system,
            correlation_id=correlation_id,
        )
        status = importer.get_status(
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


class Export(ApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    def describe(self):
        """Describes the export job status across the tenant."""
        url = Uri.of(None, endpoint=f'export/status', **self.base_uri)
        return self.request(url, method='GET')

    def initiate(
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
        response = self.request(url, method='POST', body={'inputs': inputs, **metadata})
        if isinstance(response.data, dict):
            self.logger.info(f'export job created <{response.data["id"]}>')
        return response

    def get_status(
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
            response = self.request(status_url)  # type: ignore
            if isinstance(response.data, dict) and response.data.get('status') in ['completed', 'closed']:
                self.logger.info(f'export job <{job_id}> completed')
                return response

            retries += 1
            self.logger.info(f'waiting for export job to complete (attempt {retries} of {max_retries})')
            delay = get_retry_timeout(retries, retry_interval)
            time.sleep(delay)

        err_msg = f'export job status timed out after {retries} attempts'
        self.logger.error(err_msg)
        raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)

    def cancel(self, job_id: str):
        url = Uri.of(None, endpoint=f'export/{job_id}', **self.base_uri)
        response = self.request(url, method='PATCH', body={'export_status': 'cancelled'})
        if isinstance(response.data, dict):
            self.logger.info(f'export job <${response.data["id"]}> has been cancelled')
        return response

    def download(self, urls: Union[str, List[str]]):
        downloads = []

        urls = urls if isinstance(urls, list) else [urls]
        for url in urls:
            if not url:
                self.logger.warning('skipping empty download url')
                continue
            try:
                downloads.append(self.request(url))
            except Exception as cause:
                self.logger.warning(f'failed to download file <{url}>', cause)

        return downloads


class Import(ApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    def describe(self):
        """Describes the import job status across the tenant."""
        url = Uri.of(None, endpoint=f'import/status', **self.base_uri)
        return self.request(url, method='GET')

    def initiate(
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
        response = self.request(url, method='POST', form={'importRequestEntity': json.dumps(metadata)}, files=files)
        if isinstance(response.data, dict):
            self.logger.info(f'import job created <{response.data["id"]}>')
        return response

    def get_status(
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
            response = self.request(status_url)  # type: ignore
            if isinstance(response.data, dict) and response.data.get('status') in ['completed', 'closed']:
                self.logger.info(f'import job <{job_id}> completed')
                return response

            retries += 1
            self.logger.info(f'waiting for import job to complete (attempt {retries} of {max_retries})')
            delay = get_retry_timeout(retries, retry_interval)
            time.sleep(delay)

        err_msg = f'import job status timed out after {retries} attempts'
        self.logger.error(err_msg)
        raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)


class Migration:
    def __init__(self, *, exports: Config, imports: Config, http_client: Client):
        self.configs = {'exports': exports, 'imports': imports}
        self.http_client = http_client

    @property
    def exports(self):
        return Export(self.configs['exports'], self.http_client)

    @property
    def imports(self):
        return Import(self.configs['imports'], self.http_client)

    def migrate(self):
        raise NotImplementedError('not implemented yet')


class Wasm(ApiResource):
    def download(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        service_id: Optional[str] = None,
        version_id: Optional[str] = None,
        public: Optional[bool] = False,
    ):
        params = (
            UriParams(folder, service, service_id, version_id=version_id, public=public)
            if uri is None
            else Uri.to_params(uri)
        )
        service_uri = Uri.validate(params).encode()
        endpoint = f'getnodegenzipbyId/{service_uri}'
        resource = 'nodegen' + ('/public' if params.public else '')
        url = Uri.partial(resource, base_url=self.config.base_url.full, endpoint=endpoint)

        return self.request(url)


class Files(ApiResource):
    def download(self, url: str):
        return self.request(url)


def _build_service_mappings(
    uri: Union[str, List[str], Mapping[str, str], List[Mapping[str, str]]], upgrade_type: str = 'minor'
) -> List[Mapping[str, str]]:
    if isinstance(uri, str):
        return [
            {
                'service_uri_source': uri,
                'service_uri_destination': uri,
                'update_version_type': upgrade_type,
            }
        ]

    if isinstance(uri, list):
        uris: List[Mapping[str, str]] = []
        for u in uri:
            mappings = _build_service_mappings(u, upgrade_type)
            uris.extend(mappings)
        return uris

    if isinstance(uri, dict):
        source = uri.get('source', '')
        return [
            {
                'service_uri_source': source,
                'service_uri_destination': uri.get('target', source),
                'update_version_type': uri.get('upgrade', upgrade_type),
            }
        ]

    raise SparkError.sdk('invalid import service uri', uri)
