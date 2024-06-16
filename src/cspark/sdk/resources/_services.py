import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._utils import is_str_not_empty, read
from ._base import ApiResource, Uri, UriParams

__all__ = ['Services', 'ExecuteData']


class Services(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def close(self):
        super().close()

    def execute(
        self,
        uri: Union[str, UriParams],
        *,
        data: Optional['ExecuteData'] = None,
        inputs: Optional[Dict[str, Any]] = None,
        raw: Optional[str] = None,
    ):
        uri = Uri.to_params(uri)
        url = Uri.of(uri, base_url=self.config.base_url.full, endpoint='execute')
        body = self.__build_exec_body(uri, ExecuteParams(data, inputs, raw))

        return self.request(url, method='POST', body=body)

    def __build_exec_body(self, uri: UriParams, params: 'ExecuteParams') -> Any:
        data = params.data or ExecuteData(service_id=uri.service_id, version_id=uri.version_id)
        inputs = data.inputs or params.inputs
        metadata = data.metadata()

        if inputs is None and is_str_not_empty(params.raw):
            try:
                json_data = json.loads(str(params.raw))

                request_meta = json_data.get('request_meta', {})
                metadata = {**metadata, **request_meta}
                inputs = read('request_data.inputs', json_data, {})
            except Exception:
                self.logger.warn('failed to parse the raw input as JSON')
            return {'request_data': {'inputs': inputs or {}}, 'request_meta': metadata}
        else:
            return {'request_data': {'inputs': inputs or {}}, 'request_meta': metadata}


@dataclass(frozen=True)
class ExecuteParams:
    data: Optional['ExecuteData'] = None
    inputs: Optional[Dict[str, Any]] = None
    raw: Optional[str] = None


@dataclass(frozen=True)
class ExecuteData:
    # Input definitions for calculations
    inputs: Optional[Dict[str, Any]] = None

    # Parameters to identify the correct service and version to use
    service_uri: Optional[str] = None
    service_id: Optional[str] = None
    version: Optional[str] = None
    version_id: Optional[str] = None
    active_since: Optional[str] = None

    # These fields, if provided as part of the API request, are visible in the API Call History.
    call_purpose: Optional[str] = 'Single Execution'
    source_system: Optional[str] = SPARK_SDK
    correlation_id: Optional[str] = None

    # Parameters to control the response outputs
    outputs: Union[None, str, List[str]] = None
    compiler_type: Optional[str] = 'Neuron'
    debug_solve: Optional[bool] = None
    downloadable: Optional[bool] = False
    output: Union[None, str, List[str]] = None
    output_regex: Optional[str] = None
    with_inputs: Optional[bool] = False
    subservices: Union[None, str, List[str]] = None
    validation_type: Optional[str] = None

    def metadata(self):
        data = self.__dict__.copy()
        # inputs are not part of the metadata
        data.pop('inputs', None)

        # rename fields to match the API request
        data['transaction_date'] = data.pop('active_since', None)
        data['array_outputs'] = data.pop('outputs', None)
        data['excel_file'] = data.pop('downloadable', None)
        data['requested_output'] = data.pop('output', None)
        data['requested_output_regex'] = data.pop('output_regex', None)
        data['response_data_inputs'] = data.pop('with_inputs', None)
        data['service_category'] = data.pop('subservices', None)

        # validation_type is only for the Validation API.
        validation = data.pop('validation_type', None)
        if validation is not None:
            data['validation_type'] = 'dynamic' if validation == 'dynamic' else 'default_values'
        return data
