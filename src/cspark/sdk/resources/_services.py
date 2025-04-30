import gzip
import json
import time
import zlib
from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Mapping, Optional, Tuple, Union

from .._constants import SPARK_SDK
from .._errors import RetryTimeoutError, SparkError
from .._utils import DateUtils, StringUtils, get_retry_timeout
from ._base import ApiResource, HttpResponse, Uri, UriParams
from ._transforms import TransformParams

__all__ = ['Services', 'ServiceExecuted']


class Services(ApiResource):
    @property
    def compilation(self):
        return Compilation(self.config)

    def create(
        self,
        name: str,
        *,
        folder: str,
        file: BinaryIO,
        file_name: Optional[str] = None,
        draft_name: Optional[str] = None,
        versioning: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        track_user: Optional[bool] = False,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        compiled = self.compile(
            folder=folder,
            service=name,
            file=file,
            file_name=file_name,
            versioning=versioning,
            start_date=start_date,
            end_date=end_date,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )
        upload = compiled['upload'].get('response_data', {})

        published = self.publish(
            folder=folder,
            service=name,
            file_id=upload.get('original_file_documentid'),
            engine_id=upload.get('engine_file_documentid'),
            draft_name=draft_name,
            versioning=versioning,
            start_date=start_date,
            end_date=end_date,
            track_user=track_user,
        )
        return {**compiled, 'publication': published.data}

    def compile(
        self,
        *,
        folder: str,
        service: str,
        file: BinaryIO,
        file_name: Optional[str] = None,
        versioning: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
    ):
        with self.compilation as compilation:
            upload = compilation.initiate(
                folder=folder,
                service=service,
                file=file,
                file_name=file_name,
                versioning=versioning,
                start_date=start_date,
                end_date=end_date,
            )

            status = compilation.get_status(
                job_id=isinstance(upload.data, dict)
                and upload.data.get('response_data', {}).get('nodegen_compilation_jobid')
                or '',  # NOTE: this should never happen (only bypassing type checker)
                folder=folder,
                service=service,
                max_retries=max_retries,
                retry_interval=retry_interval,
            )
            return {'upload': upload.data, 'compilation': status.data}

    def publish(
        self,
        folder: str,
        service: str,
        file_id: str,
        engine_id: str,
        draft_name: Optional[str] = None,
        versioning: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        track_user: Optional[bool] = False,
    ):
        startdate, enddate = DateUtils.parse(start_date, end_date)
        uri = Uri.validate(UriParams(folder, service))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='publish')
        params = {
            'draft_service_name': draft_name or uri.service,
            'effective_start_date': startdate.isoformat(),
            'effective_end_date': enddate.isoformat(),
            'original_file_documentid': file_id,
            'engine_file_documentid': engine_id,
            'version_difference': versioning or 'minor',
            'should_track_user_action': track_user,
        }

        response = self.request(url, method='POST', body={'request_data': params})
        version_id = isinstance(response.data, dict) and response.data.get('response_data', {}).get('version_id')
        if version_id:
            self.logger.info(f'service published with version id <{version_id}>')
        return response

    def execute(
        self,
        uri: Union[str, UriParams],
        *,
        response_format: Optional[str] = None,
        encoding: Optional[str] = None,  # 'gzip' | 'deflate'
        # data for calculations
        inputs: Union[None, str, Dict[str, Any], List[Any]] = None,  # TODO: support `pandas.DataFrame`
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        compiler_type: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        # Available only in v3
        debug_solve: Optional[bool] = None,
        downloadable: Optional[bool] = False,
        echo_inputs: Optional[bool] = False,
        tables_as_array: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        outputs_filter: Optional[str] = None,
        # extra metadata if needed
        extras: Optional[Mapping[str, Any]] = None,
    ):
        uri = Uri.validate(uri)

        executable = _ExecuteInputs(inputs)
        metadata = _ExecuteMeta(
            uri,
            is_batch=executable.is_batch,
            active_since=active_since,
            source_system=source_system,
            correlation_id=correlation_id,
            call_purpose=call_purpose,
            compiler_type=compiler_type,
            subservices=subservices,
            debug_solve=debug_solve,
            downloadable=downloadable,
            echo_inputs=echo_inputs,
            tables_as_array=tables_as_array,
            selected_outputs=selected_outputs,
            outputs_filter=outputs_filter,
            extras=extras,
        )

        if executable.is_batch:
            url = Uri.of(uri.pick('public'), base_url=self.config.base_url.full, version='api/v4', endpoint='execute')
            body = {'inputs': executable.inputs, **metadata.values}
        else:
            endpoint = '' if uri.version_id or uri.service_id else 'execute'
            url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=endpoint)
            body = {'request_data': {'inputs': executable.inputs}, 'request_meta': metadata.values}

        if encoding:
            content, headers = self.__encode(data=body, encoding=encoding)
            response = self.request(url, method='POST', content=content, headers=headers)
        else:
            response = self.request(url, method='POST', body=body)
        return ServiceExecuted(response, executable.is_batch, response_format or 'alike')

    def transform(
        self,
        uri: Union[str, UriParams],
        *,
        # data for calculations
        inputs: Any,  # required
        using: Union[str, Dict[str, str], None] = None,
        api_version: str = 'v3',  # 'v3' | 'v4'
        encoding: Optional[str] = None,  # 'gzip' | 'deflate'
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        compiler_type: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        # Only for api/v3
        debug_solve: Optional[bool] = None,
        downloadable: Optional[bool] = False,
        echo_inputs: Optional[bool] = False,
        tables_as_array: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        outputs_filter: Optional[str] = None,
        # extra metadata if needed
        extras: Optional[Mapping[str, Any]] = None,
    ):
        uri = Uri.validate(uri)

        metadata = _ExecuteMeta(
            uri,
            is_batch=api_version == 'v4',
            active_since=active_since,
            source_system=source_system,
            correlation_id=correlation_id,
            call_purpose=call_purpose,
            compiler_type=compiler_type,
            subservices=subservices,
            debug_solve=debug_solve,
            downloadable=downloadable,
            echo_inputs=echo_inputs,
            tables_as_array=tables_as_array,
            selected_outputs=selected_outputs,
            outputs_filter=outputs_filter,
            extras=extras,
        )

        if isinstance(using, str):
            # (legacy) using transform name for Documents saved under Options > /apps/transforms
            endpoint = f'transforms/{using}/for/folders/{uri.folder}/services/{uri.service}'
        else:
            using = using or {}  # use 'folder' and 'service' as fallback if using is wrong
            transform = TransformParams(using.get('folder', uri.folder), using.get('service', uri.service))
            endpoint = f'transforms/{transform.folder}/{transform.name}/for/{uri.folder}/{uri.service}'

        url = Uri.of(base_url=self.config.base_url.full, version='api/v4', endpoint=endpoint)

        if encoding:
            content, headers = self.__encode(data=inputs or {}, encoding=encoding, extras=metadata.as_header)
            response = self.request(url, method='POST', content=content, headers=headers)
        else:
            response = self.request(url, method='POST', body=inputs or {}, headers=metadata.as_header)
        return response

    def validate(
        self,
        uri: Union[str, UriParams],
        *,
        # data for validations
        inputs: Union[None, str, Dict[str, Any]] = None,
        validation_type: Optional[str] = None,  # 'dynamic' | 'static'
        # Metadata for validations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        compiler_type: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        # Available only in v3
        debug_solve: Optional[bool] = None,
        downloadable: Optional[bool] = False,
        echo_inputs: Optional[bool] = False,
        tables_as_array: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        outputs_filter: Optional[str] = None,
        # extra metadata if needed
        extras: Optional[Mapping[str, Any]] = None,
    ):
        uri = Uri.validate(uri)
        validation_type = StringUtils.is_not_empty(validation_type) and str(validation_type).lower() or None

        executable = _ExecuteInputs(inputs)
        metadata = _ExecuteMeta(
            uri,
            is_batch=False,
            active_since=active_since,
            source_system=source_system,
            correlation_id=correlation_id,
            call_purpose=call_purpose,
            compiler_type=compiler_type,
            subservices=subservices,
            debug_solve=debug_solve,
            downloadable=downloadable,
            echo_inputs=echo_inputs,
            tables_as_array=tables_as_array,
            selected_outputs=selected_outputs,
            outputs_filter=outputs_filter,
            extras=extras,
        )
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='validation')
        body = {
            'request_data': {'inputs': executable.inputs},
            'request_meta': {
                **metadata.values,
                'validation_type': 'dynamic' if validation_type == 'dynamic' else 'default_values',
            },
        }

        return self.request(url, method='POST', body=body)

    def get_schema(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        version_id: Optional[str] = None,
    ):
        uri = Uri.validate(Uri.to_params(uri) if uri else UriParams(folder, service, version_id=version_id))
        base, folder, service = self.config.base_url, uri.folder, uri.service
        if StringUtils.is_not_empty(uri.version_id):
            url = Uri.partial(f'GetEngineDetailByVersionId/versionid/{uri.version_id}', base_url=base.full)
            return self.request(url, method='POST')
        else:
            url = Uri.of(base_url=base.value, version='api/v1', endpoint=f'product/{folder}/engines/get/{service}')
            return self.request(url, method='GET')

    def get_metadata(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        service_id: Optional[str] = None,
        version_id: Optional[str] = None,
        proxy: Optional[str] = None,
        public: Optional[bool] = False,
    ):
        uri = Uri.validate(uri or UriParams(folder, service, service_id, None, version_id, proxy, public))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='metadata')

        response = self.request(url)
        return ServiceExecuted(response, False, 'original')

    def get_versions(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = Uri.validate(uri or UriParams(folder, service))
        endpoint = f'product/{uri.folder}/engines/getversions/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        response = self.request(url)
        return response.copy_with(data=response.data.get('data', []) if isinstance(response.data, dict) else [])

    def get_swagger(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        version_id: Optional[str] = None,
        downloadable: Optional[bool] = False,
        subservice: str = 'All',
    ):
        uri = Uri.validate(uri or UriParams(folder, service))
        endpoint = f'downloadswagger/{subservice}/{downloadable}/{version_id or ""}'
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=endpoint)

        return self.request(url, method='GET')

    def search(
        self,
        *,
        page: int = 1,
        limit: int = -1,
        sort: str = 'name1_co',
        query: Optional[List[Any]] = None,
        fields: Optional[List[str]] = None,
        **params: Any,
    ):
        uri = Uri.of(base_url=self.config.base_url.full, endpoint='services/search')
        search_params = {
            'page': page,
            'page_size': limit,
            'sort': sort,
            'search': query or [],
            'fields': fields or ['id', 'foldername', 'filename', 'version', 'modifiedDate'],
            **params,  # other query parameters
        }

        return self.request(uri, method='POST', body={'request_data': search_params})

    def download(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        version_id: Optional[str] = None,
        file_name: Optional[str] = None,
        type: Optional[str] = None,  # 'original' or 'configured'
    ):
        uri = Uri.validate(uri or UriParams(folder, service))
        endpoint = f'product/{uri.folder}/engines/{uri.service}/download/{version_id or ""}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)
        params = {'filename': file_name or '', 'type': 'withmetadata' if type == 'configured' else ''}

        return self.request(url, params=params)

    def recompile(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        version_id: Optional[str] = None,
        compiler: Optional[str] = None,
        release_notes: Optional[str] = None,
        label: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
        upgrade: Optional[str] = None,  # 'major' | 'minor' | 'patch'
        tags: Union[None, str, List[str]] = None,
    ):
        uri = Uri.validate(uri or UriParams(folder, service, version_id=version_id))
        url = Uri.of(uri.pick('folder', 'service'), base_url=self.config.base_url.full, endpoint='recompileNodgen')
        startdate, enddate = DateUtils.parse(start_date, end_date)
        data = {
            'versionId': uri.version_id,
            'upgradeType': upgrade or 'patch',
            'neuronCompilerVersion': compiler or 'StableLatest',
            'releaseNotes': release_notes or f'Recompiled via {SPARK_SDK}',
            'label': label,
            'effectiveStartDate': startdate.isoformat(),
            'effectiveEndDate': enddate.isoformat(),
            'tags': StringUtils.join(tags),
        }

        return self.request(url, method='POST', body={'request_data': data})

    def delete(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = Uri.validate(uri or UriParams(folder, service))
        endpoint = f'product/{uri.folder}/engines/delete/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        return self.request(url, method='DELETE')

    def __encode(
        self,
        *,
        data: Any,
        encoding: str = 'gzip',
        content_type: str = 'application/json',
        extras: Mapping[str, str] = {},
    ) -> Tuple[bytes, Dict[str, str]]:
        headers = {'Content-Type': content_type, 'Content-Encoding': encoding, 'Accept-Encoding': encoding, **extras}
        if encoding == 'gzip':
            return gzip.compress(json.dumps(data).encode('utf-8')), headers
        if encoding == 'deflate':
            return zlib.compress(json.dumps(data).encode('utf-8')), headers
        else:
            raise SparkError.sdk(f'encoding "{encoding}" is not supported', {'encoding': encoding})


class ServiceExecuted(HttpResponse):
    def __init__(self, response: HttpResponse, is_batch: bool, format: str = 'alike'):
        if format == 'original' or is_batch:
            data = response.data
        else:
            resp_data = response.data.get('response_data', {}) if isinstance(response.data, dict) else {}
            resp_meta = response.data.get('response_meta', {}) if isinstance(response.data, dict) else {}
            data = {
                'outputs': [resp_data.get('outputs')],
                'process_time': [resp_meta.get('process_time')],
                'warnings': [resp_data.get('warnings')],
                'errors': [resp_data.get('errors')],
                'service_chain': [resp_meta.get('service_chain')],
                'service_id': resp_meta.get('service_id'),
                'version_id': resp_meta.get('version_id'),
                'version': resp_meta.get('version'),
                'call_id': resp_meta.get('call_id'),
                'compiler_version': resp_meta.get('compiler_version'),
                'correlation_id': resp_meta.get('correlation_id'),
                'request_timestamp': resp_meta.get('request_timestamp'),
            }
        super().__init__(
            response.status, data, response.buffer, response.headers, response.raw_request, response.raw_response
        )


class _ExecuteInputs:
    def __init__(self, data: Union[None, str, Dict[str, Any], List[Any]] = None):
        if data is None or (isinstance(data, list) and len(data) == 0):
            data = {}
        if StringUtils.is_not_empty(data):
            data = json.loads(str(data))

        self.inputs = data
        if isinstance(data, dict):
            self.length = 1
            self.is_batch = False
        elif isinstance(data, list):
            self.length = len(data)
            self.is_batch = True
        else:
            message = 'invalid data format\nexpected input data formats are string, dict or a list'
            raise SparkError.sdk(message, data)


class _ExecuteMeta:
    __COMPILER_TYPES = ('neuron', 'type3', 'type2', 'type1', 'xconnector')

    def __init__(
        self,
        uri: UriParams,
        is_batch: bool,
        *,
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        compiler_type: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        # Available only in v3 (legacy)
        debug_solve: Optional[bool] = None,
        downloadable: Optional[bool] = False,
        echo_inputs: Optional[bool] = False,
        tables_as_array: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        outputs_filter: Optional[str] = None,
        # extra metadata if needed
        extras: Optional[Mapping[str, Any]] = None,
    ):
        self._uri = uri
        self._is_batch = is_batch
        self._active_since = active_since
        self._source_system = source_system or SPARK_SDK
        self._correlation_id = correlation_id

        self._call_purpose = (
            call_purpose
            if StringUtils.is_not_empty(call_purpose)
            else 'Sync Batch Execution'
            if is_batch
            else 'Single Execution'
        )
        self._compiler_type = (
            str(compiler_type).capitalize()
            if StringUtils.is_not_empty(compiler_type) and str(compiler_type).lower() in self.__COMPILER_TYPES
            else 'Neuron'
        )

        self._subservices = StringUtils.join(subservices)
        self._debug_solve = debug_solve
        self._downloadable = downloadable
        self._echo_inputs = echo_inputs
        self._tables_as_array = StringUtils.join(tables_as_array)
        self._selected_outputs = StringUtils.join(selected_outputs)
        self._outputs_filter = outputs_filter
        self._extras = extras or {}

    @property
    def values(self) -> Dict[str, Any]:
        if self._is_batch:
            service_uri = self._uri.pick('folder', 'service', 'version').encode(long=False)
            values = {
                'service': self._uri.service_id or service_uri or None,
                'version_id': self._uri.version_id,
                'version_by_timestamp': self._active_since,
                'subservice': self._subservices,
                'output': self._selected_outputs,
                'call_purpose': self._call_purpose,
                'source_system': self._source_system,
                'correlation_id': self._correlation_id,
                # extra metadata
                **self._extras,
            }
        else:
            values = {
                # URI locator via metadata (v3 also supports URI in url path)
                'service_id': self._uri.service_id,
                'version_id': self._uri.version_id,
                'version': self._uri.version,
                # v3 expects extra metadata
                'transaction_date': self._active_since,
                'call_purpose': self._call_purpose,
                'source_system': self._source_system,
                'correlation_id': self._correlation_id,
                'array_outputs': self._tables_as_array,
                'compiler_type': self._compiler_type,
                'debug_solve': self._debug_solve,
                'excel_file': self._downloadable,
                'requested_output': self._selected_outputs,
                'requested_output_regex': self._outputs_filter,
                'response_data_inputs': self._echo_inputs,
                'service_category': self._subservices,
                # extra metadata
                **self._extras,
            }

        return {k: v for k, v in values.items() if v is not None}

    @property
    def as_header(self) -> Dict[str, str]:
        # NOTE: this has to be a single line string: "'{\"call_purpose\":\"Single Execution\"}'"
        value = json.dumps(self.values, separators=(',', ':'))
        return {'x-meta' if self._is_batch else 'x-request-meta': "'{}'".format(value)}


class Compilation(ApiResource):
    def initiate(
        self,
        folder: str,
        service: str,
        file: BinaryIO,
        file_name: Optional[str] = None,
        versioning: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        end_date: Union[None, str, int, datetime] = None,
    ):
        startdate, enddate = DateUtils.parse(start_date, end_date)
        uri = Uri.validate(UriParams(folder, service))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='upload')

        metadata = {
            'request_data': {
                'effective_start_date': startdate.isoformat(),
                'effective_end_date': enddate.isoformat(),
                'version_difference': versioning or 'minor',
            }
        }
        form = {'engineUploadRequestEntity': json.dumps(metadata)}
        files = {'serviceFile': (file_name or f'{uri.service}.xlsx', file)}

        response = self.request(url, method='POST', form=form, files=files)
        if isinstance(response.data, dict) and response.data.get('response_data'):
            doc_id = response.data.get('response_data', {}).get('original_file_documentid')
            self.logger.info(f'service file uploaded <{doc_id}>')
        return response

    def get_status(
        self,
        folder: str,
        service: str,
        job_id: str,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        throwable: bool = True,
    ):
        """Polls the compilation job status until it's completed or timed out."""
        max_retries = max_retries or self.config.max_retries
        retry_interval = retry_interval or self.config.retry_interval

        uri = Uri.validate(UriParams(folder, service))
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=f'getcompilationprogess/{job_id}')

        retries = 0
        response = self.request(url)
        while True:
            response_data = isinstance(response.data, dict) and response.data.get('response_data', {}) or {}
            progress, status = response_data.get('progress', 0), response_data.get('status')

            if progress == 100 and status == 'Success':
                return response

            if progress < 100 and retries < max_retries:
                self.logger.info(f'waiting for compilation job to complete - {progress}%')

                retries += 1
                time.sleep(get_retry_timeout(retries, retry_interval))
                response = self.request(url)
            else:
                err_msg = f'compilation job status check timed out after {retries} attempts'
                if throwable:
                    self.logger.error(err_msg)
                    raise RetryTimeoutError(err_msg, retries=retries, interval=retry_interval)
                self.logger.warning(err_msg)
                return response
