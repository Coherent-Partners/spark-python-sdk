from __future__ import annotations

import gzip
import json
import zlib
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkError
from .._utils import DateUtils, is_str_not_empty, join_list_str
from ._base import ApiResource, HttpResponse, Uri, UriParams

__all__ = ['Services', 'ServiceExecuted']


class Services(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

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
        using: Optional[str] = None,
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
        )

        endpoint = f'transforms/{using or uri.service}/for/{uri.pick("folder", "service").encode()}'
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
    ):
        uri = Uri.validate(uri)
        validation_type = is_str_not_empty(validation_type) and str(validation_type).lower() or None

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
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = Uri.validate(UriParams(folder=folder, service=service) if uri is None else Uri.to_params(uri))
        endpoint = f'product/{uri.folder}/engines/get/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        return self.request(url)

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
        uri = (
            UriParams(folder, service, service_id, version_id=version_id, proxy=proxy, public=public)
            if uri is None
            else Uri.to_params(uri)
        )
        url = Uri.of(Uri.validate(uri), base_url=self.config.base_url.full, endpoint='metadata')

        response = self.request(url)
        return ServiceExecuted(response, False, 'original')

    def get_versions(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = Uri.validate(UriParams(folder, service) if uri is None else Uri.to_params(uri))
        endpoint = f'product/{uri.folder}/engines/getversions/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        response = self.request(url)
        return response.copy_with(data=response.data.get('data', []) if isinstance(response.data, dict) else [])

    def download(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        version: Optional[str] = None,
        file_name: Optional[str] = None,
        type: Optional[str] = None,  # 'original' or 'configured'
    ):
        uri = Uri.validate(UriParams(folder, service, version=version) if uri is None else Uri.to_params(uri))
        endpoint = f'product/{uri.folder}/engines/{uri.service}/download/{uri.version or ""}'
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
        uri = Uri.validate(UriParams(folder, service, version_id=version_id) if uri is None else Uri.to_params(uri))
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
            'tags': join_list_str(tags),
        }

        return self.request(url, method='POST', body={'request_data': data})

    def delete(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = Uri.validate(UriParams(folder, service) if uri is None else Uri.to_params(uri))
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
            raise SparkError.sdk('encoding is not supported', {'encoding': encoding})


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
        super().__init__(response.status, data, response.buffer, response.headers)


class _ExecuteInputs:
    def __init__(self, data: Union[None, str, Dict[str, Any], List[Any]] = None):
        if data is None or (isinstance(data, list) and len(data) == 0):
            data = {}
        if is_str_not_empty(data):
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
    ):
        self._uri = uri
        self._is_batch = is_batch
        self._active_since = active_since
        self._source_system = source_system or SPARK_SDK
        self._correlation_id = correlation_id

        self._call_purpose = (
            call_purpose
            if is_str_not_empty(call_purpose)
            else 'Sync Batch Execution'
            if is_batch
            else 'Single Execution'
        )
        self._compiler_type = (
            str(compiler_type).capitalize()
            if is_str_not_empty(compiler_type) and str(compiler_type).lower() in self.__COMPILER_TYPES
            else 'Neuron'
        )

        self._subservices = join_list_str(subservices)
        self._debug_solve = debug_solve
        self._downloadable = downloadable
        self._echo_inputs = echo_inputs
        self._tables_as_array = join_list_str(tables_as_array)
        self._selected_outputs = join_list_str(selected_outputs)
        self._outputs_filter = outputs_filter

    @property
    def values(self) -> Dict[str, Any]:
        if self._is_batch:
            service_uri = self._uri.pick('folder', 'service', 'version').encode(long=False)
            return {
                'service': self._uri.service_id or service_uri or None,
                'version_id': self._uri.version_id,
                'version_by_timestamp': self._active_since,
                'subservice': self._subservices,
                'output': self._selected_outputs,
                'call_purpose': self._call_purpose,
                'source_system': self._source_system,
                'correlation_id': self._correlation_id,
            }

        return {
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
        }

    @property
    def as_header(self) -> Dict[str, str]:
        # NOTE: this has to be a single line string: "'{\"call_purpose\":\"Single Execution\"}'"
        value = json.dumps({k: v for k, v in self.values.items() if v is not None}, separators=(',', ':'))
        return {'x-meta' if self._is_batch else 'x-request-meta': "'{}'".format(value)}
