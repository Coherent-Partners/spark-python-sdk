import time
from typing import List, Optional, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkError
from .._utils import get_retry_timeout
from ._base import ApiResource, Uri, UriParams

__all__ = ['ImpEx', 'Export', 'Import', 'Migration', 'Wasm', 'Files']


class ImpEx:
    def __init__(self, config: Config):
        self.config = config

    @staticmethod
    def only(config: Config):
        return ImpEx(config)

    @staticmethod
    def migration(exports: Config, imports: Config):
        return Migration(exports=exports, imports=imports)

    @property
    def exports(self):
        return Export(self.config)

    @property
    def imports(self):
        return Import(self.config)

    def export(
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
        max_retries = max_retries or self.config.max_retries
        retry_interval = retry_interval or self.config.retry_interval

        with self.exports as exporter:
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


class Export(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
        self._base_uri = {'base_url': self.config.base_url.full, 'version': 'api/v4'}

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
        url = Uri.of(None, endpoint='export', **self._base_uri)

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
        status_url = Uri.of(None, endpoint=f'export/{job_id}/status', **self._base_uri) if job_id else url

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

        error = SparkError.sdk(f'export job status timed out after {retries} attempts')
        self.logger.error(error.message)
        raise error

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
    ...


class Migration:
    def __init__(self, *, exports: Config, imports: Config):
        self.configs = {'exports': exports, 'imports': imports}

    @property
    def exports(self):
        return Export(self.configs['exports'])

    @property
    def imports(self):
        return Import(self.configs['imports'])


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
