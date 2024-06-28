import json
from typing import Any, Dict, List, Optional, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkError
from .._utils import is_str_not_empty, join_list_str
from ._base import ApiResource, HttpResponse, Uri, UriParams

__all__ = ['Services', 'ServiceExecuted']


class Services(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def execute(
        self,
        uri: Union[str, UriParams],
        *,
        response_format: str = 'alike',  # 'alike', 'typed', 'raw'
        # data for calculations
        inputs: Union[None, str, Dict[str, Any], List[Any]] = None,  # TODO: support `pandas.DataFrame`
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = SPARK_SDK,
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
            body = {'inputs': executable.inputs, **metadata.value}
        else:
            endpoint = '' if uri.version_id or uri.service_id else 'execute'
            url = Uri.of(uri, base_url=self.config.base_url.full, endpoint=endpoint)
            body = {'request_data': {'inputs': executable.inputs}, 'request_meta': metadata.value}

        response = self.request(url, method='POST', body=body)
        return ServiceExecuted(response, executable.is_batch, response_format)

    def get_schema(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = UriParams(folder=folder, service=service) if uri is None else Uri.to_params(uri)
        endpoint = f'product/{uri.folder}/engines/get/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        return self.request(url)

    def get_metadata(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        response_format: str = 'alike',  # 'alike', 'typed', 'raw'
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
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='metadata')

        response = self.request(url)
        return ServiceExecuted(response, False, response_format)

    def get_versions(
        self, uri: Union[None, str, UriParams] = None, *, folder: Optional[str] = None, service: Optional[str] = None
    ):
        uri = UriParams(folder, service) if uri is None else Uri.to_params(uri)
        endpoint = f'product/{uri.folder}/engines/getversions/{uri.service}'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)

        response = self.request(url)
        return response.copy_with(data=response.data.get('data', []) if isinstance(response.data, dict) else [])


class ServiceExecuted(HttpResponse):
    def __init__(self, response: HttpResponse, is_batch: bool, format: str = 'alike'):
        if format == 'raw':
            data = json.dumps(response.data)
        elif format == 'typed' or is_batch:
            data = response.data
        else:
            resp_data = response.data.get('response_data', {}) if isinstance(response.data, dict) else {}
            resp_meta = response.data.get('response_meta', {}) if isinstance(response.data, dict) else {}
            data = {
                'outputs': [resp_data.get('outputs')],
                'errors': [resp_data.get('errors')],
                'warnings': [resp_data.get('warnings')],
                **resp_meta,
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
            if is_str_not_empty(compiler_type)
            and str(compiler_type).lower() in ('neuron', 'type3', 'type2', 'type1', 'xconnector')
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
    def value(self) -> Dict[str, Any]:
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
