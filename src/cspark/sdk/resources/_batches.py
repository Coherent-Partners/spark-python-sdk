import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkError
from .._utils import is_str_empty, is_str_not_empty, join_list_str
from ._base import ApiResource, Uri, UriParams

__all__ = ['Batches']


class Batches(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def execute(
        self,
        uri: Union[str, UriParams],
        *,
        # kinds of input data
        inputs: Optional[List[Dict[str, Any]]] = None,
        raw: Optional[str] = None,
        # TODO: add support for `data: Optional[pandas.DataFrame] = None`.
        # supported metadata
        version_id: Optional[str] = None,
        active_since: Optional[str] = None,
        call_purpose: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        output: Optional[str] = None,
    ):
        uri = Uri.to_params(uri)
        service_uri = uri.service_id or uri.service_uri
        url = Uri.of(uri.pick('public'), base_url=self.config.base_url.full, version='api/v4', endpoint='execute')
        body = self.__build_exec_body(
            ExecuteParams(
                inputs=inputs or [],
                raw=raw,
                service_uri=service_uri,
                version_id=version_id,
                active_since=active_since,
                call_purpose=call_purpose,
                source_system=source_system,
                correlation_id=correlation_id,
                subservices=subservices,
                output=output,
            )
        )

        if len(body['inputs']) == 0:
            error = SparkError.sdk(message='no input data provided for service execution', cause=json.dumps(body))
            self.logger.error(error.message)
            raise error

        return self.request(url, method='POST', body=body)

    def __build_exec_body(self, params: 'ExecuteParams'):
        self.__validate_uri(params.service_uri, params.version_id)
        metadata = params.metadata()

        inputs = params.inputs if isinstance(params.inputs, list) else []
        if len(inputs) == 0 and is_str_not_empty(params.raw):
            try:
                json_data = json.loads(str(params.raw))
                inputs = json_data.pop('inputs', [])
                metadata.update(json_data)
            except Exception:
                self.logger.warn('failed to parse the raw input as JSON')
        return {'inputs': inputs, **metadata}

    def __validate_uri(self, service_uri: Optional[str], version_id: Optional[str]):
        if is_str_empty(service_uri) and is_str_empty(version_id):
            error = SparkError.sdk(
                message='service uri locator is required',
                cause=json.dumps({'service_uri': service_uri, 'version_id': version_id}),
            )
            self.logger.error(error.message)
            raise error


@dataclass(frozen=True)
class ExecuteParams:
    # Input definitions for calculations
    inputs: Optional[List[Dict[str, Any]]] = None
    raw: Optional[str] = None

    # Parameters to identify the correct service and version to use
    service_uri: Optional[str] = None
    service_id: Optional[str] = None
    version_id: Optional[str] = None
    active_since: Optional[str] = None

    # These fields, if provided as part of the API request, are visible in the API Call History.
    call_purpose: Optional[str] = 'Sync Batch Execution'
    source_system: Optional[str] = SPARK_SDK
    correlation_id: Optional[str] = None

    # Parameters to control the response outputs
    subservices: Union[None, str, List[str]] = None
    output: Union[None, str, List[str]] = None

    def metadata(self):
        data = self.__dict__.copy()

        # cleanse unneeded fields
        data.pop('inputs', None)
        data.pop('raw', None)
        data.pop('service_id', None)

        # rename fields to match the API request
        data['service'] = data.pop('service_uri', None)
        data['version_by_timestamp'] = data.pop('active_since', None)
        data['subservice'] = join_list_str(data.pop('subservices', None))
        data['output'] = join_list_str(data.pop('output', None))

        return data
