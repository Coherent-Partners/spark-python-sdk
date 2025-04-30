import time
from datetime import datetime
from typing import List, Optional, Union, cast

from .._errors import RetryTimeoutError, SparkError
from .._utils import DateUtils, StringUtils, get_retry_timeout, is_int
from ._base import ApiResource, Uri, UriParams

__all__ = ['History']


class History(ApiResource):
    @property
    def downloads(self) -> 'LogDownload':
        return LogDownload(self.config)

    def rehydrate(
        self,
        uri: Union[None, str, UriParams],
        *,
        call_id: str,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        index: Optional[int] = None,
        legacy: bool = False,
    ):
        if StringUtils.is_empty(call_id):
            raise SparkError.sdk('call_id is required when rehydrating', {'call_id': call_id})

        uri = Uri.validate(UriParams(folder, service) if uri is None else Uri.to_params(uri))
        endpoint = f'download/{call_id}' if legacy else f'download/xml/{call_id}'
        url = Uri.of(uri.pick('folder', 'service'), base_url=self.config.base_url.full, endpoint=endpoint)
        params = {'index': str(index)} if is_int(index) and cast(int, index) >= 0 else None
        response = self.request(url, params=params)

        if isinstance(response.data, dict) and isinstance(response.data['response_data'], dict):
            download_url = response.data['response_data']['download_url']
            response.data['status'] = 'Success'  # comes as None from the API
        else:
            raise SparkError('failed to produce a download URL', response)

        return self.request(download_url).copy_with(data=response.data)

    def download(
        self,
        *,
        folder: str,
        service: str,
        type: str = 'json',
        version_id: Optional[str] = None,
        call_ids: Optional[List[str]] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        timezone_offset: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        with self.downloads as downloads:
            response = downloads.initiate(
                folder=folder,
                service=service,
                type=type,
                version_id=version_id,
                call_ids=call_ids,
                start_date=start_date,
                end_date=end_date,
                source_system=source_system,
                correlation_id=correlation_id,
                timezone_offset=timezone_offset,
            )

            job_id = isinstance(response.data, dict) and response.data.get('response_data', {}).get('job_id') or ''
            if not job_id:
                error = SparkError('failed to produce a download job', response)
                self.logger.error(error.message)
                raise error

            job = downloads.get_status(
                job_id=job_id,
                folder=folder,
                service=service,
                type=type,
                max_retries=max_retries,
                retry_interval=retry_interval,
            )

            download_url = isinstance(job.data, dict) and job.data.get('response_data', {}).get('download_url') or ''
            if not download_url:
                error = SparkError(f'failed to produce a download URL for <{job_id}>', job)
                self.logger.error(error.message)
                raise error

            logs = self.request(download_url)

            # NOTE: rewrite response as API response is missing status
            job.data.update({'status': 'Success'})  # type: ignore
            return logs.copy_with(status=job.status, data=job.data)


class LogDownload(ApiResource):
    def initiate(
        self,
        *,
        folder: str,
        service: str,
        type: str = 'json',
        version_id: Optional[str] = None,
        call_ids: Optional[List[str]] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        timezone_offset: Optional[str] = None,
    ):
        type = type.lower() if type.lower() in ['json', 'csv'] else 'json'
        uri = Uri.validate(UriParams(folder, service))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=f'log/download{type}')

        call_ids = call_ids or []
        if len(call_ids) == 0 and source_system:
            call_ids.append(source_system)
        if len(call_ids) == 0 and correlation_id:
            call_ids.append(correlation_id)

        body = {
            'request_data': {'call_ids': call_ids, 'timezone_offset': timezone_offset},
            'request_meta': {'version_id': version_id},
        }
        if DateUtils.is_date(start_date):
            body['request_data']['start_date'] = DateUtils.to_datetime(start_date).isoformat()  # type: ignore
        if DateUtils.is_date(end_date):
            body['request_data']['end_date'] = DateUtils.to_datetime(end_date).isoformat()  # type: ignore

        response = self.request(url, method='POST', body=body)
        if isinstance(response.data, dict):
            self.logger.info(f'{type} download job created <{response.data.get("response_data",{}).get("job_id")}>')
        return response

    def get_status(
        self,
        *,
        folder: str,
        service: str,
        job_id: str,
        type: str = 'json',
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        throwable: bool = False,
    ):
        max_retries = max_retries or self.config.max_retries
        retry_interval = retry_interval or self.config.retry_interval
        type = type.lower() if type.lower() in ['json', 'csv'] else 'json'

        uri = Uri.validate(UriParams(folder, service))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=f'log/download{type}/status/{job_id}')

        retries = 0
        response = self.request(url)
        while True:
            response_data = isinstance(response.data, dict) and response.data.get('response_data', {}) or {}
            progress = response_data.get('progress', 0)

            if progress == 100:
                return response

            if progress < 100 and retries < max_retries:
                self.logger.info(f'waiting for log download status job to complete - {progress}%')

                retries += 1
                time.sleep(get_retry_timeout(retries, retry_interval))
                response = self.request(url)
            else:
                err_msg = f'log download job status check timed out after {retries} attempts'
                if throwable:
                    self.logger.error(err_msg)
                    raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)
                self.logger.warning(err_msg)
                return response
